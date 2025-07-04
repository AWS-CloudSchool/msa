FROM python:3.9
ENV PYTHONUNBUFFERED=1

# 앱 코드 위치
WORKDIR /app/auth_service

# 코드 복사
COPY . /app/auth_service
COPY ../../requirements.txt /app/requirements.txt

# PYTHONPATH 설정
ENV PYTHONPATH=/app

# 의존성 설치
RUN pip install --no-cache-dir -r /app/requirements.txt

# 앱 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
