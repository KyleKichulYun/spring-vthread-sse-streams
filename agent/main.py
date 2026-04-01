import os
import json
import pika
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# ... (중략) ...
# [0번 초기 셋업] ~ [4번 라우팅 및 그래프 조립] 까지는 대장님의 기존 코드와 100% 동일하게 유지합니다!
# ... (중략) ...

# ==========================================
# 5. RabbitMQ 워커(Worker) 설정 및 실행
# ==========================================

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "kyle")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "password")

def process_question(ch, method, properties, body):
    """
    RabbitMQ의 'question.queue'에 메시지가 들어오면 자동으로 실행되는 워커 함수
    """
    data = json.loads(body.decode('utf-8'))
    thread_id = data.get("threadId", "default-session")
    question = data.get("question", "")

    print(f"\n==================================================")
    print(f"📩 [작업 수신] Thread: {thread_id}")
    print(f"❓ [질문 내용] {question}")
    print(f"==================================================")

    try:
        # 1. LangGraph 메타인지 에이전트 실행 (비동기 대신 동기 invoke 사용)
        config = {"configurable": {"thread_id": thread_id}}
        input_state = {
            "messages": [HumanMessage(content=question)],
            "question": question,
            "search_query": question,
            "retry_count": 0
        }

        # Pika의 BlockingConnection 안에서는 동기(invoke)로 돌리는 것이 안전합니다.
        result = graph_app.invoke(input_state, config=config)

        final_answer = result.get("generation", "답변을 생성하지 못했습니다.")
        final_query = result.get("search_query", question)
        retry_count = result.get("retry_count", 0)

        # 2. Spring Boot(answer.queue)로 보낼 최종 응답 데이터 구성
        response_data = {
            "threadId": thread_id,
            "answer": final_answer,
            "isDone": True, # 프론트엔드 연결 종료를 위한 플래그
            "metadata": {
                "query": final_query,
                "retries": retry_count
            }
        }

        # 3. answer.queue로 Publish!
        ch.basic_publish(
            exchange='',
            routing_key='answer.queue',
            body=json.dumps(response_data, ensure_ascii=False)
        )
        print(f"\n📤 [답변 발송 완료] Spring Boot로 전송했습니다. (Thread: {thread_id})")

    except Exception as e:
        print(f"\n❌ [에러 발생] AI 처리 중 오류: {str(e)}")
        # 에러가 나더라도 프론트엔드가 무한 대기하지 않도록 에러 메시지를 쏴줍니다.
        error_data = {
            "threadId": thread_id,
            "answer": "죄송합니다. 시스템 오류로 인해 답변을 생성하지 못했습니다.",
            "isDone": True
        }
        ch.basic_publish(exchange='', routing_key='answer.queue', body=json.dumps(error_data, ensure_ascii=False))

    finally:
        # 4. RabbitMQ에 "이 작업 성공적으로 끝냈어!" 라고 보고 (ACK)
        ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    """
    RabbitMQ와 연결하고 큐를 모니터링하는 메인 루프
    """
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)

    try:
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # 큐가 없으면 생성 (Spring Boot 쪽과 동일한 설정)
        channel.queue_declare(queue='question.queue', durable=True)
        channel.queue_declare(queue='answer.queue', durable=True)

        # 파이썬 워커가 한 번에 하나의 메시지만 처리하도록 설정 (Fair Dispatch)
        channel.basic_qos(prefetch_count=1)

        # question.queue를 구독
        channel.basic_consume(queue='question.queue', on_message_callback=process_question)

        print("\n==================================================")
        print("🐰 [*] 파이썬 메타인지 AI 워커 가동 완료!")
        print("🎧 'question.queue' 대기 중... (종료하려면 CTRL+C)")
        print("==================================================\n")

        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError:
        print("❌ [연결 실패] RabbitMQ 서버(Docker)가 켜져 있는지 확인해 주세요!")
    except KeyboardInterrupt:
        print("\n🛑 워커를 종료합니다.")
        if 'connection' in locals() and connection.is_open:
            connection.close()

if __name__ == '__main__':
    main()