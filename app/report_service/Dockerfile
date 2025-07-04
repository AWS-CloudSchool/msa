FROM python:3.9
ENV PYTHONUNBUFFERED=1

WORKDIR /app/report_service

COPY . /app/report_service
COPY ../../requirements.txt /app/requirements.txt

ENV PYTHONPATH=/app
RUN pip install --no-cache-dir -r /app/requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
