from fastapi import FastAPI
from youtube_service.search.routers.youtube_search import router as youtube_router

app = FastAPI()

app.include_router(youtube_router, prefix="/youtube")

@app.get("/")
def root():
    return {"message": "Hello from youtube_service!"}
