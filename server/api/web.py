"""The built web app, served from the same origin as the API (011)."""

from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from store.paths import ROOT

BUILD = ROOT / "web" / "build"
ENTRY = "index.html"
API = "api"


def routes(build: Path) -> APIRouter:
    router = APIRouter()
    root = build.resolve()

    @router.get("/{path:path}", include_in_schema=False)
    def file(path: str) -> FileResponse:
        if path.split("/", 1)[0] == API:
            raise HTTPException(status.HTTP_404_NOT_FOUND)

        # The app finds its own screens: any path that is not one of its files is the app.
        asked = (root / path).resolve()
        if asked.is_file() and asked.is_relative_to(root):
            return FileResponse(asked)
        return FileResponse(root / ENTRY)

    return router
