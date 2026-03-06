from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import dashboard_routes, worker_routes, chatbot_routes

app = FastAPI(title="Skills Mirage API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_routes.router)
app.include_router(worker_routes.router)
app.include_router(chatbot_routes.router)


@app.get("/")
def root():
    return {"message": "Skills Mirage Backend Running"}
