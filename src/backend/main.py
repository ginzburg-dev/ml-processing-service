import uvicorn


def run_app() -> None:
    uvicorn.run(
        "backend.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="debug",
    )
