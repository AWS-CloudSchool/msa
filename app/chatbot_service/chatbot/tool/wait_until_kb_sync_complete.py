#tool/wait_until_kb_sync_complete.py
import boto3
import time
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from core.config import settings

def get_ingestion_job_status(job_id: str) -> str:
    try:
        bedrock_client = boto3.client("bedrock-agent", region_name=settings.AWS_REGION)
        response = bedrock_client.get_ingestion_job(
            knowledgeBaseId=settings.BEDROCK_KB_ID,
            dataSourceId=settings.BEDROCK_DS_ID,
            ingestionJobId=job_id
        )
        return response["ingestionJob"]["status"]
    except Exception as e:
        print(f"Job status search failed: {e}")
        return "UNKNOWN"

def wait_until_kb_sync_complete(job_id: str, max_wait_sec: int = 60) -> str:
    print(f"Wait until KB synchronization completed... (MAX {max_wait_sec}s)")
    
    start_time = time.time()
    while time.time() - start_time < max_wait_sec:
        try:
            status = get_ingestion_job_status(job_id)
            if status in ["COMPLETE", "FAILED", "STOPPED"]:
                if status == "COMPLETE":
                    print(" KB synchronization completed!")
                else:
                    print(f" KB synchronization failed : {status}")
                return status
            
            time.sleep(5)
            
        except Exception as e:
            print(f"Error during checking status: {e}")
            time.sleep(2)
    
    print(f"Timeout ({max_wait_sec}초)")
    return "TIMEOUT"