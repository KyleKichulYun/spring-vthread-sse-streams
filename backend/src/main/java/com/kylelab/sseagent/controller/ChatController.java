package com.kylelab.sseagent.controller;

import com.kylelab.sseagent.dto.request.ChatMessageRequest;
import com.kylelab.sseagent.dto.response.AiAgentResponse;
import com.kylelab.sseagent.service.AiAgentService;
import com.kylelab.sseagent.service.RedisPublisherService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/chat")
public class ChatController {

    private static final Logger log = LoggerFactory.getLogger(ChatController.class);

    private final AiAgentService aiAgentService;
    private final RedisPublisherService redisPublisherService;

    // 생성자 주입
    public ChatController(AiAgentService aiAgentService, RedisPublisherService redisPublisherService) {
        this.aiAgentService = aiAgentService;
        this.redisPublisherService = redisPublisherService;
    }

    @PostMapping
    public ResponseEntity<String> askQuestion(@RequestBody ChatMessageRequest request) {
        log.info("📩 [API 요청 수신] 질문: {}, 세션: {}", request.question(), request.threadId());

        // 1. AI 에이전트에게 질문하고 답변 받기 (Virtual Threads로 논블로킹 동작)
        // 🚀 수정: request에서 threadId를 꺼내서 같이 넘겨줍니다.
        AiAgentResponse response = aiAgentService.askAgent(request.question(), request.threadId());

        // 2. 받은 답변을 Redis Streams 채널에 브로드캐스팅(Publish)
        redisPublisherService.publishAiResponse(response);

        log.info("📤 [API 처리 완료] 질문 접수 및 브로드캐스팅 성공");

        // SSE로 결과가 날아갈 것이므로, HTTP 요청 자체는 "접수 완료" 메시지만 짧게 끊어서 바로 반환합니다.
        return ResponseEntity.ok("질문이 성공적으로 접수되어 AI가 답변을 스트리밍합니다.");
    }
}