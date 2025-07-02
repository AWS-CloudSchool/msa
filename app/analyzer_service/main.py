from fastapi import FastAPI
from analyzer_service.analyze.routers.youtube_analyze import router as analysis_router
from analyzer_service.audio.routers.audio_service import router as audio_router

app = FastAPI()

app.include_router(analysis_router, prefix="/analysis")
app.include_router(audio_router, prefix="/audio")

@app.get("/")
def root():
    return {"message": "Hello from analyzer_service!"}
