import time


def add_timing_middleware(app):
    @app.middleware("http")
    async def add_process_time_header(request, call_next):
        start_time = time.perf_counter()

        response = await call_next(request)

        process_time = time.perf_counter() - start_time

        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Process-Time-ms"] = str(round(process_time * 1000, 2))

        return response