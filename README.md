
> A high-performance real-time SSE broadcasting system integrated with an autonomous LLM Agent, built with Java 21 Virtual Threads, Spring Boot 3, Redis Streams, Next.js, and Python (LangGraph/Neo4j).
> (Java 21 가상 스레드, Spring Boot 3 AOT, Redis Streams, Next.js 및 자율형 LLM 에이전트로 구축된 고성능 실시간 SSE 브로드캐스팅 시스템)

# 🚀 High-Concurrency Realtime Event Streams & AI Agent

A high-performance, real-time event broadcasting system designed to handle massive concurrent Server-Sent Events (SSE) connections. This system seamlessly integrates an **Autonomous LLM Agent** that processes complex data using **Graph RAG** and a **Meta-Cognition Self-Correction Loop**, broadcasting AI-generated insights in real-time.

## 🎯 Project Motivation & Architecture

Traditional thread-per-request models struggle with long-lived connections like SSE. This project overcomes these limitations using modern Java features (Virtual Threads), while simultaneously integrating an advanced AI reasoning engine capable of self-reflection.

### Why This Tech Stack? (기술 도입 배경)

* **Spring Boot 3 AOT & Java 21 Virtual Threads:** Provides an ultra-lightweight, highly scalable backend capable of maintaining thousands of concurrent SSE connections with zero context-switching overhead.
* **Redis Streams:** Acts as the central nervous system. It reliably buffers both standard system events and AI-generated insights, ensuring no messages are lost before they are broadcasted to clients via SSE.
* **🧠 AI Meta-Cognition Agent (Python, LangGraph & Neo4j):** Instead of a simple chatbot, the Python backend serves as an intelligent reasoning engine utilizing an advanced **Graph RAG** architecture.
* **Graph-based Retrieval (Neo4j):** Understands complex relationships between data points, providing deep contextual grounding rather than simple keyword matching.
* **Self-Correction Loop (Reflexion):** Built with LangGraph (or n8n), the LLM agent autonomously evaluates its own answers (Self-Reflection). If an answer lacks context or hallucinates, the agent automatically rewrites the query and retrieves data again until it reaches a high-confidence conclusion before publishing to Redis.



---

## 🛠️ Getting Started (실행 방법)

### Python LLM Agent Setup (AI 에이전트 환경 설정)

LangGraph, Neo4j 연동 및 LLM 데이터 처리를 위한 파이썬 환경 설정 방법입니다. 본 프로젝트는 보안과 중앙 관리를 위해 **Doppler**를 사용하여 환경 변수를 주입합니다.

**1. 가상환경 생성 (최초 1회만 수행)**

```bash
# Python 3.12 버전을 기준으로 .venv라는 이름의 가상환경을 생성합니다.
python3.12 -m venv .venv

```

**2. 가상환경 활성화 (작업 시 매번 켜기)**

```bash
# Mac/Linux 기준
source .venv/bin/activate

# Windows의 경우: .venv\Scripts\activate

```

**3. 패키지 관리자 업데이트 및 의존성 설치**

```bash
# pip 업그레이드 (권장)
pip install --upgrade pip

# LangGraph, OpenAI, FastAPI 등 프로젝트에 필요한 패키지 일괄 설치
pip install -r requirements.txt

```

**4. Doppler 연동 및 서버 실행**

```bash
# 1. Doppler CLI 설치 후 로그인 (최초 1회)
doppler login

# 2. 로컬 프로젝트와 Doppler 연결 (프로젝트 및 환경 선택)
doppler setup

# 3. Uvicorn으로 FastAPI 서버 실행 (Doppler가 런타임에 환경 변수 주입)
doppler run -- uvicorn main:app --reload

```

---

## ⚙️ Environment Variables (환경 변수 설정)

본 프로젝트는 보안을 위해 로컬 `.env` 파일을 사용하지 않고 **Doppler** 대시보드를 통해 환경 변수를 관리합니다. 프로젝트 세팅 시 Doppler 대시보드에 아래의 키값들을 등록해 주세요.
*(Doppler를 사용하지 않는 환경이라면 루트 디렉토리에 `.env` 파일을 생성하고 기입합니다.)*

```env
# ------------------------------
# Redis Configuration (공통)
# ------------------------------
REDIS_HOST=localhost
REDIS_PORT=6379

# ------------------------------
# Python LLM Agent Configuration (AI 에이전트용)
# ------------------------------
OPENAI_API_KEY=sk-your-openai-api-key
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-neo4j-password

# ------------------------------
# Spring Boot Configuration (백엔드용)
# ------------------------------
SERVER_PORT=8080

```

---

## ☕ Spring Boot Backend Setup (백엔드 설정 및 실행)

Spring Boot 서버는 Java 21의 Virtual Threads를 활용하여 대규모 SSE 연결을 논블로킹(Non-blocking) 방식으로 처리하고 Redis Streams의 메시지를 구독(Subscribe)합니다.

**1. 필수 요구사항 (Prerequisites)**

* JDK 21 이상 설치
* (선택) GraalVM (Native Image 빌드 시 필요)
* 로컬 환경에 Redis 서버 실행 중

**2. Redis 서버 실행 (Docker 활용 시)**
로컬에 Redis가 설치되어 있지 않다면, 도커를 이용해 백그라운드에서 빠르게 실행할 수 있습니다.

```bash
docker run -d --name redis-streams -p 6379:6379 redis:latest

```

**3. 애플리케이션 실행 (Gradle 기준)**

```bash
# 스프링 부트 프로젝트 디렉토리로 이동 (실제 경로에 맞게 수정)
cd backend

# Gradle Wrapper에 실행 권한 부여 (Mac/Linux)
chmod +x gradlew

# 스프링 부트 서버 빌드 및 실행
./gradlew bootRun

```

**4. 🚀 AOT & Native Image 빌드 (고성능/초경량 배포용)**
Spring Boot 3의 AOT(Ahead-of-Time) 컴파일과 GraalVM을 이용해 네이티브 이미지로 빌드하면, 시작 시간을 밀리초 단위로 단축하고 메모리 사용량을 극적으로 줄일 수 있습니다.

```bash
# Native Image 빌드 (시스템 리소스에 따라 시간이 다소 소요될 수 있습니다)
./gradlew nativeCompile

# 빌드된 네이티브 실행 파일 실행
./build/native/nativeCompile/backend

```
