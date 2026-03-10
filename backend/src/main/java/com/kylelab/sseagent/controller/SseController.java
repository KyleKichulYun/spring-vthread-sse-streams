package com.kylelab.sseagent.controller;

import com.kylelab.sseagent.service.SseConnectionService;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@RestController
@RequestMapping("/api/stream")
public class SseController {

    private final SseConnectionService sseConnectionService;

    public SseController(SseConnectionService sseConnectionService) {
        this.sseConnectionService = sseConnectionService;
    }

    // 🚀 [핵심] 반환 타입이 SseEmitter이고, produces가 TEXT_EVENT_STREAM_VALUE 이어야 합니다.
    @GetMapping(produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter subscribe() {
        return sseConnectionService.createConnection();
    }
}