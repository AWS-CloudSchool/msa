from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from database.models.database_models import UserAnalysisJob, UserReport, UserAudioFile
from database.core.database import get_db

class DatabaseService:
    def create_analysis_job(self, db: Session, user_id: str, job_type: str, input_data: dict) -> UserAnalysisJob:
   
        job = UserAnalysisJob(
            user_id=user_id,
            job_type=job_type,
            input_data=input_data,
            status="processing"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job
    
    def update_job_status(self, db: Session, job_id: str, status: str, result_s3_key: str = None):

        job = db.query(UserAnalysisJob).filter(UserAnalysisJob.id == job_id).first()
        if job:
            job.status = status
            if result_s3_key:
                job.result_s3_key = result_s3_key
            if status == "completed":
                job.completed_at = datetime.utcnow()
            db.commit()
    
    def get_user_jobs(self, db: Session, user_id: str, limit: int = 50) -> List[UserAnalysisJob]:

        return db.query(UserAnalysisJob).filter(
            UserAnalysisJob.user_id == user_id
        ).order_by(UserAnalysisJob.created_at.desc()).limit(limit).all()
    
    def get_job_by_id(self, db: Session, job_id: str, user_id: str) -> Optional[UserAnalysisJob]:

        return db.query(UserAnalysisJob).filter(
            UserAnalysisJob.id == job_id,
            UserAnalysisJob.user_id == user_id
        ).first()
    

        report = UserReport(
            job_id=job_id,
            user_id=user_id,
            title=title,
            s3_key=s3_key,
            file_type=file_type
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report
    
    def create_user_audio(self, db: Session, job_id: str, user_id: str, s3_key: str, duration: int) -> UserAudioFile:
    
        audio = UserAudioFile(
            job_id=job_id,
            user_id=user_id,
            s3_key=s3_key,
            duration=duration
        )
        db.add(audio)
        db.commit()
        db.refresh(audio)
        return audio
    
    def get_user_reports(self, db: Session, user_id: str, limit: int = 50) -> List[UserReport]:
   
        return db.query(UserReport).filter(
            UserReport.user_id == user_id
        ).order_by(UserReport.created_at.desc()).limit(limit).all()
    
    def get_user_audio_files(self, db: Session, user_id: str, limit: int = 50) -> List[UserAudioFile]:
        return db.query(UserAudioFile).filter(
            UserAudioFile.user_id == user_id
        ).order_by(UserAudioFile.created_at.desc()).limit(limit).all()
    
    def delete_job(self, db: Session, job_id: str, user_id: str) -> bool:
        job = db.query(UserAnalysisJob).filter(
            UserAnalysisJob.id == job_id,
            UserAnalysisJob.user_id == user_id
        ).first()
        
        if job:
            db.query(UserReport).filter(UserReport.job_id == job_id).delete()
            db.query(UserAudioFile).filter(UserAudioFile.job_id == job_id).delete()
            db.delete(job)
            db.commit()
            return True
        return False

database_service = DatabaseService()

async def get_user_jobs(username: str):
    db = next(get_db())
    try:
        jobs = database_service.get_user_jobs(db, username)
        return [{
            "id": job.id,
            "status": job.status,
            "job_type": job.job_type,
            "input_data": job.input_data,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        } for job in jobs]
    finally:
        db.close()

async def get_job_progress(job_id: str):
    return {
        "progress": 50,
        "message": "In Process...",
        "status": "processing"
    }