from fastapi import APIRouter
from app.models.schemas import AskRequest, AskResponse
from app.services.ai_service import ask_ops_ai

router = APIRouter(tags=["ops"])


@router.post("/ops/ask", response_model=AskResponse)
def ask_ops(payload: AskRequest):
    answer = ask_ops_ai(payload.question)
    return AskResponse(answer=answer)
