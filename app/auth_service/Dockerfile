FROM python:3.9
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY . /app

ENV PYTHONPATH=/app
RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

