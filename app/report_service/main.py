from fastapi import FastAPI
from report_service.s3.routers.s3 import router as report_router
from report_service.routers.s3 import router as s3_router
from report_service.routers.user_analysis import router as user_analysis_router

app = FastAPI()

app.include_router(report_router, prefix="/report")
app.include_router(s3_router, prefix="/s3")
app.include_router(user_analysis_router, prefix="/user_analysis")

@app.get("/")
def root():
    return {"message": "Hello from report_service!"}
