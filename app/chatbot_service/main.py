from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from chatbot_service.chatbot.routers.chat_router import router as chat_router_router

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

app.include_router(chat_router_router, prefix="/chat_router")

@app.get("/")
def root():
    return {"message": "Hello from chatbot_service!"}
