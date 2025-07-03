from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth.routers.auth import router as auth_router

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Hello from auth_service!"}

origins = [
    "http://34.228.65.221:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth_router, prefix="/auth")

# main.py ¸Ç ¾Æ·¡
for r in app.routes:
    print("ROUTE:", r.path, r.methods)
