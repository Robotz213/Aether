"""ProcessPool WSGI Server com graceful shutdown."""

from __future__ import annotations

import signal
import sys
import traceback
from concurrent.futures import ProcessPoolExecutor
from contextlib import suppress
from multiprocessing import Event, Lock
from typing import TYPE_CHECKING, ClassVar, Self
from wsgiref.simple_server import WSGIServer
from wsgiref.types import WSGIApplication

from clear import clear
from rich.console import Console
from rich.panel import Panel

from aether._requesthandlerwsgi import WSGIRequestHandler

if TYPE_CHECKING:
    from multiprocessing.synchronize import Event as SyncEvent

    from aether._types import Host, Port

sigint_count = 0
console = Console()

with_gil = sys._is_gil_enabled() if hasattr(sys, "_is_gil_enabled") else True


class ProcessPoolWSGIServer(WSGIServer):
    """Servidor WSGI ProcessBased com ProcessPoolExecutor."""

    _shutdown_event: ClassVar[SyncEvent] = Event()

    @property
    def shutdown_event(self) -> SyncEvent:
        return self._shutdown_event

    @shutdown_event.setter
    def shutdown_event(self, event: SyncEvent) -> None:
        self._shutdown_event = event

    def __init__(
        self,
        host: Host,
        port: Port,
        app: WSGIApplication | None = None,
        poll_interval: float = 0.5,
        max_workers: int = 10,
    ) -> None:
        """Servidor WSGI com ProcessPoolExecutor."""
        self.host = host
        self.port = port
        self.poll_interval = poll_interval
        self.executor = ProcessPoolExecutor(max_workers=max_workers)

        super().__init__((host, port), WSGIRequestHandler)
        self.app = app
        self.set_app(app)

    def process_request(self, request: object, client_address: object) -> None:
        # Rejeita novas conexões durante shutdown
        if not with_gil:
            with Lock():
                if self.shutdown_event.is_set():
                    request.close()
                    return

                self.executor.submit(
                    self.__handle_request,
                    request,
                    client_address,
                )

        else:
            if self.shutdown_event.is_set():
                request.close()
                return

            self.executor.submit(
                self.__handle_request,
                request,
                client_address,
            )

    def __handle_request(
        self,
        request: object,
        client_address: object,
    ) -> None:
        try:
            self.finish_request(request, client_address)
            self.shutdown_request(request)
        except Exception as e:
            exc = "\n".join(traceback.format_exception(e))
            console.log(f"[red]{exc}[/red]")
            self.handle_error(request, client_address)
            self.shutdown_request(request)

    def server_close(self) -> None:
        super().server_close()
        self.executor.shutdown(wait=True)

    def run(self) -> None:
        clear()
        panel = Panel.fit(
            title="[bold cyan]Processed WSGI Server",
            renderable=f"[cyan]Servidor rodando em [bold white]http://{self.host}:{self.port}[/bold white]",
            subtitle="[bold green]Pressione Ctrl+C para iniciar o graceful shutdown[/bold green]",
            border_style="bright_blue",
            width=300,
        )
        console.log(panel)

        with suppress(KeyboardInterrupt):
            while not self.shutdown_event.is_set():
                self.serve_forever()

    def __enter__(self) -> Self:
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
    ) -> Self:
        """Create a new WSGI server listening on `host` and `port` for `app`.

        Returns:
            server: WSGI Server.

        """
        server = cls(host=host, port=port)
        signal.signal(signal.SIGINT, server._handle_sigint)

        server.set_app(app)
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


make_server = ProcessPoolWSGIServer._make_server
