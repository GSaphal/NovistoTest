from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.agent import answer_question
from app.identity import AuthError, get_users_by_token, resolve_token

app = FastAPI(title="Internal Knowledge Assistant")


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    citations: list[dict] = []


def _extract_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split(maxsplit=1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Expected 'Authorization: Bearer <token>'")
    return parts[1]


@app.post("/ask", response_model=AskResponse)
async def ask(body: AskRequest, authorization: str | None = Header(default=None)) -> AskResponse:
    token = _extract_token(authorization)
    try:
        resolve_token(token, get_users_by_token())
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    result = await answer_question(token=token, question=body.question)
    return AskResponse(answer=result["answer"], citations=result.get("citations", []))


app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")