from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from chatbot.query_router import handle_query
from utils.jwt_handler import get_current_user
from db.mongo import users_collection

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


class ChatbotQuery(BaseModel):
    worker_profile: dict = {}
    question: str


@router.post("/query")
def chatbot(query: ChatbotQuery, current_user: Optional[dict] = Depends(get_current_user)):
    """
    Handle chatbot queries with intent-based routing.
    Passes the authenticated user's full MongoDB document so the query router
    can access worker analysis and reskilling data for personalised answers.
    """
    try:
        # Fetch the freshest user data from MongoDB (current_user from JWT
        # may be stale if analysis was generated in a different tab)
        user_data = {}
        if current_user and current_user.get("email"):
            fresh = users_collection.find_one({"email": current_user["email"]})
            if fresh:
                fresh.pop("_id", None)
                user_data = fresh

        response = handle_query(query.model_dump(), user_data=user_data)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Chatbot failed: {exc}") from exc

    return {"response": response}
