from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database import init_db
from src.routers import auth, competency, matrix, questionnaire, handbook

app = FastAPI(title="AC测评工具API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(competency.router)
app.include_router(matrix.router)
app.include_router(questionnaire.router)
app.include_router(handbook.router)

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/")
async def root():
    return {"message": "AC测评工具API"}
