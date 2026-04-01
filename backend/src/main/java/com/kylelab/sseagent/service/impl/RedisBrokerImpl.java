package com.kylelab.sseagent.service.impl;

import com.kylelab.sseagent.dto.request.ChatMessageRequest;
import com.kylelab.sseagent.service.MessageBrokerService;
import com.kylelab.sseagent.service.SseSessionManager;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
@ConditionalOnProperty(name = "app.broker.type", havingValue = "redis")
public class RedisBrokerImpl implements MessageBrokerService {

    // 💡 롬복이 생성자를 통해 안전하게 주입해 줍니다.
    private final RedisTemplate<String, Object> redisTemplate;
    private final SseSessionManager sseSessionManager;

    @Override
    public void sendQuestion(ChatMessageRequest request) {
        // 🚀 1. redisTemplate 사용 (첫 번째 경고 해결!)
        // 기존에 사용하시던 Redis Streams 에 맞게 데이터를 Map 형태로 변환하여 발송합니다.
        Map<String, Object> streamData = Map.of(
                "threadId", request.threadId(),
                "question", request.question()
        );

        redisTemplate.opsForStream().add("question-stream", streamData);
        log.info("🔴 [Redis 발송 완료] question-stream -> {}", request.question());
    }

    // 🚀 2. sseSessionManager 사용 (두 번째 경고 해결!)
    // (참고) 이 메서드는 대장님이 기존에 구현해두신 Redis Stream Listener 쪽에서
    // AI의 답변 데이터를 수신했을 때 호출해주시면 됩니다.
    @SuppressWarnings("unused")
    public void broadcastAnswerToClient(Map<String, Object> responseData) {
        String threadId = (String) responseData.get("threadId");
        Boolean isDone = (Boolean) responseData.getOrDefault("isDone", false);

        log.info("🔴 [Redis 수신 완료] 프론트엔드로 SSE 전송 중... (Thread: {})", threadId);

        // SseSessionManager를 사용하여 해당 클라이언트에게만 1:1로 답변을 쏴줍니다.
        sseSessionManager.sendToClient(threadId, responseData, isDone);
    }
}