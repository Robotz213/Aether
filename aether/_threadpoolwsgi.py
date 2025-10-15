"""Threaded WSGI Server com graceful shutdown."""

import signal
import sys
import traceback
from collections import UserList
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import suppress
from threading import Event
from typing import ClassVar, Self
from wsgiref.types import WSGIApplication

import rich
from clear import clear
from rich.console import Console
from rich.panel import Panel
from werkzeug.serving import ThreadedWSGIServer

from aether._requesthandlerwsgi import WSGIRequestHandler
from aether._types import Host, Port

sigint_count = 0
console = Console()

with_gil = sys._is_gil_enabled() if hasattr(sys, "_is_gil_enabled") else True


class _Futures(UserList[Future]):
    """Joinable list of all non-daemon threads."""

    def append(self, thread: Future) -> None:
        self.reap()
        super().append(thread)

    def pop_all(self) -> Self:
        self[:], futures = [], self[:]
        return futures

    def join(self) -> None:
        for future in self.pop_all():
            future.result()

    def reap(self) -> None:
        self[:] = (future for future in self if future.running())


class ThreadPoolWSGIServer(ThreadedWSGIServer):
    """Servidor WSGI ThreadBased com ThreadPoolExecutor."""

    _shutdown_event: ClassVar[Event] = Event()

    _futures = _Futures()

    @property
    def shutdown_event(self) -> Event:
        return self._shutdown_event

    @shutdown_event.setter
    def shutdown_event(self, event: Event) -> None:
        self._shutdown_event = event  # pyright: ignore[reportAttributeAccessIssue]

    def __init__(
        self,
        host: Host,
        port: Port,
        app: WSGIApplication | None = None,
        poll_interval: float = 0.5,
        max_workers: int = 10,
    ) -> None:
        """Servidor WSGI com ThreadPoolExecutor."""
        self.host = host
        self.port = port
        self.poll_interval = poll_interval
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        super().__init__(host, port, app, WSGIRequestHandler)  # pyright: ignore[reportArgumentType]

    def process_request(self, request: object, client_address: object) -> None:
        # Rejeita novas conexões durante shutdown

        if self.shutdown_event.is_set():
            request.close()  # pyright: ignore[reportAttributeAccessIssue]
            return

        self._futures.append(
            self.executor.submit(
                self.__handle_request,
                request,
                client_address,
            ),
        )

    def __handle_request(
        self,
        request: object,
        client_address: object,
    ) -> None:
        try:
            self.finish_request(request, client_address)  # pyright: ignore[reportArgumentType]
            self.shutdown_request(request)  # pyright: ignore[reportArgumentType]
        except Exception as e:
            exc = "\n".join(traceback.format_exception(e))
            console.log(f"[red]{exc}[/red]")
            self.handle_error(request, client_address)  # pyright: ignore[reportArgumentType]
            self.shutdown_request(request)  # pyright: ignore[reportArgumentType]

    def server_close(self) -> None:
        super().server_close()
        self.executor.shutdown(wait=True)

    def run(self) -> None:
        clear()
        panel = Panel.fit(
            title="[bold cyan]Threaded WSGI Server",
            renderable=f"[cyan]Servidor rodando em [bold white]http://{self.host}:{self.port}[/bold white]",
            border_style="bright_blue",
        )

        rich.print(panel)
        rich.print(
            "[bold green]Pressione Ctrl+C para iniciar o graceful shutdown[/bold green]",
        )

        with suppress(KeyboardInterrupt):
            while not self.shutdown_event.is_set():
                self.serve_forever()

    def __enter__(self) -> Self:  # pyright: ignore[reportReturnType]
        with suppress(Exception):
            return self

    def __exit__(self, *args: object, **kwargs: object) -> None:
        with suppress(Exception):
            return super().server_close()

    @classmethod
    def _make_server(
        cls,
        host: Host,
        port: Port,
        app: WSGIApplication,
        pool_interval: float = 0.5,
        max_workers: int = 10,
    ) -> Self:
        """Create a new WSGI server listening on `host` and `port` for `app`.

        Returns:
            server: WSGI Server.

        """
        server = cls(
            host=host,
            port=port,
            app=app,
            poll_interval=pool_interval,
            max_workers=max_workers,
        )
        signal.signal(signal.SIGINT, server._handle_sigint)

        return server

    def _handle_sigint(self, signum: int, frame: object) -> None:
        global sigint_count
        sigint_count += 1

        if sigint_count == 1:
            msg = "\n[INFO] Ctrl+C detectado (SIGINT 1x): iniciando graceful shutdown. Pressione Ctrl+C novamente para forçar cold shutdown."
            console.log(msg)
            self.shutdown_event.set()  # Sinaliza para o servidor parar de aceitar novas conexões
        elif sigint_count == 2:
            msg = "\n[WARN] Ctrl+C pressionado novamente (SIGINT 2x): cold shutdown! Encerrando imediatamente."
            console.log(msg)
            sys.exit(1)


make_server = ThreadPoolWSGIServer._make_server
