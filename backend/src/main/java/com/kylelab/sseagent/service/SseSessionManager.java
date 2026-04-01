package com.kylelab.sseagent.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Slf4j
@Component
public class SseSessionManager {

    private final Map<String, SseEmitter> emitters = new ConcurrentHashMap<>();

    public SseEmitter subscribe(String threadId) {
        SseEmitter emitter = new SseEmitter(60 * 1000L);
        emitters.put(threadId, emitter);

        emitter.onCompletion(() -> emitters.remove(threadId));
        emitter.onTimeout(() -> emitters.remove(threadId));
        emitter.onError((e) -> emitters.remove(threadId));

        try {
            emitter.send(SseEmitter.event().name("connect").data("connected!"));
        } catch (IOException e) {
            emitters.remove(threadId);
        }
        return emitter;
    }

    // 브로커(Rabbit/Redis)가 AI 답변을 받았을 때 호출할 메서드
    public void sendToClient(String threadId, Object data, boolean isDone) {
        SseEmitter emitter = emitters.get(threadId);
        if (emitter != null) {
            try {
                emitter.send(SseEmitter.event().name("message").data(data));
                if (isDone) {
                    emitter.complete();
                    emitters.remove(threadId);
                }
            } catch (IOException e) {
                emitters.remove(threadId);
            }
        }
    }
}