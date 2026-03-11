'use client';

import { useState, useRef, useEffect } from 'react';
import { useSSE } from '@/hooks/useSSE';
import { Send, Bot, User, Sparkles } from 'lucide-react';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  metadata?: {
    query: string;
    retries: number;
  };
}

export default function ChatPage() {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  
  // SSE 실시간 데이터 수신
  const latestAiResponse = useSSE('http://localhost:8080/api/stream');

  // AI 응답이 도착할 때마다 메시지 리스트에 추가
  useEffect(() => {
    if (latestAiResponse) {
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: latestAiResponse.answer,
        metadata: {
          query: latestAiResponse.final_query,
          retries: latestAiResponse.retry_count
        }
      }]);
    }
  }, [latestAiResponse]);

  const scrollRef = useRef<HTMLDivElement>(null);

  // 🚀 메시지가 추가될 때마다 하단으로 자동 스크롤
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isSending]); // 메시지 목록이나 전송 상태가 바뀔 때 실행
  

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isSending) return;

    // 1. 사용자 질문을 화면에 즉시 추가
    const userMsg = question;
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }]);
    setQuestion('');
    setIsSending(true);

    // 2. 백엔드로 질문 전송
    try {
      await fetch('http://localhost:8080/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userMsg }),
      });
    } finally {
      setIsSending(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-4 md:p-8 bg-slate-50">
      <div className="w-full max-w-3xl bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col h-[85vh]">
        {/* Header */}
        <div className="bg-slate-900 p-5 text-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500 rounded-lg">
              <Bot size={24} />
            </div>
            <div>
              <h1 className="font-bold text-lg">KyleLab Meta-Agent</h1>
              <p className="text-[10px] text-slate-400 uppercase tracking-widest">Powered by Java 21 & LangGraph</p>
            </div>
          </div>
          <Sparkles className="text-yellow-400 animate-pulse" size={20} />
        </div>

        {/* Chat Content */}
        <div 
          ref={scrollRef} /* 🚀 1. 여기에 ref를 꼭 달아주셔야 자동 스크롤이 작동합니다! */
          className="flex-1 overflow-y-auto p-6 space-y-6 bg-[#F8FAFC] scroll-smooth"
        >
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 space-y-2">
              <Bot size={48} className="opacity-20" />
              <p>무엇이든 물어보세요. AI 에이전트가 사고를 시작합니다.</p>
            </div>
          )}
          
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] p-4 rounded-2xl shadow-sm ${
                msg.role === 'user' 
                  ? 'bg-blue-600 text-white rounded-tr-none' 
                  : 'bg-white border border-slate-200 text-slate-800 rounded-tl-none'
              }`}>
                <div className="flex items-center gap-2 mb-1 opacity-70">
                  {msg.role === 'user' ? <User size={14} /> : <Bot size={14} />}
                  <span className="text-[10px] font-bold uppercase">{msg.role}</span>
                </div>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                
                {msg.metadata && (
                  <div className="mt-3 pt-2 border-t border-slate-100 text-[10px] text-blue-500 font-mono">
                    🔍 Query: {msg.metadata.query} | 🔄 Retries: {msg.metadata.retries}
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* 🚀 2. AI가 생각 중일 때 보여줄 타이핑 인디케이터 (메시지 맵핑 바로 아래에 추가) */}
          {isSending && (
            <div className="flex justify-start">
              <div className="bg-white border border-slate-200 p-4 rounded-2xl rounded-tl-none shadow-sm flex items-center gap-3">
                <Bot size={16} className="text-blue-500 animate-pulse" />
                <span className="text-sm text-slate-500 font-medium">AI 에이전트가 사고 중입니다</span>
                <div className="flex gap-1.5 ml-1">
                  <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                  <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                  <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input Field */}
        <form onSubmit={handleSubmit} className="p-4 bg-white border-t border-slate-100 flex gap-3">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={isSending}
            placeholder={isSending ? "AI가 추론 중입니다..." : "질문을 입력하세요..."}
            className="flex-1 p-3 bg-slate-100 border-none rounded-xl focus:ring-2 focus:ring-blue-500 text-slate-700 placeholder:text-slate-400 transition-all"
          />
          <button 
            type="submit"
            disabled={isSending || !question.trim()}
            className="bg-blue-600 text-white px-5 rounded-xl hover:bg-blue-700 disabled:bg-slate-300 transition-all flex items-center gap-2"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </main>
  );
}