from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from db.mongo import users_collection
from utils.jwt_handler import get_current_user
from worker_engine.worker_parser import parse_worker_profile
from worker_engine.risk_score import compute_worker_risk
from worker_engine.reskilling_engine import generate_reskilling_path
from worker_engine.worker_gemini import analyze_worker as gemini_analyze_worker
from intelligence.vulnerability_index import compute_vulnerability_index
import logging
from datetime import datetime

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
        "gemini_risk_score": current_user.get("gemini_risk_score"),
        "reasoning": current_user.get("reasoning"),
        "reskilling_path": current_user.get("reskilling_path"),
        "gemini_analysis": current_user.get("gemini_analysis"),
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
    vulnerability_data = compute_vulnerability_index()
    ai_vulnerability = vulnerability_data["role_risks"].get(parsed.get("role", "").lower(), 50)
    risk = compute_worker_risk(parsed)
    path = generate_reskilling_path(parsed)

    # Call Gemini for AI-powered worker analysis
    gemini_analysis = gemini_analyze_worker(
        job_title=profile.job_role,
        city=profile.city,
        experience=profile.years_of_experience,
        skills=profile.skills if profile.skills else parsed.get("skills", []),
    )

    logging.info("Worker profile update called")
    logging.info(f"user_id: {current_user['_id']}")
    logging.info(f"job_role: {profile.job_role}")
    logging.info(f"gemini_risk_score: {gemini_analysis.get('risk_score')}")

    # Save to MongoDB
    users_collection.update_one(
        {"email": current_user["email"]},
        {"$set": {
            "name": current_user.get("name"),
            "email": current_user["email"],
            "job_role": profile.job_role,
            "city": profile.city,
            "years_experience": profile.years_of_experience,
            "role_description": profile.role_description,
            "skills": profile.skills if profile.skills else parsed.get("skills", []),
            "gemini_risk_score": gemini_analysis.get("risk_score") if gemini_analysis else None,
            "reasoning": gemini_analysis.get("explanation") if gemini_analysis else None,
            "updated_at": datetime.utcnow()
        }},
        upsert=True
    )
    logging.info("Mongo profile update successful")

    return {
        "parsed_profile": parsed,
        "gemini_analysis": gemini_analysis,
    }
