from fastapi import FastAPI
from auth_service.auth.routers.auth import router as auth_router

app = FastAPI()

app.include_router(auth_router, prefix="/auth")

@app.get("/")
def root():
    return {"message": "Hello from auth_service!"}
