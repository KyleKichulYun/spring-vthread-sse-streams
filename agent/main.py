import os
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# 🚀 dotenv 로드
# from dotenv import load_dotenv
# load_dotenv()

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
from langgraph.graph.message import add_messages
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
    messages: Annotated[list[BaseMessage], add_messages]
    question: str 
    search_query: str 
    past_queries: Annotated[list[str], operator.add] 
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
    current_query = state.get("search_query") or state["question"]
    print(f"\n[DB 검색] 검색어: '{current_query}' (원래 질문: '{state['question']}')")

    keywords = current_query.split()
    
    # 🚀 어제(KYL-56) 완성한 가장 완벽한 Graph RAG Cypher 쿼리!
    cypher_query = """
    MATCH (n)
    WHERE any(keyword IN $keywords WHERE n.name CONTAINS keyword OR n.title CONTAINS keyword OR n.content CONTAINS keyword)
    OPTIONAL MATCH (n)-[r]-(m)
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
            documents = [record["context"] for record in result if record["context"]]
    except Exception as e:
        print(f"DB 검색 중 에러: {e}")

    if not documents:
        print("⚠️ 관련 문서가 검색되지 않았습니다.")
        documents = ["관련 문서가 검색되지 않았습니다. 질문을 더 구체적으로 수정해보세요."]
    else:
        print(f"✅ {len(documents)}개의 그래프 문맥(Context) 검색 완료.")

    return {
        "search_query": current_query,
        "documents": documents, 
        "past_queries": [current_query], 
        "retry_count": state.get("retry_count", 0)
    }

def generate_node(state: AgentState):
    print("\n[생성] 답변 초안 작성 중...")

    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 제공된 문서(Context)와 이전 대화 기록을 바탕으로 사용자의 질문에 답하는 유능한 어시스턴트입니다.\n\n문서: {context}"),
        ("placeholder", "{messages}")
    ])

    chain = prompt | llm | StrOutputParser()
    context_str = "\n".join(state["documents"])

    generation = chain.invoke({"context": context_str, "messages": state["messages"]})
    print(f"💡 답변 초안: {generation}")

    return {"generation": generation, "messages": [AIMessage(content=generation)]}

def evaluate_node(state: AgentState):
    print("\n[평가] 환각 여부 및 질문 해결 완벽성 검증 중...")

    # 🚀 오늘(KYL-57) 업그레이드한 이중 검증 프롬프트!
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 깐깐한 AI 품질 검증관(QA)입니다.
        생성된 답변이 다음 두 가지 기준을 모두 완벽히 통과하는지 엄격하게 평가하세요.

        [평가 기준]
        1. 사실성(Factuality): '생성된 답변'이 오직 '제공된 문서'에만 기반했는가? (문서에 없는 내용을 조금이라도 지어냈다면 무조건 Fail)
        2. 관련성(Relevance): '생성된 답변'이 사용자의 '원래 질문'에 대한 답을 명확하고 완벽하게 제공했는가? (동문서답이거나 정보가 부족하면 Fail)

        위 두 기준을 모두 만족해야만 'Pass'를 부여하고, 하나라도 부족하면 'Fail'을 부여하세요."""),
        ("user", "원래 질문: {question}\n\n제공된 문서: {context}\n\n생성된 답변: {generation}")
    ])

    structured_llm = llm.with_structured_output(GradeOutput)
    chain = prompt | structured_llm

    context_str = "\n".join(state["documents"])
    
    result = chain.invoke({
        "question": state["question"], 
        "context": context_str, 
        "generation": state["generation"]
    })

    feedback_str = f"{result.score}: {result.reason}"
    print(f"⚖️ 평가 결과: {feedback_str}")

    return {"feedback": feedback_str}

def rewrite_query_node(state: AgentState):
    print("\n[재작성] 평가 실패. 메타인지 분석 및 검색어 수정 중...")

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

    past_queries_str = ", ".join(state.get("past_queries", []))
    
    result = chain.invoke({
        "question": state['question'], 
        "past_queries": past_queries_str,
        "feedback": state["feedback"]
    })
    
    print(f"🔄 새 키워드 도출: '{result.improved_query}'\n💡 반성 및 변경 이유: {result.reasoning}")
    
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

memory = MemorySaver()
graph_app = workflow.compile(checkpointer=memory)


# ==========================================
# 5. FastAPI 서버 설정 및 API 엔드포인트
# ==========================================
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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)