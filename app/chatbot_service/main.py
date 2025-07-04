from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from chatbot.routers.chat_router import router as chat_router_router

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello from chatbot_service!"}


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

app.include_router(chat_router_router, prefix="/chat_router")

# main.py ¸Ç ¾Æ·¡
for r in app.routes:
    print("ROUTE:", r.path, r.methods)