import json
import sys
import os
import boto3

# Add parent directory to import app.core.config
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from core.config import settings
from chatbot.tool.sync_kb import sync_kb

def lambda_handler(event, context):
    try:
        print("Lambda event triggered:", event)
        body = json.loads(event["body"]) if "body" in event else event
        user_id = body.get("user_id")
        job_id = body.get("job_id")
        
        if not user_id or not job_id:
            return {"statusCode": 400, "body": "Missing user_id or job_id"}

        # Check if caption file exists for this user/job
        s3_key = f"captions/{user_id}/{job_id}_caption.txt"
        
        # Check if the file exists in S3
        s3 = boto3.client("s3")
        try:
            s3.head_object(Bucket=settings.AWS_S3_BUCKET, Key=s3_key)
            print(f"S3 file found: {s3_key}")
        except:
            return {
                "statusCode": 404, 
                "body": json.dumps({"error": f"File not found: {s3_key}"})
            }

        # Start KB sync process
        sync_job_id = sync_kb()
        
        if sync_job_id:
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "KB sync started for specific file",
                    "sync_job_id": sync_job_id,
                    "user_id": user_id,
                    "job_id": job_id,
                    "s3_key": s3_key
                })
            }
        else:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Failed to start KB sync"})
            }

    except Exception as e:
        print("Lambda error occurred:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

def process_user_job(user_id: str, job_id: str) -> str:
    print(f"process_user_job started: user_id={user_id}, job_id={job_id}")
    event = {"user_id": user_id, "job_id": job_id}
    result = lambda_handler(event, None)
    
    print(f"lambda_handler result: {result}")
    body = json.loads(result["body"])
    if result["statusCode"] == 200:
        return body.get("sync_job_id", "KB sync completed")
    else:
        raise Exception(body.get("error", "Unknown error"))
