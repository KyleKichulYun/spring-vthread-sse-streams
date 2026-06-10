# 1. 베이스 이미지: 경량화된 파이썬 이미지 사용
FROM python:3.12-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 의존성 파일 복사 및 설치 (Poetry 사용 시)
COPY pyproject.toml poetry.lock* ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --no-interaction --no-ansi

# 4. 소스 코드 복사
COPY . .

# 5. 실행 환경 변수 (필요시)
ENV PYTHONUNBUFFERED=1

# 6. 실행 명령어 (FastAPI API 서버 실행 기준)
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]