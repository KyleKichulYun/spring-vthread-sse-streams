package com.kylelab.sseagent.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.atomic.AtomicInteger;

import io.micrometer.core.instrument.Gauge;
import io.micrometer.core.instrument.MeterRegistry;

@Service
public class SseConnectionService {

    private static final Logger log = LoggerFactory.getLogger(SseConnectionService.class);

    private final List<SseEmitter> emitters = new CopyOnWriteArrayList<>();
    private final AtomicInteger connectionCount = new AtomicInteger(0);
    private static final int MAX_CONNECTIONS = 10000;

    public SseConnectionService(MeterRegistry meterRegistry) {
        Gauge.builder("sse.connections.active", connectionCount, AtomicInteger::get)
                .description("현재 활성 SSE 연결 수")
                .register(meterRegistry);
    }

    public SseEmitter createConnection() {
        if (connectionCount.incrementAndGet() > MAX_CONNECTIONS) {
            connectionCount.decrementAndGet();
            throw new IllegalStateException("최대 연결 수 초과");
        }

        SseEmitter emitter = new SseEmitter(600_000L);
        emitters.add(emitter);

        Runnable cleanup = () -> {
            if (emitters.remove(emitter)) {
                connectionCount.decrementAndGet();
            }
        };

        emitter.onCompletion(cleanup);
        emitter.onTimeout(cleanup);
        emitter.onError((e) -> cleanup.run());

        try {
            emitter.send(SseEmitter.event().name("connect").data("connected!"));
            log.info("🔌 [SSE] 접속 완료. 현재 연결 수: {}", connectionCount.get());
        } catch (IOException e) {
            log.debug("🔌 [SSE] 접속 직후 연결 끊김.");
            cleanup.run(); // 명시적 정리
        }

        return emitter;
    }

    public void broadcast(String jsonData) {
        log.info("📡 [SSE 브로드캐스트] {} 명의 클라이언트 전송 시작", connectionCount.get());

        for (SseEmitter emitter : emitters) {
            try {
                emitter.send(SseEmitter.event().name("ai-response").data(jsonData));
            } catch (IOException e) {
                // [개선] completeWithError를 호출하면 이미 죽은 소켓에
                // 상태 변경을 시도하다 IllegalStateException이 발생할 수 있음.
                // 따라서 직접 cleanup 로직을 호출하여 리스트에서 즉시 제거만 수행함.
                log.debug("📡 [SSE] 클라이언트 연결 유실(Broken Pipe). 명부 제외.");

                // onError 콜백이 나중에 호출되길 기다릴 필요 없이 즉시 제거
                if (emitters.remove(emitter)) {
                    connectionCount.decrementAndGet();
                }
            }
        }
    }
}