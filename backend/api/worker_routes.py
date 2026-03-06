from fastapi import APIRouter
from pydantic import BaseModel
from worker_engine.worker_parser import parse_worker_profile
from worker_engine.risk_score import compute_worker_risk
from worker_engine.reskilling_engine import generate_reskilling_path

router = APIRouter(prefix="/worker", tags=["Worker"])


class WorkerProfile(BaseModel):
    job_title: str
    city: str
    experience_years: float
    writeup: str


@router.post("/analyze")
def analyze_worker(profile: WorkerProfile):
    parsed = parse_worker_profile(profile.model_dump())

    risk = compute_worker_risk(parsed)

    path = generate_reskilling_path(parsed)

    return {
        "parsed_profile": parsed,
        "risk_score": risk,
        "reskilling_path": path,
    }
