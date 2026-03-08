import os
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
from dotenv import load_dotenv
from typing import TypedDict, List
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END

# 1. 환경 변수 로드 (.env 파일에서 OPENAI_API_KEY 자동 인식)
load_dotenv()

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
    # (일단 테스트용 가짜 문서 주입)
    print(f"\n[검색] 검색어: '{state['question']}'")
    # 일부러 환각을 유도하기 위해 문서에는 '한도' 금액을 적지 않았습니다.
    mock_docs = ["2024년 복지 가이드: 올해 체력단련비 지원 제도가 신설되었습니다. 구체적인 한도는 인사팀에 문의하세요."]
    return {"documents": mock_docs, "retry_count": state.get("retry_count", 0)}

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
        """),
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

    print(f"🔄 새 검색어 적용: '{result.improved_query}'")
    print(f"💡 변경 이유: {result.reasoning}")

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

app = workflow.compile()

# ==========================================
# 실행 테스트
# ==========================================
if __name__ == "__main__":
    initial_state = {
        "question": "올해 체력단련비 지원 한도가 얼마야?",
        "retry_count": 0
    }
    app.invoke(initial_state)