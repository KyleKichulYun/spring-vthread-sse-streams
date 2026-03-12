package com.kylelab.sseagent.dto.request;

public record ChatMessageRequest(
        String question,
        // 🚀 추가: 프론트엔드에서 생성해서 보내줄 대화방 ID (없으면 기본값)
        String threadId
) {
    public ChatMessageRequest {
        if (threadId == null || threadId.isBlank()) {
            threadId = "default-session";
        }
    }
}