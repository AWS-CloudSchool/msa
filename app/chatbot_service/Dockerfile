FROM python:3.9
ENV PYTHONUNBUFFERED=1

WORKDIR /app/chatbot_service

# 여기 경로 수정됨
COPY . /app/chatbot_service
COPY ../../requirements.txt /app/requirements.txt

ENV PYTHONPATH=/app
RUN pip install --no-cache-dir -r /app/requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
