import { useEffect, useState } from 'react';

export const useSSE = (url: string) => {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    // 🚀 백엔드의 SSE 엔드포인트와 연결
    const eventSource = new EventSource(url);

    // 백엔드에서 .name("ai-response")로 보낸 이벤트를 수신
    eventSource.addEventListener('ai-response', (event) => {
      const parsedData = JSON.parse(event.data);
      setData(parsedData);
    });

    eventSource.onerror = (err) => {
      console.error("SSE Connection Error:", err);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [url]);

  return data;
};