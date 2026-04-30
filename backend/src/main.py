from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database import init_db
from src.routers import (
    auth, competency, matrix, questionnaire, handbook, report, file, user_settings, practice, roleplay, vision_practice, behavior_evaluation, knowledge_base, judge_team, evaluation_criteria
)

app = FastAPI(title="AC测评工具API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176", "http://localhost:5177"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(competency.router)
app.include_router(matrix.router)
app.include_router(questionnaire.router)
app.include_router(handbook.router)
app.include_router(report.router)
app.include_router(file.router)
app.include_router(user_settings.router)
app.include_router(practice.router)
app.include_router(roleplay.router)
app.include_router(vision_practice.router)
app.include_router(behavior_evaluation.router)
app.include_router(knowledge_base.router)
app.include_router(judge_team.router)
app.include_router(evaluation_criteria.router)

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/")
async def root():
    return {"message": "AC测评工具API"}
