FROM python:3.9
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY . /app/analyzer_service
ENV PYTHONPATH=/app
RUN pip install --no-cache-dir -r /app/analyzer_service/requirements.txt
CMD ["uvicorn", "analyzer_service.main:app", "--host", "0.0.0.0", "--port", "8000"]