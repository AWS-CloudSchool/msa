# retrievers/kb_retriever.py
import boto3
import sys
import os
from langchain_aws import ChatBedrock

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from core.config import settings

def get_llm():
    return ChatBedrock(
        client=boto3.client("bedrock-runtime", region_name=settings.AWS_REGION),
        model_id=settings.BEDROCK_MODEL_ID,
        model_kwargs={"temperature": 0.0, "max_tokens": 4096}
    )

def get_kb_retriever():
    bedrock_client = boto3.client("bedrock-agent-runtime", region_name=settings.AWS_REGION)
    
    def retrieve(query: str):
        try:
            response = bedrock_client.retrieve(
                knowledgeBaseId=settings.BEDROCK_KB_ID,
                retrievalQuery={
                    "text": query
                },
                retrievalConfiguration={
                    "vectorSearchConfiguration": {
                        "numberOfResults": 5
                    }
                }
            )
            
            from langchain_core.documents import Document
            documents = []
            
            for result in response.get("retrievalResults", []):
                doc = Document(
                    page_content=result.get("content", {}).get("text", ""),
                    metadata={
                        "score": result.get("score", 0.0),
                        "location": result.get("location", {}),
                        "metadata": result.get("metadata", {})
                    }
                )
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            print(f" KB search fail: {e}")
            return []
    
    return retrieve