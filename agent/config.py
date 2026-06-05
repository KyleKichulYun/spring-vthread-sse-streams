import os
import warnings
import logging
from neo4j import GraphDatabase, exceptions as neo4j_exceptions
from langchain_openai import ChatOpenAI

warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# ==========================================
# 💡 로깅(Logging) 전역 설정
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


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
    logger.info("✅ [Config] Neo4j DB 연결 성공!")
except neo4j_exceptions.AuthError:
    logger.error("❌ [Config] Neo4j 인증 실패: Username 또는 Password를 확인하세요.")
except neo4j_exceptions.ServiceUnavailable:
    logger.error("❌ [Config] Neo4j 서버에 연결할 수 없습니다. 인프라가 구동 중인지 확인하세요.")
except Exception as e:
    logger.error(f"❌ [Config] Neo4j 연결 중 알 수 없는 예외 발생: {e}")

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

def close_db():
    """애플리케이션 종료 시 Neo4j 커넥션을 안전하게 닫습니다."""
    if neo4j_driver is not None:
        neo4j_driver.close()
        logger.info("🛑 [Config] Neo4j 커넥션이 안전하게 종료되었습니다.")