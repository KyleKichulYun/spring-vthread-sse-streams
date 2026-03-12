import os
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
# from dotenv import load_dotenv
from typing import TypedDict, List
from pydantic import BaseModel, Field

# --- [NEW] FastAPI 관련 패키지 추가 ---
from fastapi import FastAPI, HTTPException
import uvicorn

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from neo4j import GraphDatabase

# 1. 환경 변수 로드 (.env 파일에서 OPENAI_API_KEY 자동 인식)
# doppler를 사용하여 환경 변수를 관리하는 경우, load_dotenv()는 필요하지 않을 수 있습니다.
# load_dotenv()

# 2. LLM 초기화 (평가관 역할은 일관성이 중요하므로 temperature를 0으로 설정)
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# 3. 상태(State) 정의
class AgentState(TypedDict):
    question: str
    documents: List[str]
    generation: str
    feedback: str
    retry_count: int

# ==========================================
# [핵심] Pydantic을 이용한 평가 결과 구조 강제
# ==========================================
class GradeOutput(BaseModel):
    score: str = Field(description="평가 결과. 'Pass' 또는 'Fail'만 입력")
    reason: str = Field(description="왜 이런 평가를 내렸는지 논리적인 이유 1~2문장")

class RewriteOutput(BaseModel):
    improved_query: str = Field(description="원래 질문을 더 구체적이고 명확하게 개선한 검색어")
    reasoning: str = Field(description="왜 이렇게 검색어를 개선했는지 간단한 설명")

# ==========================================
# 노드(Node) 실제 구현
# ==========================================
def retrieve_node(state: AgentState):
    question = state['question']
    print(f"\n[DB 검색] 질문: '{question}'에 대한 관련 문서 검색 중...")

    # 띄어쓰기 기준으로 키워드를 분리 (간단한 키워드 매칭용)
    keywords = question.split()

    # [Cyper 쿼리 예시 - 실제 DB 스키마에 맞게 조정 필요]
    # 예: MATCH (d:Document) WHERE any(keyword IN $keywords WHERE d.content CONTAINS keyword) RETURN d
    cypher_query = """
    MATCH (d:Document)
    WHERE any(keyword IN $keywords WHERE d.content CONTAINS keyword OR d.title CONTAINS keyword)
    RETURN d.content AS content
    LIMIT 3
    """

    # Neo4j에서 쿼리 실행
    with neo4j_driver.session() as session:
        result = session.run(cypher_query, keywords=keywords)
        documents = [record["content"] for record in result]

    # 검색된 문서가 없을 경우 빈 배열 대신 안내 문구 전달 (LLM이 인식할 수 있도록)
    if not documents:
        print("⚠️ 관련 문서가 검색되지 않았습니다. LLM이 환각을 유도할 수 있으므로, 빈 문서 대신 안내 메시지를 제공합니다.")
        documents = ["관련 문서가 검색되지 않았습니다. 질문을 더 구체적으로 수정해보세요."]
    else:
        print(f"✅ {len(documents)}개의 관련 문서 검색 완료.")

    return {"documents": documents, "retry_count": state.get("retry_count", 0)}

def generate_node(state: AgentState):
    print("\n[생성] 답변 초안 작성 중...")

    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 제공된 문서(Context)를 바탕으로 사용자의 질문에 답하는 유능한 어시스턴트입니다.\n문서: {context}"),
        ("user", "질문: {question}")
    ])

    chain = prompt | llm | StrOutputParser()
    context_str = "\n".join(state["documents"])

    generation = chain.invoke({"context": context_str, "question": state["question"]})
    print(f"💡 답변 초안: {generation}")

    return {"generation": generation}

def evaluate_node(state: AgentState):
    print("\n[평가] 환각 여부 및 품질 검증 중...")

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 사실 관계를 검증하는 깐깐한 감사관입니다.
        '생성된 답변'이 오직 '제공된 문서'에만 기반했는지 확인하세요.
        문서에 없는 내용(예: 구체적인 금액 등)을 임의로 지어냈다면 무조건 'Fail'을 부여하세요.
        평가 기준:
        1) 문서에 명시된 정보만 사용했는가? (Pass/Fail)
        2) 평가 이유를 간단히 설명 (1~2문장)"""),
        ("user", "제공된 문서: {context}\n\n생성된 답변: {generation}")
    ])

    # LLM이 무조건 GradeOutput(Pydantic) 형태의 JSON을 반환하도록 강제
    structured_llm = llm.with_structured_output(GradeOutput)
    chain = prompt | structured_llm

    context_str = "\n".join(state["documents"])
    result = chain.invoke({"context": context_str, "generation": state["generation"]})

    feedback_str = f"{result.score}: {result.reason}"
    print(f"⚖️ 평가 결과: {feedback_str}")

    return {"feedback": feedback_str}

def rewrite_query_node(state: AgentState):
    print("\n[재작성] 평가 실패. 검색어 수정 중...")
    # (여기도 LLM을 붙일 수 있지만, 일단 테스트를 위해 문자열 추가로 대체)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 AI 에이전트의 검색 성능을 극대화하는 '전문 검색 전략가'입니다.
        이전 검색이 실패한 이유(피드백)를 분석하여, DB에서 정답을 찾을 수 있는 **새로운 검색 쿼리**를 작성하세요.
        문장이 아닌, 검색 매칭률이 높은 '핵심 키워드' 위주로 재구성하는 것이 좋습니다."""),
        ("user", "원래 질문: {question}\n\n이전 평가 피드백: {feedback}")
    ])
    # LLM이 무조건 RewriteOutput(Pydantic) 형태의 JSON을 반환하도록 강제
    structured_llm = llm.with_structured_output(RewriteOutput)
    chain = prompt | structured_llm

    # 현재 상태의 질문과 피드백을 LLM에 전달하여 개선된 검색어를 받아옵니다.
    result = chain.invoke({"question": state['question'], "feedback": state["feedback"]})
    print(f"🔄 새 검색어 적용: '{result.improved_query}'\n💡 변경 이유: {result.reasoning}")
    return {"question": result.improved_query, "retry_count": state["retry_count"] + 1}

# ==========================================
# 라우팅 및 그래프 조립
# ==========================================
def route_evaluation(state: AgentState):
    if "Pass" in state["feedback"]:
        print("\n✅ [완료] 검증 통과! 최종 답변을 전송합니다.")
        return "end"
    elif state["retry_count"] >= 2:
        print("\n❌ [중단] 최대 재시도 횟수 초과. 환각을 방지하기 위해 답변을 포기합니다.")
        return "end"
    else:
        return "rewrite"

# 그래프 조립 (변수명을 app -> graph_app으로 변경)
workflow = StateGraph(AgentState)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", generate_node)
workflow.add_node("evaluate", evaluate_node)
workflow.add_node("rewrite_query", rewrite_query_node)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", "evaluate")
workflow.add_conditional_edges("evaluate", route_evaluation, {"end": END, "rewrite": "rewrite_query"})
workflow.add_edge("rewrite_query", "retrieve")

# 🚀 1. 메모리 저장소 인스턴스 생성
memory = MemorySaver()

# 🚀 2. 컴파일 할 때 checkpointer로 메모리를 넘겨줍니다!
# 기존: app = workflow.compile()
app = workflow.compile(checkpointer=memory)


# ==========================================
# [NEW] FastAPI 서버 설정 및 API 엔드포인트
# ==========================================
app = FastAPI(title="LangGraph Meta-Cognition API", version="1.0")

# API 요청/응답 모델 정의
class ChatRequest(BaseModel):
    question: str = Field(..., example="올해 체력단련비 지원 한도가 얼마야?")
    # 🚀 클라이언트가 스레드 ID를 주지 않으면 기본값으로 새 세션을 만듭니다.
    thread_id: str = "default-session"    

class ChatResponse(BaseModel):
    answer: str
    final_query: str
    retry_count: int

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    # 🚀 설정(config) 객체에 thread_id를 담아서 그래프에 전달합니다.
    config = {"configurable": {"thread_id": request.thread_id}}
    
    # 사용자의 질문을 그래프에 입력
    input_message = {"messages": [("user", request.question)]}
    
    # 🚀 그래프 실행 시 config를 반드시 같이 넘겨주어야 합니다!
    # ainvoke 또는 astream 등 사용하시는 메서드에 맞게 config=config 를 추가해 주세요.
    result = await app.ainvoke(input_message, config=config)
    try:
        print(f"\n🚀 [API 요청 수신] 질문: {request.question}")
        initial_state = {
            "question": request.question,
            "retry_count": 0
        }
        
        # LangGraph 워크플로우 실행
        result = graph_app.invoke(initial_state)
        
        # Spring Boot 등으로 보낼 최종 응답 생성
        return ChatResponse(
            answer=result.get("generation", "답변을 생성하지 못했습니다."),
            final_query=result.get("question", request.question),
            retry_count=result.get("retry_count", 0)
        )
    except Exception as e:
        print(f"❌ [에러 발생] {str(e)}")
        raise HTTPException(status_code=500, detail="AI 에이전트 처리 중 오류가 발생했습니다.")

# 서버 실행 (터미널에서 직접 실행 시)
if __name__ == "__main__":
    # Spring Boot(8080)와 포트 충돌을 피하기 위해 8000번 포트 사용
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


from neo4j import GraphDatabase

# Neo4j 드라이버 세팅
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

try:
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    print("✅ Neo4j DB 연결 성공!")
except Exception as e:
    print(f"❌ Neo4j 연결 실패: {e}")
