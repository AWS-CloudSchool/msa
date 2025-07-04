from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from youtube_service.search.routers.youtube_search import router as youtube_router

app = FastAPI()

# ? CORS Çã¿ë
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

app.include_router(youtube_router)

@app.get("/")
def root():
    return {"message": "Hello from youtube_service!"}


for route in app.routes:
    print(f"? {route.path}")