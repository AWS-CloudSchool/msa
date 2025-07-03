FROM python:3.9
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY ./youtube_service /app/youtube_service
ENV PYTHONPATH=/app
RUN pip install --no-cache-dir -r /app/youtube_service/requirements.txt
CMD ["uvicorn", "youtube_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
