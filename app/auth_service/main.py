from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth_service.auth.routers.auth import router as auth_router

app = FastAPI()

app.include_router(auth_router, prefix="/auth")

@app.get("/")
def root():
    return {"message": "Hello from auth_service!"}

origins = [
    "http://44.244.212.37:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

for route in app.routes:
    print(f"? {route.path}")


app.include_router(auth_router, prefix="/auth")
