# 베이스 이미지
FROM python:3.13-slim

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/root/.local/bin:${PATH}"

# 시스템 필수 패키지 설치 (Poetry 설치 및 빌드 도구)
RUN apt-get update \
 && apt-get install -y curl build-essential \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Poetry 설치
RUN curl -sSL https://install.python-poetry.org | python3 - \
 && /root/.local/bin/poetry --version

# 작업 디렉토리 설정
WORKDIR /app

# pyproject.toml & poetry.lock 복사 후 의존성 설치
COPY pyproject.toml poetry.lock ./

# Poetry 의존성 설치 (루트 패키지는 설치하지 않음)
RUN /root/.local/bin/poetry install --no-interaction --no-ansi --no-root

# 앱 코드 및 실행 스크립트 복사
COPY . /app

# static 파일 생성
RUN mkdir -p /app/static

# 실행 스크립트 권한 부여
RUN chmod +x /app/scripts/run.sh

# 포트 설정
EXPOSE 8000

CMD ["/app/scripts/run.sh"]
