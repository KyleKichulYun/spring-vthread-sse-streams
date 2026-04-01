package com.kylelab.sseagent.controller;

import com.kylelab.sseagent.dto.request.ChatMessageRequest;
import com.kylelab.sseagent.service.MessageBrokerService;
import com.kylelab.sseagent.service.SseSessionManager;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@Slf4j
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class ChatController {

    private final SseSessionManager sseSessionManager;
    private final MessageBrokerService messageBrokerService; // 🚀 다형성의 마법!

    @GetMapping("/stream")
    public SseEmitter stream(@RequestParam String threadId) {
        log.info("🔌 [SSE 연결 요청] 세션: {}", threadId);
        return sseSessionManager.subscribe(threadId);
    }

    @PostMapping("/chat")
    public ResponseEntity<String> askQuestion(@RequestBody ChatMessageRequest request) {
        log.info("📩 [API 요청 수신] 질문: {}, 세션: {}", request.question(), request.threadId());

        // application.yml 설정에 따라 RabbitMQ 또는 Redis로 알아서 날아갑니다.
        messageBrokerService.sendQuestion(request);

        return ResponseEntity.ok("질문이 성공적으로 브로커에 접수되었습니다.");
    }
}