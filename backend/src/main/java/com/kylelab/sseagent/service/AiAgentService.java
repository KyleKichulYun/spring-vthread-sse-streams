package com.kylelab.sseagent.service;

import com.kylelab.sseagent.dto.request.ChatMessageRequest;
import com.kylelab.sseagent.dto.response.AiAgentResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

@Service
public class AiAgentService {

    private static final Logger log = LoggerFactory.getLogger(AiAgentService.class);
    private final RestClient aiAgentRestClient;

    public AiAgentService(RestClient aiAgentRestClient) {
        this.aiAgentRestClient = aiAgentRestClient;
    }

    /**
     * Python AI 에이전트에게 질문을 던지고 답변을 받아옵니다.
     */
    public AiAgentResponse askAgent(String question) {
        log.info("🤖 AI 에이전트에게 질문 전송 중... [질문: {}]", question);

        try {
            ChatMessageRequest request = new ChatMessageRequest(question);

            // 🚀 가상 스레드 매직: 이 HTTP 요청이 끝날 때까지 기다리는 동안
            // 톰캣 스레드가 멈추지 않고 다른 사용자의 요청을 처리하러 떠납니다!
            AiAgentResponse response = aiAgentRestClient.post()
                    .body(request)
                    .retrieve()
                    .body(AiAgentResponse.class);

            if (response != null) {
                log.info("✅ AI 응답 수신 완료! [수정된 검색어: {}, 재시도: {}]",
                        response.final_query(), response.retry_count());
            }

            return response;

        } catch (RestClientException e) {
            log.error("❌ AI 에이전트 통신 실패: {}", e.getMessage());
            throw new RuntimeException("AI 에이전트 서버와 통신할 수 없습니다.", e);
        }
    }
}