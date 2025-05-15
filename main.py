from fastapi import FastAPI
from routes.CVJobAIAnalyzer import router as cv_job_ai_analyzer_router

app = FastAPI()

app.include_router(cv_job_ai_analyzer_router)


@app.get("/")
def read_root():
    return {"message": "Hello World"}
