from fastapi import APIRouter, HTTPException, Query, Depends, Header
from typing import Dict, Any, List, Optional
from report_service.s3.services.s3_service import s3_service
from report_service.core.config import settings
import json
import requests


router = APIRouter(
    prefix="/s3",
    tags=["s3"]
)

def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    try:
        response = requests.post(
            "http://auth_service:8000/auth/verify-token",
            headers={"Authorization": authorization},
            timeout=3
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Auth service unreachable: {str(e)}")
        

@router.get("/list")
async def list_s3_objects(
    prefix: str = Query("", description="S3 object key prefix"),
    max_keys: int = Query(100, description="Maximum number of objects")
) -> Dict[str, Any]:
    """
    List objects in S3 bucket

    - **prefix**: Object key prefix (e.g., 'reports/')
    - **max_keys**: Maximum number of objects to retrieve
    """
    try:
        objects = s3_service.list_objects(prefix=prefix, max_keys=max_keys)
        
        return {
            "bucket": s3_service.bucket_name,
            "region": settings.AWS_REGION,
            "prefix": prefix,
            "objects": [
                {
                    "Key": obj.get("Key", ""),
                    "Size": obj.get("Size", 0),
                    "LastModified": obj.get("LastModified", "").isoformat() if hasattr(obj.get("LastModified", ""), "isoformat") else obj.get("LastModified", ""),
                    "ETag": obj.get("ETag", ""),
                    "StorageClass": obj.get("StorageClass", "")
                }
                for obj in objects
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list S3 objects: {str(e)}")


@router.get("/object/{key:path}")
async def get_s3_object(key: str) -> Dict[str, Any]:
    """
    Retrieve metadata and presigned URL of a specific S3 object

    - **key**: Object key (path)
    """
    try:
        response = s3_service.s3_client.head_object(
            Bucket=s3_service.bucket_name,
            Key=key
        )
        
        url = s3_service.s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': s3_service.bucket_name, 'Key': key},
            ExpiresIn=3600
        )
        
        return {
            "key": key,
            "size": response.get("ContentLength", 0),
            "last_modified": response.get("LastModified", "").isoformat() if hasattr(response.get("LastModified", ""), "isoformat") else response.get("LastModified", ""),
            "content_type": response.get("ContentType", ""),
            "metadata": response.get("Metadata", {}),
            "url": url
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"S3 object not found: {str(e)}")


@router.get("/reports/list")
async def list_reports_with_metadata(current_user: dict = Depends(get_current_user)) -> List[Dict[str, Any]]:
    """
    List user reports with metadata
    """
    try:
        user_id = current_user["user_id"]
        report_objects = s3_service.list_objects(prefix=f"reports/{user_id}/", max_keys=100)
        
        reports = []
        for obj in report_objects:
            if obj.get("Key", "").endswith("_report.json"):
                try:
                    report_content = s3_service.get_file_content(obj.get("Key", ""))
                    if report_content:
                        report_data = json.loads(report_content)
                        job_id = obj.get("Key", "").replace(f"reports/{user_id}/", "").replace("_report.json", "")
                        metadata = report_data.get("metadata", {})
                        
                        report_url = s3_service.s3_client.generate_presigned_url(
                            'get_object',
                            Params={'Bucket': s3_service.bucket_name, 'Key': obj.get("Key", "")},
                            ExpiresIn=3600
                        )
                        
                        reports.append({
                            "id": job_id,
                            "key": obj.get("Key", ""),
                            "title": metadata.get("youtube_title", f"YouTube Report - {job_id[:8]}"),
                            "youtube_url": metadata.get("youtube_url", ""),
                            "youtube_channel": metadata.get("youtube_channel", "Unknown Channel"),
                            "youtube_duration": metadata.get("youtube_duration", "Unknown"),
                            "youtube_thumbnail": metadata.get("youtube_thumbnail", ""),
                            "video_id": metadata.get("video_id", ""),
                            "type": "YouTube",
                            "analysis_type": metadata.get("analysis_type", "youtube_analysis"),
                            "status": metadata.get("status", "completed"),
                            "last_modified": obj.get("LastModified", "").isoformat() if hasattr(obj.get("LastModified", ""), "isoformat") else obj.get("LastModified", ""),
                            "url": report_url,
                            "metadata": metadata
                        })
                        
                except Exception as e:
                    print(f"Failed to process report: {obj.get('Key', '')} - {e}")
                    continue
        
        reports.sort(key=lambda x: x.get("last_modified", ""), reverse=True)
        
        return reports
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve report list: {str(e)}")
