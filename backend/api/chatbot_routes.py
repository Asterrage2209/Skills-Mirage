from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from chatbot.query_router import handle_query

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


class ChatbotQuery(BaseModel):
    worker_profile: dict
    question: str


@router.post("/query")
def chatbot(query: ChatbotQuery):
    try:
        response = handle_query(query.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Chatbot failed: {exc}") from exc

    return {"response": response}
