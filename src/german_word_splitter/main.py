"""FastAPI application."""

from fastapi import FastAPI

from .api.routes import router
from .config import get_port, get_port_file, get_socket, get_socket_mode


def create_app() -> FastAPI:
    app = FastAPI(title="German Compound Splitter Service")
    app.include_router(router)
    return app


app = create_app()

def run() -> None:
    import os
    import socket

    import uvicorn

    socket_path = get_socket()
    if socket_path:
        # The socket is created with the umask applied, so derive it from the mode.
        os.umask(0o777 & ~get_socket_mode())
        uvicorn.run(app, uds=socket_path)
        return

    # Port 0 lets the kernel pick a free port; it is reported in the log and port file.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", get_port()))
    port = sock.getsockname()[1]
    port_file = get_port_file()
    if port_file:
        with open(port_file, "w") as fh:
            fh.write(f"{port}\n")
    uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port)).run(sockets=[sock])


if __name__ == "__main__":  # pragma: no cover
    run()
