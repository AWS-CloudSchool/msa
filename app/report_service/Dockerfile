FROM python:3.9
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY . /app/report_service
ENV PYTHONPATH=/app
RUN pip install --no-cache-dir -r /app/report_service/requirements.txt
CMD ["uvicorn", "report_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
