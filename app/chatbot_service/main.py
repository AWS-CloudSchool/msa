from fastapi import FastAPI
from chatbot_service.chatbot.routers.chat_router import router as chat_router_router

app = FastAPI()

app.include_router(chat_router_router, prefix="/chat_router")

@app.get("/")
def root():
    return {"message": "Hello from chatbot_service!"}
