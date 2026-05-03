from tasks.celery_app import celery_app
from src.crews.content_crew.content_crew import ContentCrew
from src.crews.crew_rag.crew_rag import CrewRag
import logging
import traceback

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="doc_analyzer")
def doc_analyzer(self, file: str):
    self.update_state(state='RUNNING', meta={'current': f'start job for {file}'})
    try:
        # Menjalankan crew dengan input variable 'file'
        result = CrewRag().crew().kickoff(inputs={"file": file})
        return str(result)
    except Exception as e:
        logger.error(f"Task failed with error: {e}\n{traceback.format_exc()}")
        raise

@celery_app.task(bind=True, name="research")
def research(self, topic: str):
    # Update status ke RUNNING
    self.update_state(state='RUNNING', meta={'current': f'Memulai riset tentang {topic}'})
    try:
        # Menjalankan CrewAI secara sinkron di dalam worker
        result = ContentCrew().crew().kickoff(inputs={"topic": topic})
        return str(result)
    except Exception as e:
        logger.error(f"Task gagal: {e}\n{traceback.format_exc()}")
        raise
