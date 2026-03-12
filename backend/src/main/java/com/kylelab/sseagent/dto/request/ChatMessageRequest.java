package com.kylelab.sseagent.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;

public record ChatMessageRequest(
        String question,

        // 🚀 자바에서는 threadId로 쓰지만, JSON으로 바꿀 땐 "thread_id"로 바꿔라!
        @JsonProperty("thread_id")
        String threadId
) {
    public ChatMessageRequest {
        if (threadId == null || threadId.isBlank()) {
            threadId = "default-session";
        }
    }
}