import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class SimpleStateManager:
    
    def update_progress(self, job_id: str, progress: int, message: str = ""):
        logger.info(f"Job {job_id}: {progress}% - {message}")
    
    def get_progress(self, job_id: str) -> Optional[dict]:
        return {"progress": 0, "message": "In Process..."}

state_manager = SimpleStateManager()