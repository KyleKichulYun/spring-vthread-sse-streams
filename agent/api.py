import uvicorn
from contextlib import asynccontextmanager  # 💡 1. 누락된 임포트 추가
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage

# 🚀 분리한 모듈 임포트
from agent import graph_app
from config import close_db, logger

# 💡 [핵심] FastAPI 시작과 종료 시점을 제어하는 로직
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시점 (yield 이전) - 현재는 config.py에서 자동 연결되므로 비워둠
    yield
    # 종료 시점 (yield 이후) - 서버가 꺼질 때 실행
    close_db()

# 💡 2. FastAPI 객체 생성 시 lifespan 파라미터 연결
app = FastAPI(title="LangGraph Meta-Cognition API", version="1.0", lifespan=lifespan)

class ChatRequest(BaseModel):
    question: str = Field(..., example="올해 체력단련비 지원 한도가 얼마야?")
    thread_id: str = "default-session"

class ChatResponse(BaseModel):
    answer: str
    final_query: str
    retry_count: int

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        logger.info(f"🚀 [API 요청 수신] 질문: {request.question} (Thread: {request.thread_id})")

        config = {"configurable": {"thread_id": request.thread_id}}

        input_state = {
            "messages": [HumanMessage(content=request.question)],
            "question": request.question,
            "search_query": request.question,
            "retry_count": 0
        }

        # agent 모듈에서 가져온 graph_app 비동기 실행
        result = await graph_app.ainvoke(input_state, config=config)

        final_answer = result.get("generation", "답변을 생성하지 못했습니다.")

        return ChatResponse(
            answer=final_answer,
            final_query=result.get("search_query", request.question),
            retry_count=result.get("retry_count", 0)
        )
    except Exception as e:
        logger.exception(f"❌ [에러 발생] API 처리 중 예기치 못한 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail="AI 에이전트 처리 중 오류가 발생했습니다.")

if __name__ == "__main__":
    logger.info("==================================================")
    logger.info("🌐 FastAPI 서버를 시작합니다...")
    logger.info("==================================================")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)