'use client';

import { useState } from 'react';
import { useSSE } from '@/hooks/useSSE';
import { Send, Bot, User } from 'lucide-react';

export default function ChatPage() {
  const [question, setQuestion] = useState('');
  const [isSending, setIsSending] = useState(false);
  const latestResponse = useSSE('http://localhost:8080/api/stream');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setIsSending(true);
    await fetch('http://localhost:8080/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });
    setQuestion('');
    setIsSending(false);
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-8 bg-slate-50">
      <div className="w-full max-w-2xl bg-white rounded-2xl shadow-xl overflow-hidden flex flex-col h-[80vh]">
        {/* 헤더 */}
        <div className="bg-slate-800 p-4 text-white flex items-center gap-2">
          <Bot size={24} className="text-blue-400" />
          <h1 className="font-bold">KyleLab AI Meta-Agent</h1>
        </div>

        {/* 채팅 내역 영역 */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {latestResponse && (
            <div className="flex gap-3">
              <div className="bg-blue-100 p-3 rounded-2xl rounded-tl-none">
                <p className="text-sm font-semibold text-blue-800 mb-1">AI Agent</p>
                <p className="text-slate-700 leading-relaxed">{latestResponse.answer}</p>
                <div className="mt-2 text-[10px] text-blue-500 italic">
                  Final Query: {latestResponse.final_query} (Retries: {latestResponse.retry_count})
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 입력창 */}
        <form onSubmit={handleSubmit} className="p-4 border-t flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="AI에게 무엇이든 물어보세요..."
            className="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-700"
          />
          <button 
            disabled={isSending}
            className="bg-blue-600 text-white p-2 rounded-lg hover:bg-blue-700 disabled:bg-slate-400 transition-colors"
          >
            <Send size={20} />
          </button>
        </form>
      </div>
    </main>
  );
}