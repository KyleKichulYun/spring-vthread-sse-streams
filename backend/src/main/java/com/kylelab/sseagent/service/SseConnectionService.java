package com.kylelab.sseagent.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

@Service
public class SseConnectionService {

    private static final Logger log = LoggerFactory.getLogger(SseConnectionService.class);

    // 🚀 동시성 문제가 발생하지 않도록 Thread-Safe 한 컬렉션 사용
    private final List<SseEmitter> emitters = new CopyOnWriteArrayList<>();

    /**
     * 새로운 클라이언트의 SSE 연결을 생성하고 명부에 등록합니다.
     */
    public SseEmitter createConnection() {
        // 타임아웃을 10분(600,000ms)으로 넉넉하게 설정
        SseEmitter emitter = new SseEmitter(600_000L);
        emitters.add(emitter);

        // 클라이언트가 연결을 끊거나 타임아웃/에러가 발생하면 명부에서 즉시 삭제
        emitter.onCompletion(() -> emitters.remove(emitter));
        emitter.onTimeout(() -> emitters.remove(emitter));
        emitter.onError((e) -> emitters.remove(emitter));

        try {
            // 연결 성공 시, 최초 접속 더미 이벤트를 하나 보내줍니다. (안 보내면 타임아웃 될 수 있음)
            emitter.send(SseEmitter.event().name("connect").data("connected!"));
            log.info("🔌 [SSE] 새로운 클라이언트 접속 완료. 현재 연결 수: {}", emitters.size());
        } catch (IOException e) {
            emitters.remove(emitter);
        }

        return emitter;
    }

    /**
     * 접속 중인 모든 클라이언트에게 JSON 데이터를 브로드캐스팅합니다.
     */
    public void broadcast(String jsonData) {
        log.info("📡 [SSE 브로드캐스트] {} 명의 클라이언트에게 데이터 전송 중...", emitters.size());
        for (SseEmitter emitter : emitters) {
            try {
                // 'ai-response' 라는 이벤트 이름으로 JSON 데이터를 쏩니다.
                emitter.send(SseEmitter.event().name("ai-response").data(jsonData));
            } catch (IOException e) {
                // 전송 실패 시 죽은 연결로 간주하고 삭제
                emitter.completeWithError(e);
                emitters.remove(emitter);
            }
        }
    }
}