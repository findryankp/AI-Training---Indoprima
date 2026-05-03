from celery.result import AsyncResult
from tasks.celery_app import celery_app
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import tasks.celery_tasks as celeryTask
import os
import uuid

app = FastAPI(title="CrewAI Celery API")

# Folder to save uploaded files
FILE_FOLDER = "output"
os.makedirs(FILE_FOLDER, exist_ok=True)

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

@app.post("/rag")
async def rag(file: UploadFile = File(...)):
    # Validasi tipe file
    if file.content_type != "text/plain":
        raise HTTPException(status_code=400, detail="File must be a .txt file")

    # Simpan file ke lokasi temporary
    file_extension = os.path.splitext(file.filename)[1] or ".txt"
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(FILE_FOLDER, unique_filename)

    # Simpan konten file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Kirim ke Celery task secara background
    task = celeryTask.doc_analyzer.delay(file_path)
    
    return {
        "task_id": task.id, 
        "file_path": file_path
    }
