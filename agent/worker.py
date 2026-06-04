import json
import asyncio
import aio_pika
from langchain_core.messages import HumanMessage

# 🚀 분리한 모듈 임포트
from config import RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASS
from agent import graph_app

async def process_question(message: aio_pika.abc.AbstractIncomingMessage):
    """
    RabbitMQ의 'question.queue'에 메시지가 들어오면 비동기로 실행되는 워커 콜백 함수
    """
    # async with 블록을 사용하면 처리가 무사히 끝났을 때 자동으로 ACK를 전송합니다.
    async with message.process():
        body = message.body.decode('utf-8')
        data = json.loads(body)
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

            # 💡 [핵심] ainvoke를 사용하여 AI 처리를 비동기로 대기합니다!
            result = await graph_app.ainvoke(input_state, config=config)

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

            # 💡 [핵심] 메시지 발행(Publish)도 비동기로 처리합니다.
            await message.channel.default_exchange.publish(
                aio_pika.Message(body=json.dumps(response_data, ensure_ascii=False).encode('utf-8')),
                routing_key='answer.queue'
            )
            print(f"\n📤 [답변 발송 완료] Spring Boot로 전송했습니다. (Thread: {thread_id})")

        except Exception as e:
            print(f"\n❌ [에러 발생] AI 처리 중 오류: {str(e)}")
            error_data = {
                "threadId": thread_id,
                "answer": "죄송합니다. 시스템 오류로 인해 답변을 생성하지 못했습니다.",
                "isDone": True
            }
            await message.channel.default_exchange.publish(
                aio_pika.Message(body=json.dumps(error_data, ensure_ascii=False).encode('utf-8')),
                routing_key='answer.queue'
            )


async def main():
    """
    비동기 RabbitMQ 연결 및 큐 모니터링 메인 루프
    """
    amqp_url = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}/"

    try:
        # connect_robust를 사용하면 네트워크 단절 시 자동 재연결을 시도합니다.
        connection = await aio_pika.connect_robust(amqp_url)

        async with connection:
            channel = await connection.channel()

            # 💡 [핵심] 비동기 처리량이 높아졌으므로 prefetch_count를 늘려 한 번에 여러 메시지를 가져옵니다.
            await channel.set_qos(prefetch_count=5)

            # 큐 선언 (durable=True로 설정하여 메시지 유실 방지)
            queue = await channel.declare_queue('question.queue', durable=True)
            await channel.declare_queue('answer.queue', durable=True)

            print("\n==================================================")
            print("⚡ [*] 파이썬 '비동기(Async)' 메타인지 AI 워커 가동 완료!")
            print("🎧 'question.queue' 대기 중... (종료하려면 CTRL+C)")
            print("==================================================\n")

            # 메시지 소비 시작
            await queue.consume(process_question)

            # 워커가 종료되지 않고 계속 백그라운드에서 돌도록 무한 대기
            await asyncio.Future()

    except Exception as e:
        print(f"❌ [에러 발생] RabbitMQ 연결 또는 실행 중 오류: {e}")

if __name__ == '__main__':
    from config import close_db  # 추가된 함수 임포트
    try:
        # 비동기 이벤트 루프 실행
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 워커를 안전하게 종료합니다.")
    finally:
        # 💡 [핵심] 정상 종료든 에러 종료든 무조건 DB 커넥션을 닫고 나갑니다.
        close_db()