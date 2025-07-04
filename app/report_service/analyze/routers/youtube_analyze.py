# app/analyze/routers/youtube_analyze.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any

from analyze.core.auth import get_current_user
from database.core.database import get_db
from analyze.services.youtube_analyze_service import youtube_reporter_service
from database.services.database_service import database_service
from analyze.models.youtube_analyze import YouTubeReporterRequest, YouTubeReporterResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["YouTube Reporter"])


async def run_youtube_analysis(job_id: str, user_id: str, youtube_url: str, db: Session):
    try:
        await youtube_reporter_service.process_youtube_analysis(
            job_id=job_id,
            user_id=user_id,
            youtube_url=youtube_url,
            db=db
        )
    except Exception as e:
        logger.error(f"Background YouTube analysis failed: {job_id} - {str(e)}")


@router.post("/youtube", response_model=YouTubeReporterResponse)
async def create_youtube_analysis(
        request: YouTubeReporterRequest,
        background_tasks: BackgroundTasks,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Submit YouTube video for analysis and generate smart visualization report.

    - **youtube_url**: YouTube video URL to analyze
    """
    try:
        user_id = current_user["user_id"]
        youtube_url = request.youtube_url

        logger.info(f"[POST] YouTube Reporter analysis requested: {youtube_url} (User: {user_id})")

        job_id = await youtube_reporter_service.create_analysis_job(
            user_id=user_id,
            youtube_url=youtube_url,
            db=db
        )

        background_tasks.add_task(
            run_youtube_analysis,
            job_id=job_id,
            user_id=user_id,
            youtube_url=youtube_url,
            db=db
        )

        return YouTubeReporterResponse(
            job_id=job_id,
            status="processing",
            message="YouTube Reporter analysis has started. AI is analyzing the video and generating a report...",
            estimated_time="2-5 minutes"
        )

    except Exception as e:
        logger.error(f"YouTube Reporter analysis request failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"YouTube Reporter analysis start failed: {str(e)}"
        )


@router.get("/jobs/{job_id}/status")
async def get_analysis_status(
        job_id: str,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Check status of YouTube Reporter analysis job.

    - **job_id**: Job ID
    """
    try:
        user_id = current_user["user_id"]

        job = database_service.get_job_by_id(db, job_id, user_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found.")

        progress_info = youtube_reporter_service.get_job_progress(job_id)

        return {
            "job_id": job_id,
            "status": job.status,
            "progress": progress_info.get("progress", 0),
            "message": progress_info.get("message", f"Status: {job.status}"),
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "input_data": job.input_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check job status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check job status: {str(e)}")


@router.get("/jobs/{job_id}/result")
async def get_analysis_result(
        job_id: str,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Retrieve YouTube Reporter analysis result.

    - **job_id**: Job ID
    """
    try:
        user_id = current_user["user_id"]

        job = database_service.get_job_by_id(db, job_id, user_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found.")

        if job.status == "processing":
            raise HTTPException(status_code=202, detail="Analysis is not yet complete. Please try again later.")
        elif job.status == "failed":
            raise HTTPException(status_code=500, detail="Analysis failed.")
        elif job.status != "completed":
            raise HTTPException(status_code=400, detail=f"Job status: {job.status}")

        reports = database_service.get_user_reports(db, user_id)
        job_report = next((r for r in reports if str(r.job_id) == job_id), None)

        if not job_report:
            raise HTTPException(status_code=404, detail="Report not found.")

        from report_service.s3.services.user_s3_service import user_s3_service
        import json

        try:
            download_url = user_s3_service.get_presigned_url(job_report.s3_key)
            report_content = None
            try:
                content = user_s3_service.get_file_content(job_report.s3_key)
                if content and job_report.file_type == 'json':
                    report_content = json.loads(content)
                    logger.info(f"Loaded report from S3: {job_id}")
            except Exception as e:
                logger.warning(f"Failed to load report content: {e}")

            return {
                "job_id": job_id,
                "status": "completed",
                "title": job_report.title,
                "created_at": job_report.created_at.isoformat(),
                "download_url": download_url,
                "s3_key": job_report.s3_key,
                "file_type": job_report.file_type,
                "content": report_content,
                "message": "YouTube Reporter analysis completed."
            }

        except Exception as e:
            logger.error(f"Failed to load S3 result: {e}")
            raise HTTPException(status_code=500, detail="Error occurred while loading analysis result.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve analysis result: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analysis result: {str(e)}")


@router.get("/jobs")
async def list_my_analyses(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    List of YouTube Reporter analysis jobs for the current logged-in user.
    """
    try:
        if not current_user:
            return {"jobs": [], "total": 0}

        user_id = current_user["user_id"]

        all_jobs = database_service.get_user_jobs(db, user_id)
        youtube_jobs = [job for job in all_jobs if job.job_type == "youtube_reporter"]

        return {
            "jobs": [
                {
                    "id": str(job.id),
                    "status": job.status,
                    "youtube_url": job.input_data.get("youtube_url", ""),
                    "created_at": job.created_at.isoformat(),
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None
                }
                for job in youtube_jobs
            ],
            "total": len(youtube_jobs)
        }

    except Exception as e:
        logger.error(f"Failed to retrieve job list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve job list: {str(e)}")


@router.delete("/jobs/{job_id}")
async def delete_analysis_job(
        job_id: str,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Delete a YouTube Reporter analysis job.

    - **job_id**: Job ID to delete
    """
    try:
        user_id = current_user["user_id"]

        success = database_service.delete_job(db, job_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Job not found.")

        return {"message": f"Job {job_id} has been deleted."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")


@router.get("/health")
async def health_check():
    """YouTube Reporter service health check"""
    try:
        return {
            "service": "YouTube Reporter",
            "status": "healthy",
            "version": "1.0.0",
            "features": {
                "smart_visualization": True,
                "comprehensive_summary": True,
                "context_analysis": True,
                "audio_generation": True
            },
            "supported_visualizations": [
                "charts", "network_diagrams", "flow_charts", "tables"
            ]
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")