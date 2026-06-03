import json
import pika
from langchain_core.messages import HumanMessage

# 🚀 분리한 모듈 임포트
from config import RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASS
from agent import graph_app

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
        config = {"configurable": {"thread_id": thread_id}}
        input_state = {
            "messages": [HumanMessage(content=question)],
            "question": question,
            "search_query": question,
            "retry_count": 0
        }

        # agent 모듈에서 가져온 graph_app 동기 실행
        result = graph_app.invoke(input_state, config=config)

        final_answer = result.get("generation", "답변을 생성하지 못했습니다.")
        final_query = result.get("search_query", question)
        retry_count = result.get("retry_count", 0)

        response_data = {
            "threadId": thread_id,
            "answer": final_answer,
            "isDone": True,
            "metadata": {
                "query": final_query,
                "retries": retry_count
            }
        }

        ch.basic_publish(
            exchange='',
            routing_key='answer.queue',
            body=json.dumps(response_data, ensure_ascii=False)
        )
        print(f"\n📤 [답변 발송 완료] Spring Boot로 전송했습니다. (Thread: {thread_id})")

    except Exception as e:
        print(f"\n❌ [에러 발생] AI 처리 중 오류: {str(e)}")
        error_data = {
            "threadId": thread_id,
            "answer": "죄송합니다. 시스템 오류로 인해 답변을 생성하지 못했습니다.",
            "isDone": True
        }
        ch.basic_publish(exchange='', routing_key='answer.queue', body=json.dumps(error_data, ensure_ascii=False))

    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    """
    RabbitMQ와 연결하고 큐를 모니터링하는 메인 루프
    """
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)

    connection = None  # 💡 경고 해결: 할당 전 참조 방지를 위한 명시적 초기화

    try:
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        channel.queue_declare(queue='question.queue', durable=True)
        channel.queue_declare(queue='answer.queue', durable=True)
        channel.basic_qos(prefetch_count=1)

        channel.basic_consume(queue='question.queue', on_message_callback=process_question)

        print("\n==================================================")
        print("🐰 [*] 파이썬 메타인지 AI 워커 가동 완료!")
        print("🎧 'question.queue' 대기 중... (종료하려면 CTRL+C)")
        print("==================================================\n")

        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError:
        print("❌ [연결 실패] RabbitMQ 서버가 켜져 있는지 확인해 주세요!")
    except KeyboardInterrupt:
        print("\n🛑 워커를 종료합니다.")
        if 'connection' in locals() and connection.is_open:
            connection.close()

if __name__ == '__main__':
    main()