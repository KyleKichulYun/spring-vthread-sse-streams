> A high-performance real-time SSE broadcasting system integrated with an autonomous LLM Agent, built with Java 21 Virtual Threads, Spring Boot 3, Redis Streams, RabbitMQ, Next.js, and Python (LangGraph/Neo4j).
> (Java 21 가상 스레드, Spring Boot 3 AOT, Redis Streams, RabbitMQ, Next.js 및 자율형 LLM 에이전트로 구축된 고성능 실시간 SSE 브로드캐스팅 시스템)

# 🚀 High-Concurrency Realtime Event Streams & AI Agent

A high-performance, real-time event broadcasting system designed to handle massive concurrent Server-Sent Events (SSE) connections. This system seamlessly integrates an **Autonomous LLM Agent** that processes complex data using **Graph RAG** and a **Meta-Cognition Self-Correction Loop**, broadcasting AI-generated insights in real-time.

## 🎯 Project Motivation & Architecture

Traditional thread-per-request models struggle with long-lived connections like SSE. This project overcomes these limitations using modern Java features (Virtual Threads), while simultaneously integrating an advanced AI reasoning engine capable of self-reflection via an asynchronous Message Queue architecture.

### Why This Tech Stack? (기술 도입 배경)

* **Spring Boot 3 AOT & Java 21 Virtual Threads:** Provides an ultra-lightweight, highly scalable backend capable of maintaining thousands of concurrent SSE connections with zero context-switching overhead.
* **RabbitMQ (Message Broker):** Decouples the fast Java backend from the AI processing time. It asynchronously routes user questions to the AI worker and reliably returns the generated answers without blocking the main server.
* **Redis (Pub/Sub & Streams):** Acts as the central nervous system for broadcasting. It reliably buffers AI-generated insights, ensuring no messages are lost before they are broadcasted to distributed client SSE connections.
* **🧠 AI Meta-Cognition Agent (Python, LangGraph & Neo4j):** Instead of a simple chatbot, the Python backend serves as an intelligent reasoning engine utilizing an advanced **Graph RAG** architecture.
* **Graph-based Retrieval (Neo4j):** Understands complex relationships between data points, providing deep contextual grounding rather than simple keyword matching.
* **Self-Correction Loop (Reflexion):** Built with LangGraph, the LLM agent autonomously evaluates its own answers (Self-Reflection). If an answer lacks context or hallucinates, the agent automatically rewrites the query and retrieves data again until it reaches a high-confidence conclusion before replying.

---

## 📂 Project Structure & Data Flow (프로젝트 구조 및 데이터 흐름)

본 프로젝트는 언어와 프레임워크의 장점을 극대화하기 위해 3개의 독립적인 서비스로 구성된 **폴리글랏 모노레포(Polyglot Monorepo)** 아키텍처를 채택했습니다.

### Directory Tree

```text
polyglot-sse-project/          # Root Directory
├── docker-compose.yml         # 🐳 인프라 전체 통합 실행 (RabbitMQ, Redis, Neo4j 등)
│
├── 🐍 agent/                  # [Python] 메타인지 AI 에이전트 (LangGraph + RabbitMQ)
│   ├── config.py              # 환경 변수 및 공통 커넥션 설정
│   ├── agent.py               # LangGraph 워크플로우 및 노드 핵심 로직
│   ├── api.py                 # (선택) HTTP REST API 테스트용 진입점 (FastAPI)
│   ├── worker.py              # (운영) RabbitMQ 메시지 큐 구독 및 처리 백그라운드 워커
│   └── requirements.txt       # 파이썬 패키지 의존성
│
├── ☕ backend/                # [Java] 실시간 스트리밍 서버 (Spring Boot 3 + Virtual Threads)
│   ├── build.gradle           # 의존성 및 AOT/Native 빌드 설정
│   └── src/main/java/.../     # Controllers, Services, RabbitMQ Config, Redis Pub/Sub, SSE
│
└── ⚛️ frontend/               # [TypeScript] 사용자 웹 UI (Next.js - 예정)
    └── app/                   # 채팅 UI 및 SSE 구독(Subscribe) 훅

```

### 🔄 How It Works (데이터 흐름)

1. **사용자 입력 (`frontend`):** 사용자가 Next.js 화면에서 질문을 입력합니다.
2. **요청 접수 (`backend`):** Spring Boot가 `/api/chat`을 통해 질문을 받습니다. 가상 스레드(Virtual Threads)가 할당되어 리소스를 최소화합니다.
3. **작업 큐 적재 (`backend` -> `RabbitMQ`):** Spring Boot가 HTTP 통신을 기다리지 않고 질문 데이터를 즉시 RabbitMQ의 `question.queue`로 발행(Publish)합니다.
4. **AI 사고 및 검색 (`RabbitMQ` -> `agent`):** 백그라운드에서 대기 중인 파이썬 워커(`worker.py`)가 큐에서 질문을 가져옵니다. **Neo4j**에서 Graph RAG 검색을 수행하고, 스스로 환각을 평가(Meta-Cognition)하여 완벽한 답변을 생성합니다.
5. **답변 큐 반환 (`agent` -> `RabbitMQ`):** 파이썬 워커가 최종 생성된 정답을 RabbitMQ의 `answer.queue`로 발행합니다.
6. **메시지 발행 (`backend`):** Spring Boot의 RabbitMQ Listener가 정답을 수신하고, 이를 분산 환경 전파를 위해 **Redis**에 퍼블리시합니다.
7. **실시간 브로드캐스팅 (`backend` -> `frontend`):** Spring Boot의 Redis Listener가 새 메시지를 감지하고, SSE(Server-Sent Events)를 통해 구독 중인 클라이언트 화면에 실시간으로 전송합니다.

---

## 🛠️ Getting Started (실행 방법)

### Python LLM Agent Setup (AI 에이전트 환경 설정)

LangGraph, Neo4j 연동 및 RabbitMQ 큐 처리를 위한 파이썬 환경 설정 방법입니다. 본 프로젝트는 보안과 중앙 관리를 위해 **Doppler**를 사용하여 환경 변수를 주입합니다.

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

# LangGraph, OpenAI, Pika 등 프로젝트에 필요한 패키지 일괄 설치
pip install -r requirements.txt

```

**4. 🐳 인프라 전체 실행 (Docker Compose - 권장)**
명령어 한 줄로 `Neo4j DB`, `Redis`, `RabbitMQ`를 한 번에 백그라운드에서 실행합니다.

```bash
# 백그라운드(-d)로 인프라 동시 빌드 및 실행!
docker-compose up -d --build

```

**5. 💻 에이전트 로컬 실행**
용도에 따라 REST API 서버 또는 RabbitMQ 백그라운드 워커를 선택하여 실행할 수 있습니다.

```bash
# 1. Doppler CLI 설정 (최초 1회)
doppler login
doppler setup

# 2. [운영 모드] Spring Boot와 연동하기 위해 RabbitMQ 워커 실행
doppler run -- python worker.py

# 3. [테스트 모드] HTTP 요청을 통한 에이전트 단독 테스트 시 FastAPI 서버 실행
doppler run -- python api.py

```

---

## ⚙️ Environment Variables (환경 변수 설정)

본 프로젝트는 로컬 `.env` 파일 대신 **Doppler** 대시보드를 통해 환경 변수를 중앙 관리합니다. 프로젝트 세팅 시 대시보드에 아래의 키값들을 등록해 주세요.
*(Doppler를 사용하지 않는 환경이라면 루트 디렉토리에 `.env` 파일을 생성하고 기입합니다.)*

```env
# ------------------------------
# Messaging & Cache (공통)
# ------------------------------
REDIS_HOST=localhost
REDIS_PORT=6379

RABBITMQ_HOST=localhost
RABBITMQ_USER=guest
RABBITMQ_PASS=guest

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

Spring Boot 서버는 Java 21의 Virtual Threads를 활용하여 대규모 SSE 연결을 논블로킹(Non-blocking) 방식으로 처리하고, RabbitMQ 및 Redis 메시지를 구독(Subscribe)합니다.

**1. 필수 요구사항 (Prerequisites)**

* JDK 21 이상 설치
* (선택) GraalVM (Native Image 빌드 시 필요)
* **주의:** `docker-compose up`을 통해 RabbitMQ와 Redis 인프라가 켜져 있어야 합니다.

**2. 애플리케이션 실행 (Gradle 기준)**

```bash
# 스프링 부트 프로젝트 디렉토리로 이동
cd backend

# Gradle Wrapper에 실행 권한 부여 (Mac/Linux)
chmod +x gradlew

# 스프링 부트 서버 빌드 및 실행
./gradlew bootRun

```

**3. 🚀 AOT & Native Image 빌드 (고성능/초경량 배포용)**
Spring Boot 3의 AOT(Ahead-of-Time) 컴파일과 GraalVM을 이용해 네이티브 이미지로 빌드하면, 시작 시간을 밀리초 단위로 단축하고 메모리 사용량을 극적으로 줄일 수 있습니다.

```bash
# Native Image 빌드 (시스템 리소스에 따라 시간이 다소 소요될 수 있습니다)
./gradlew nativeCompile

# 빌드된 네이티브 실행 파일 직접 실행
./build/native/nativeCompile/backend

```