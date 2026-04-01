package com.kylelab.sseagent.service;

import com.kylelab.sseagent.dto.request.ChatMessageRequest;

public interface MessageBrokerService {
    // 프론트엔드에서 온 질문을 큐/스트림으로 발행(Publish)하는 기능
    void sendQuestion(ChatMessageRequest request);
}