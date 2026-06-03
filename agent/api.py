import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage

# 🚀 분리한 모듈 임포트
from agent import graph_app

app = FastAPI(title="LangGraph Meta-Cognition API", version="1.0")

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
        print(f"\n🚀 [API 요청 수신] 질문: {request.question} (Thread: {request.thread_id})")

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
        print(f"❌ [에러 발생] {str(e)}")
        raise HTTPException(status_code=500, detail="AI 에이전트 처리 중 오류가 발생했습니다.")

if __name__ == "__main__":
    print("==================================================")
    print("🌐 FastAPI 서버를 시작합니다...")
    print("==================================================")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)