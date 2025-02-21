import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from v1.routes import router

app = FastAPI(title="Admin Woome AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(router, prefix="/api/v1")


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <script>
        window.location.href = '/static/index.html';
    </script>
    """


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
