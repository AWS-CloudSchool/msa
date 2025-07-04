from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from report_service.analyze.routers.youtube_analyze import router as analysis_router
from report_service.audio.routers.audio_service import router as audio_router
from report_service.s3.routers.s3 import router as report_router
#from report_service.routers.s3 import router as s3_router
from routers.user_analysis import router as user_analysis_router

app = FastAPI()

origins = [
    "http://34.228.65.221:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(analysis_router, prefix="/analysis")
app.include_router(audio_router, prefix="/audio")

app.include_router(report_router, prefix="/report")
app.include_router(analysis_router, prefix="/analyze")

#app.include_router(s3_router, prefix="/s3")
#app.include_router(user_analysis_router, prefix="/user_analysis")

@app.get("/")
def root():
    return {"message": "Hello from analyzer_service!"}
