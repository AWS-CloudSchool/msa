import boto3
import json
import sys
import os
from botocore.exceptions import ClientError

# Add root path to import app.core.config
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from core.config import settings

def sync_kb():
    """Start a new Bedrock Knowledge Base ingestion job."""
    try:
        bedrock_client = boto3.client("bedrock-agent", region_name=settings.AWS_REGION)
        
        response = bedrock_client.start_ingestion_job(
            knowledgeBaseId=settings.BEDROCK_KB_ID,
            dataSourceId=settings.BEDROCK_DS_ID
        )
        
        job_id = response["ingestionJob"]["ingestionJobId"]
        print(f"KB ingestion job started: {job_id}")
        return job_id
        
    except Exception as e:
        print(f"Failed to start KB ingestion job: {e}")
        return None

    # The following block is unreachable due to the return above,
    # but retained for debugging structure if refactored later.
    print("===== Lambda sync_kb ENTRY =====")
    print("MODULE FILE:", __file__)
    print("BEDROCK_DS_ID:", settings.BEDROCK_DS_ID, type(settings.BEDROCK_DS_ID))
    print("BEDROCK_KB_ID:", settings.BEDROCK_KB_ID, type(settings.BEDROCK_KB_ID))
    print("AWS_REGION:", settings.AWS_REGION, type(settings.AWS_REGION))

    # Check for missing configuration
    if not settings.BEDROCK_KB_ID or not settings.BEDROCK_DS_ID:
        print("Missing BEDROCK_KB_ID or BEDROCK_DS_ID configuration.")
        print(f"BEDROCK_KB_ID: {settings.BEDROCK_KB_ID}")
        print(f"BEDROCK_DS_ID: {settings.BEDROCK_DS_ID}")
        return None

    print("Proceeding to fallback ingestion trigger.")
    kb_client = boto3.client("bedrock-agent", region_name=settings.AWS_REGION)
    print("Bedrock Agent client initialized.")

    # Try to find an already running ingestion job
    try:
        print("Checking existing ingestion jobs...")
        jobs = kb_client.list_ingestion_jobs(
            knowledgeBaseId=settings.BEDROCK_KB_ID,
            dataSourceId=settings.BEDROCK_DS_ID
        )
        print(f"Total existing jobs: {len(jobs.get('ingestionJobSummaries', []))}")
        
        for job in jobs.get("ingestionJobSummaries", []):
            print(f"  - Job ID: {job.get('ingestionJobId')}, Status: {job.get('status')}")
            if (
                str(job.get("dataSourceId")) == str(settings.BEDROCK_DS_ID) and
                job.get("status") in ["STARTING", "IN_PROGRESS", "COMPLETE"]
            ):
                job_id = job["ingestionJobId"]
                print(f"Found already running/complete ingestion job: {job_id}")
                return str(job_id)
    except Exception as e:
        print(f"Failed to check existing ingestion jobs: {e}")

    # Attempt new ingestion job as fallback
    try:
        # AWS Bedrock API requires camelCase parameters
        params = {
            "knowledgeBaseId": str(settings.BEDROCK_KB_ID),
            "dataSourceId": str(settings.BEDROCK_DS_ID)
        }
        print("Starting new ingestion job...")
        print("Calling start_ingestion_job with params:", params)
        print("Parameter types:", {k: type(v) for k, v in params.items()})
        print("Parameter values:")
        print(f"  knowledgeBaseId: '{params['knowledgeBaseId']}' (length: {len(params['knowledgeBaseId'])})")
        print(f"  dataSourceId: '{params['dataSourceId']}' (length: {len(params['dataSourceId'])})")

        response = kb_client.start_ingestion_job(**params)
        job_id = response["ingestionJob"]["ingestionJobId"]
        print("New ingestion job started:", job_id)
        return str(job_id)

    except ClientError as e:
        print("AWS ClientError occurred.")
        print("Error message:", str(e))
        print("Raw AWS response:", json.dumps(e.response, indent=2, ensure_ascii=False))
        return None

    except Exception as e:
        print("General exception occurred during ingestion job.")
        print("Error message:", str(e))
        return None
