FROM python:3.9
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY . /app/auth_service
ENV PYTHONPATH=/app
RUN pip install --no-cache-dir -r /app/auth_service/requirements.txt
CMD ["uvicorn", "auth_service.main:app", "--host", "0.0.0.0", "--port", "8000"]