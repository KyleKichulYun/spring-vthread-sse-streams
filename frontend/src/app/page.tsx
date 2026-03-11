'use client';

import { useState, useRef, useEffect } from 'react';
import { useSSE } from '@/hooks/useSSE';
import { Send, Bot, User, Sparkles, AlertCircle, Wifi } from 'lucide-react';
// 🚀 마크다운 렌더링을 위한 패키지 임포트
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

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
  
  const { data: latestAiResponse, isConnected, error } = useSSE('http://localhost:8080/api/stream');

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

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isSending]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isSending || !isConnected) return;

    const userMsg = question;
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }]);
    setQuestion('');
    setIsSending(true);

    try {
      await fetch('http://localhost:8080/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userMsg }),
      });
    } catch (err) {
      console.error("질문 전송 실패:", err);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-4 md:p-8 bg-slate-50">
      <div className="w-full max-w-3xl bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col h-[85vh]">
        
        {/* Header */}
        <div className="bg-slate-900 p-5 text-white flex items-center justify-between z-10">
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

        {/* 네트워크 상태 배너 */}
        {!isConnected && (
          <div className="bg-amber-100 text-amber-800 p-2 text-xs flex items-center justify-center gap-2 border-b border-amber-200">
            <AlertCircle size={14} className="animate-pulse" />
            {error || "서버와 연결 중입니다..."}
          </div>
        )}
        {isConnected && messages.length === 0 && (
           <div className="bg-green-100 text-green-800 p-2 text-xs flex items-center justify-center gap-2 border-b border-green-200 opacity-80 transition-opacity duration-1000">
             <Wifi size={14} />
             실시간 AI 스트림 서버에 연결되었습니다.
           </div>
        )}

        {/* Chat Content */}
        <div 
          ref={scrollRef} 
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
                <div className="flex items-center gap-2 mb-2 opacity-70">
                  {msg.role === 'user' ? <User size={14} /> : <Bot size={14} />}
                  <span className="text-[10px] font-bold uppercase">{msg.role}</span>
                </div>
                
                {/* 🚀 일반 텍스트 대신 ReactMarkdown 컴포넌트를 사용합니다 */}
                <div className="text-sm leading-relaxed overflow-x-auto">
                  {msg.role === 'user' ? (
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  ) : (
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      className="prose prose-sm max-w-none prose-p:my-1 prose-pre:p-0 prose-pre:bg-transparent"
                      components={{
                        code({ node, inline, className, children, ...props }: any) {
                          const match = /language-(\w+)/.exec(className || '');
                          return !inline && match ? (
                            <SyntaxHighlighter
                              style={vscDarkPlus as any}
                              language={match[1]}
                              PreTag="div"
                              className="rounded-lg !my-2"
                              {...props}
                            >
                              {String(children).replace(/\n$/, '')}
                            </SyntaxHighlighter>
                          ) : (
                            <code className="bg-slate-100 text-red-500 px-1.5 py-0.5 rounded text-[13px]" {...props}>
                              {children}
                            </code>
                          );
                        }
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  )}
                </div>
                
                {msg.metadata && (
                  <div className="mt-3 pt-2 border-t border-slate-100 text-[10px] text-blue-500 font-mono">
                    🔍 Query: {msg.metadata.query} | 🔄 Retries: {msg.metadata.retries}
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* AI가 생각 중일 때 보여줄 타이핑 인디케이터 */}
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
            disabled={isSending || !isConnected}
            placeholder={
              !isConnected ? "서버 연결 대기 중..." : 
              isSending ? "AI가 추론 중입니다..." : "질문을 입력하세요..."
            }
            className="flex-1 p-3 bg-slate-100 border-none rounded-xl focus:ring-2 focus:ring-blue-500 text-slate-700 placeholder:text-slate-400 transition-all disabled:opacity-50"
          />
          <button 
            type="submit"
            disabled={isSending || !question.trim() || !isConnected}
            className="bg-blue-600 text-white px-5 rounded-xl hover:bg-blue-700 disabled:bg-slate-300 transition-all flex items-center gap-2"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </main>
  );
}