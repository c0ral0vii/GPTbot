import os

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from src.api.v1 import routes, auth


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

app.include_router(routes.router, prefix="/api/v1", tags=["Analytic API"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth API"])


@app.get(
    "/admin",
    response_class=FileResponse,
    dependencies=[Depends(auth.security.access_token_required)],
)
async def root():
    index_html = static_dir + "/index.html"
    return FileResponse(index_html)


@app.get("/", response_class=FileResponse)
async def auth_page():
    auth_html = static_dir + "/auth.html"
    return FileResponse(auth_html)
