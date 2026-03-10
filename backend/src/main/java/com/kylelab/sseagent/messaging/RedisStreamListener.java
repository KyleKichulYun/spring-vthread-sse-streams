package com.kylelab.sseagent.messaging;

import com.kylelab.sseagent.service.SseConnectionService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.stream.StreamListener;
import org.springframework.stereotype.Component;

@Component
public class RedisStreamListener implements StreamListener<String, MapRecord<String, String, String>> {

    private static final Logger log = LoggerFactory.getLogger(RedisStreamListener.class);
    private final SseConnectionService sseConnectionService;

    public RedisStreamListener(SseConnectionService sseConnectionService) {
        this.sseConnectionService = sseConnectionService;
    }

    @Override
    public void onMessage(MapRecord<String, String, String> message) {
        // 우리가 아까 'payload'라는 키로 JSON을 넣었죠! 그걸 꺼냅니다.
        String payload = message.getValue().get("payload");
        log.info("📥 [Redis Subscribe] 스트림에서 메시지 수신 완료: {}", payload);

        // SSE로 접속 중인 모든 클라이언트에게 쏩니다!
        sseConnectionService.broadcast(payload);
    }
}