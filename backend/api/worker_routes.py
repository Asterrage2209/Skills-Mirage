from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from db.mongo import users_collection
from utils.jwt_handler import get_current_user
from worker_engine.worker_parser import parse_worker_profile
from worker_engine.risk_score import compute_worker_risk
from worker_engine.reskilling_engine import generate_reskilling_path

router = APIRouter(prefix="/worker", tags=["Worker"])

class WorkerProfile(BaseModel):
    job_role: str
    city: str
    years_of_experience: float
    role_description: str
    skills: List[str]


@router.get("/profile")
def get_worker_profile(current_user: dict = Depends(get_current_user)):
    return {
        "job_role": current_user.get("job_role"),
        "city": current_user.get("city"),
        "years_of_experience": current_user.get("years_of_experience"),
        "role_description": current_user.get("role_description"),
        "skills": current_user.get("skills", []),
        "risk_score": current_user.get("risk_score")
    }

@router.post("/profile")
def update_worker_profile(profile: WorkerProfile, current_user: dict = Depends(get_current_user)):
    
    # Map the new schema back to legacy worker intelligence parser
    legacy_profile = {
        "job_title": profile.job_role,
        "city": profile.city,
        "experience_years": profile.years_of_experience,
        "writeup": profile.role_description,
        "skills": profile.skills # Ensure arrays traverse safely if possible.
    }
    
    parsed = parse_worker_profile(legacy_profile)

    # Allow frontend skills override explicitly avoiding purely AI extracted parsing limitations
    if profile.skills:
        parsed["skills"] = list(set(parsed.get("skills", []) + profile.skills))

    # Calculate actual risk from worker engine
    risk = compute_worker_risk(parsed)
    path = generate_reskilling_path(parsed)

    # Save to MongoDB Native Document securely overriding previous iterations synchronously.
    users_collection.update_one(
        {"_id": current_user["_id"]},
        {"$set": {
            "job_role": profile.job_role,
            "city": profile.city,
            "years_of_experience": profile.years_of_experience,
            "role_description": profile.role_description,
            "skills": parsed.get("skills", []),
            "risk_score": risk
        }}
    )

    return {
        "parsed_profile": parsed,
        "risk_score": risk,
        "reskilling_path": path,
    }
