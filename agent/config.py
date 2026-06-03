import os
import warnings
from neo4j import GraphDatabase
from langchain_openai import ChatOpenAI

warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# 🚀 dotenv 로드 (필요시 주석 해제)
# from dotenv import load_dotenv
# load_dotenv()

# ==========================================
# Neo4j 설정
# ==========================================
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

try:
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    print("✅ [Config] Neo4j DB 연결 성공!")
except Exception as e:
    print(f"❌ [Config] Neo4j 연결 실패: {e}")

# ==========================================
# LLM 설정
# ==========================================
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# ==========================================
# RabbitMQ 설정
# ==========================================
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "kyle")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "password")