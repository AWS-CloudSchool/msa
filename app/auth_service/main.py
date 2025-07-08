from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth.routers.auth import router as auth_router

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Hello from auth_service!"}

origins = [
    "https://www.tissue.cloud",
    "https://dltec80i79zlu.cloudfront.net"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth_router, prefix="/auth")
#app.include_router(auth_router.router)

# main.py ¸Ç ¾Æ·¡
for r in app.routes:
    print("ROUTE:", r.path, r.methods)
