import { useEffect, useState } from 'react';

export const useSSE = (url: string) => {
  const [data, setData] = useState<any>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const eventSource = new EventSource(url);

    // 🚀 연결이 성공했을 때
    eventSource.onopen = () => {
      setIsConnected(true);
      setError(null);
    };

    // 데이터 수신 시
    eventSource.addEventListener('ai-response', (event) => {
      const parsedData = JSON.parse(event.data);
      setData(parsedData);
    });

    // ❌ 에러 또는 연결 끊김 발생 시
    eventSource.onerror = (err) => {
      console.error("SSE Connection Error:", err);
      setIsConnected(false);
      setError("서버와의 실시간 연결이 끊어졌습니다. 재연결을 시도합니다...");
      // EventSource는 기본적으로 자동 재연결을 시도합니다.
    };

    return () => {
      eventSource.close();
    };
  }, [url]);

  return { data, isConnected, error };
};