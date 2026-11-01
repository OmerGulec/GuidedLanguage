"""Signing in and out (011): an httpOnly session cookie."""

from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Cookie, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict

from api.server import Server
from store.accounts import SESSION_LENGTH, account_of, sign_in, sign_out

COOKIE = "session"


class SignIn(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)
    email: str
    password: str


def signed_in(server: Server) -> Callable[..., int]:
    """A dependency giving the signed-in account; anyone else gets 401."""

    def account(session: Annotated[str | None, Cookie()] = None) -> int:
        found = None if session is None else account_of(server.db, session, server.clock())
        if found is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED)
        return found

    return account


def routes(server: Server) -> APIRouter:
    router = APIRouter(prefix="/api/session")

    @router.post("", status_code=status.HTTP_204_NO_CONTENT)
    def open_session(body: SignIn, response: Response) -> None:
        token = sign_in(server.db, body.email, body.password, server.clock())
        if token is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED)
        response.set_cookie(
            COOKIE,
            token,
            max_age=int(SESSION_LENGTH.total_seconds()),
            httponly=True,
            samesite="lax",
            secure=server.secure_cookies,
        )

    @router.delete("", status_code=status.HTTP_204_NO_CONTENT)
    def close_session(response: Response, session: Annotated[str | None, Cookie()] = None) -> None:
        if session is not None:
            sign_out(server.db, session)
        response.delete_cookie(COOKIE)

    return router
