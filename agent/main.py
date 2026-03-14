import os
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# 🚀 추가: dotenv를 임포트하고 바로 실행하여 환경변수를 로드합니다!
from dotenv import load_dotenv
load_dotenv()

from typing import TypedDict, List, Annotated
import operator
from pydantic import BaseModel, Field

# --- FastAPI 관련 패키지 ---
from fastapi import FastAPI, HTTPException
import uvicorn

# --- LangChain & LangGraph ---
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages # 🚀 핵심: 메시지를 누적하는 함수
from langgraph.checkpoint.memory import MemorySaver

# --- Neo4j ---
from neo4j import GraphDatabase

# ==========================================
# 0. 초기 셋업 (DB & LLM)
# ==========================================
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

try:
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    print("✅ Neo4j DB 연결 성공!")
except Exception as e:
    print(f"❌ Neo4j 연결 실패: {e}")

llm = ChatOpenAI(model="gpt-4o", temperature=0)

# ==========================================
# 1. 상태(State) 정의
# ==========================================
class AgentState(TypedDict):
    # 🚀 핵심: messages 필드는 add_messages 리듀서를 통해 계속 누적(Append)됩니다.
    messages: Annotated[list[BaseMessage], add_messages]
    
    question: str # 사용자의 원래 질문 (고정)
    
    # 🚀 추가: 메타인지를 위한 검색어 추적 장치
    search_query: str # 현재 DB 검색에 사용할 쿼리
    past_queries: Annotated[list[str], operator.add] # 시도했던 검색어 히스토리 누적
    
    documents: List[str]
    generation: str
    feedback: str
    retry_count: int

# ==========================================
# 2. 구조화된 출력 모델 (Pydantic)
# ==========================================
class GradeOutput(BaseModel):
    score: str = Field(description="평가 결과. 'Pass' 또는 'Fail'만 입력")
    reason: str = Field(description="왜 이런 평가를 내렸는지 논리적인 이유 1~2문장")

class RewriteOutput(BaseModel):
    improved_query: str = Field(description="원래 질문을 더 구체적이고 명확하게 개선한 검색어")
    reasoning: str = Field(description="왜 이렇게 검색어를 개선했는지 간단한 설명")

# ==========================================
# 3. 노드(Node) 구현
# ==========================================
def retrieve_node(state: AgentState):
    # 🚀 수정: 메타인지가 수정한 'search_query'를 우선 사용 (없으면 원래 질문 사용)
    current_query = state.get("search_query") or state["question"]
    print(f"\n[DB 검색] 검색어: '{current_query}' (원래 질문: '{state['question']}')")

    # 검색어를 띄어쓰기 기준으로 분리하여 핵심 키워드만 추출
    keywords = current_query.split()
    
    # 🚀 핵심: 노드 자체의 내용뿐만 아니라, 연결된(Relationship) 이웃 노드의 정보까지 끌어옵니다!
    cypher_query = """
    // 1. 키워드를 포함하는 핵심 노드(n) 찾기
    MATCH (n)
    WHERE any(keyword IN $keywords WHERE n.name CONTAINS keyword OR n.title CONTAINS keyword OR n.content CONTAINS keyword)
    
    // 2. 핵심 노드와 1-hop(직접 연결) 거리에 있는 이웃 노드(m) 탐색
    OPTIONAL MATCH (n)-[r]-(m)
    
    // 3. 🚀 수정: 메인 노드의 내용뿐만 아니라 연결된(m) 노드의 상세 내용까지 완벽하게 조합
    WITH n, r, m
    RETURN 
      "[" + coalesce(n.name, n.title, '이름없음') + "] " + coalesce(n.content, n.description, '') + 
      CASE WHEN m IS NOT NULL THEN 
        " ➡️ (추가 관련 정보: " + coalesce(m.name, m.title, '') + " - " + coalesce(m.content, m.description, '') + ")"
      ELSE "" END AS context
    LIMIT 10
    """

    documents = []
    try:
        with neo4j_driver.session() as session:
            result = session.run(cypher_query, keywords=keywords)
            # 쿼리 결과를 문자열 리스트로 변환
            documents = [record["context"] for record in result if record["context"]]
    except Exception as e:
        print(f"DB 검색 중 에러: {e}")

    if not documents:
        print("⚠️ 관련 문서가 검색되지 않았습니다.")
        documents = ["관련 문서가 검색되지 않았습니다. 질문을 더 구체적으로 수정해보세요."]
    else:
        print(f"✅ {len(documents)}개의 관련 문서 검색 완료.")

    return {
        "search_query": current_query,
        "documents": documents, 
        "past_queries": [current_query], # 🚀 추가: 시도한 검색어를 리듀서(operator.add)로 누적
        "retry_count": state.get("retry_count", 0)
    }

def generate_node(state: AgentState):
    print("\n[생성] 답변 초안 작성 중...")

    # 🚀 핵심: LLM에게 이전 대화 기록(messages)을 통째로 넘겨주어 문맥을 유지합니다.
    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 제공된 문서(Context)와 이전 대화 기록을 바탕으로 사용자의 질문에 답하는 유능한 어시스턴트입니다.\n\n문서: {context}"),
        # 이전 대화 내용들이 여기에 삽입됩니다 (랭체인이 자동 처리)
        ("placeholder", "{messages}")
    ])

    chain = prompt | llm | StrOutputParser()
    context_str = "\n".join(state["documents"])

    # 실행 시 누적된 messages 전체를 전달
    generation = chain.invoke({"context": context_str, "messages": state["messages"]})
    print(f"💡 답변 초안: {generation}")

    # 최종 답변을 messages 배열에 AIMessage 형태로 추가하여 반환
    return {"generation": generation, "messages": [AIMessage(content=generation)]}

def evaluate_node(state: AgentState):
    print("\n[평가] 환각 여부 및 품질 검증 중...")

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 사실 관계를 검증하는 깐깐한 감사관입니다.
        '생성된 답변'이 오직 '제공된 문서'에만 기반했는지 확인하세요.
        문서에 없는 내용을 지어냈다면 무조건 'Fail'을 부여하세요.
        평가 기준:
        1) 문서에 명시된 정보만 사용했는가? (Pass/Fail)
        2) 평가 이유 (1~2문장)"""),
        ("user", "제공된 문서: {context}\n\n생성된 답변: {generation}")
    ])

    structured_llm = llm.with_structured_output(GradeOutput)
    chain = prompt | structured_llm

    context_str = "\n".join(state["documents"])
    result = chain.invoke({"context": context_str, "generation": state["generation"]})

    feedback_str = f"{result.score}: {result.reason}"
    print(f"⚖️ 평가 결과: {feedback_str}")

    return {"feedback": feedback_str}

def rewrite_query_node(state: AgentState):
    print("\n[재작성] 평가 실패. 메타인지 분석 및 검색어 수정 중...")

    # 🚀 수정: 과거 실패 기록과 구체적인 지시사항을 포함한 프롬프트
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 AI 에이전트의 검색 성능을 극대화하는 '전문 검색 전략가'입니다.
        사용자의 원래 질문에 답하기 위해 DB를 검색했지만 실패했습니다.
        
        [반드시 지켜야 할 규칙]
        1. 이전 평가 피드백을 분석하여 무엇이 부족했는지 파악하세요.
        2. '시도했던 검색어'와 겹치지 않는 완전히 새로운 유의어나 더 포괄적인 단어를 선택하세요.
        3. 문장 형태가 아닌, **띄어쓰기로만 구분된 2~3개의 핵심 명사 키워드**만 출력하세요. (예: "복지포인트 규정 금액")"""),
        ("user", "원래 질문: {question}\n시도했던 검색어들: {past_queries}\n이전 평가 피드백: {feedback}")
    ])
    
    structured_llm = llm.with_structured_output(RewriteOutput)
    chain = prompt | structured_llm

    # 누적된 과거 검색어 배열을 보기 좋은 문자열로 변환
    past_queries_str = ", ".join(state.get("past_queries", []))
    
    result = chain.invoke({
        "question": state['question'], 
        "past_queries": past_queries_str,
        "feedback": state["feedback"]
    })
    
    print(f"🔄 새 키워드 도출: '{result.improved_query}'\n💡 반성 및 변경 이유: {result.reasoning}")
    
    # 🚀 원래 질문(question)은 놔두고, 검색어(search_query)만 업데이트합니다.
    return {"search_query": result.improved_query, "retry_count": state["retry_count"] + 1}

# ==========================================
# 4. 라우팅 및 그래프 조립
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

# 🚀 2. 컴파일 할 때 checkpointer로 메모리를 넘겨줍니다! (이름을 graph_app으로 통일)
graph_app = workflow.compile(checkpointer=memory)


# ==========================================
# 5. FastAPI 서버 설정 및 API 엔드포인트
# ==========================================
app = FastAPI(title="LangGraph Meta-Cognition API", version="1.0")

class ChatRequest(BaseModel):
    question: str = Field(..., example="올해 체력단련비 지원 한도가 얼마야?")
    # 🚀 클라이언트가 스레드 ID를 주지 않으면 기본값으로 새 세션을 만듭니다.
    thread_id: str = "default-session"    

class ChatResponse(BaseModel):
    answer: str
    final_query: str
    retry_count: int

# ==========================================
# 5. FastAPI 서버 설정 및 API 엔드포인트
# ==========================================
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        print(f"\n🚀 [API 요청 수신] 질문: {request.question} (Thread: {request.thread_id})")
        
        config = {"configurable": {"thread_id": request.thread_id}}
        
        # 🚀 수정: 최초 상태에 search_query를 질문과 동일하게 추가
        input_state = {
            "messages": [HumanMessage(content=request.question)],
            "question": request.question, 
            "search_query": request.question, # 첫 검색은 질문 그대로 시도
            "retry_count": 0
        }
        
        result = await graph_app.ainvoke(input_state, config=config)
        
        final_answer = result.get("generation", "답변을 생성하지 못했습니다.")
        
        return ChatResponse(
            answer=final_answer,
            final_query=result.get("search_query", request.question), # 최종 검색어로 응답
            retry_count=result.get("retry_count", 0)
        )
    except Exception as e:
        print(f"❌ [에러 발생] {str(e)}")
        raise HTTPException(status_code=500, detail="AI 에이전트 처리 중 오류가 발생했습니다.")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)