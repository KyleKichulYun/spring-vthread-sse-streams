package com.kylelab.sseagent.dto.response;

// 파이썬 FastAPI의 ChatResponse 구조와 완벽히 일치해야 합니다.
public record AiAgentResponse(
        String answer,
        String final_query,
        int retry_count
) {
}