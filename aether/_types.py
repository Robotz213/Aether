from typing import Literal

type Host = Literal["localhost", "127.0.0.1", "192.168.0.1", "example.com"]
type Port = Literal[5000, 8000, 4000]
type TupleServerAddress = tuple[Host, Port]
