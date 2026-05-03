from celery.result import AsyncResult
from tasks.celery_app import celery_app
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import tasks.celery_tasks as celeryTask

app = FastAPI(title="CrewAI Celery API")

class ResearchInput(BaseModel):
    topic: str

@app.post("/research")
async def start_research(input_data: ResearchInput):
    # Mengirim tugas ke Celery
    task = celeryTask.research.delay(input_data.topic)
    return {"task_id": task.id}

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": task_result.state,
        "result": None,
        "error": None
    }
    
    if task_result.state == 'SUCCESS':
        response["result"] = task_result.result
    elif task_result.state == 'FAILURE':
        response["error"] = str(task_result.info)
        
    return response
