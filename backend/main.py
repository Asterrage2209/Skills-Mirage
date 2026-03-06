import logging
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api import dashboard_routes, worker_routes, chatbot_routes
from api.courses_routes import router as courses_router
from data.courses_dataset import is_empty as courses_dataset_is_empty, get_course_count
from scrapers.courses.courses_scraper import (
    run_courses_scraper,
    run_courses_scraper_background,
)

logger = logging.getLogger(__name__)

MIN_COURSES = 200  # Keep scraping until we have at least this many

# ── Scheduler (module-level so lifespan can shut it down cleanly) ─────────────
scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── On startup: scrape courses if below minimum threshold ─────────────────
    course_count = get_course_count()
    if course_count < MIN_COURSES:
        logger.info(
            "Courses dataset has %s courses (need %s) — starting scrape in background.",
            course_count, MIN_COURSES,
        )
        run_courses_scraper_background()

    # ── Weekly refresh every 7 days ───────────────────────────────────────────
    scheduler.add_job(
        run_courses_scraper,
        trigger="interval",
        days=7,
        kwargs={"max_per_source": 50},  # 50 NPTEL + 50 SWAYAM = 100 new courses/week
        id="weekly_courses_scrape",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("APScheduler started — weekly courses scrape scheduled.")

    yield  # app runs here

    # ── On shutdown ───────────────────────────────────────────────────────────
    scheduler.shutdown(wait=False)
    logger.info("APScheduler shut down.")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Skills Mirage API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logging.info(f"API Request: {request.method} {request.url}")
    response = await call_next(request)
    return response

# ── Routers ───────────────────────────────────────────────────────────────────
from api import auth_routes                                                # ← new

app.include_router(dashboard_routes.router)
app.include_router(worker_routes.router)
app.include_router(chatbot_routes.router)
app.include_router(courses_router)          # ← new
app.include_router(auth_routes.router)      # ← new


@app.get("/")
def root():
    return {"message": "Skills Mirage Backend Running"}

