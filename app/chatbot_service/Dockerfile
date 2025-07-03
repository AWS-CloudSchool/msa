FROM python:3.9
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY ./chatbot_service /app/chatbot_service
ENV PYTHONPATH=/app
RUN pip install --no-cache-dir -r /app/chatbot_service/requirements.txt
CMD ["uvicorn", "chatbot_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
