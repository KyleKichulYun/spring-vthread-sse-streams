from typing import TypedDict, List, Annotated
import operator
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

# 🚀 config.py에서 공통 자원 임포트
from config import neo4j_driver, llm

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

    # Full-Text 검색을 위해 검색어들을 논리합(OR) 형태로 가공 (예: "복지 포인트" -> "복지 OR 포인트")
    keywords_str = " OR ".join(current_query.split())

    # 🚀 최적화된 Cypher 쿼리: Full-Text 인덱스 활용 및 가중치 정렬 (Score 기반)
    cypher_query = """
    CALL db.index.fulltext.queryNodes("search_index", $keywords) YIELD node, score
    OPTIONAL MATCH (node)-[r]-(m)
    WITH node, score, r, m
    ORDER BY score DESC
    RETURN 
      "[" + coalesce(node.name, node.title, '이름없음') + "] " + coalesce(node.content, node.description, '') + 
      CASE WHEN m IS NOT NULL THEN 
        " ➡️ (추가 관련 정보: " + coalesce(m.name, m.title, '') + " - " + coalesce(m.content, m.description, '') + ")"
      ELSE "" END AS context
    LIMIT 10
    """

    documents = []
    try:
        with neo4j_driver.session() as session:
            # 리스트 대신 가공된 문자열(keywords_str)을 파라미터로 넘깁니다.
            result = session.run(cypher_query, keywords=keywords_str)
            documents = [record["context"] for record in result if record["context"]]
    except Exception as e:
        print(f"❌ DB 검색 중 에러: {e}")

    if not documents:
        print("⚠️ 관련 문서가 검색되지 않았습니다.")
        documents = ["관련 문서가 검색되지 않았습니다. 질문을 더 구체적으로 수정해보세요."]
    else:
        print(f"✅ {len(documents)}개의 최적화된 문맥(Context) 검색 완료.")

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
# 외부(api, worker)에서 이 객체를 가져다 사용합니다.
graph_app = workflow.compile(checkpointer=memory)