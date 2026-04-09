import { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Bot, User, Minimize2, Loader2, Info, Paperclip, Link as LinkIcon } from 'lucide-react';
import { api } from '../api/client';
import { useAppStore } from '../store/appStore';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function ChatWidget() {
  const { analysisResult, selectedHistoryItem } = useAppStore();
  const [isOpen, setIsOpen] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [useContext, setUseContext] = useState(true);
  const [sessions, setSessions] = useState<any[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: "Hello! I'm your IndustriFix Assistant. How can I help you with your maintenance tasks today?" }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Determine active context
  const activeContext = selectedHistoryItem || (analysisResult?.history_id ? analysisResult : null);
  const contextId = selectedHistoryItem?.id || analysisResult?.history_id;
  const contextName = selectedHistoryItem?.machine_part || analysisResult?.analysis_result?.machine_part;

  // Load sessions when widget opens
  useEffect(() => {
    if (isOpen) {
        loadSessions();
    }
  }, [isOpen]);

  const loadSessions = async () => {
    try {
        const data = await api.getChatSessions();
        setSessions(data);
    } catch (err) {
        console.error("Failed to load sessions", err);
    }
  };

  const loadHistory = async (sessionId: number) => {
    setIsTyping(true);
    setShowHistory(false);
    setCurrentSessionId(sessionId);
    try {
        const history = await api.getChatHistory(sessionId);
        setMessages(history);
    } catch (err) {
        console.error("Failed to load history", err);
    } finally {
        setIsTyping(false);
    }
  };

  const startNewChat = () => {
    setCurrentSessionId(null);
    setShowHistory(false);
    setMessages([{ role: 'assistant', content: "How can I help you with a new maintenance task?" }]);
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;

    const userMsg = input.trim();
    const currentContextId = useContext ? contextId : undefined;
    
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setIsTyping(true);

    try {
      const response = await api.getChatStream(userMsg, currentContextId, currentSessionId || undefined);
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      let assistantMsg = '';
      setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

      while (true) {
        const { done, value } = await reader!.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              // If backend created a new session, track it
              if (data.session_id && !currentSessionId) {
                setCurrentSessionId(data.session_id);
                loadSessions(); // Refresh list
              }

              if (data.text) {
                assistantMsg += data.text;
                setMessages(prev => {
                  const newMsgs = [...prev];
                  newMsgs[newMsgs.length - 1].content = assistantMsg;
                  return newMsgs;
                });
              }
            } catch (e) {
              // Ignore partial chunk errors
            }
          }
        }
      }
    } catch (error) {
      console.error("Chat error:", error);
      setMessages(prev => [...prev, { role: 'assistant', content: "I'm sorry, I encountered an error connectng to the AI. Please try again later." }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {/* Chat Window */}
      {isOpen && (
        <div className="mb-4 w-96 h-[560px] bg-white/90 backdrop-blur-xl border border-white/20 shadow-2xl rounded-3xl overflow-hidden flex flex-col animate-in slide-in-from-bottom-4 duration-300">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-indigo-700 p-4 text-white flex items-center justify-between shadow-lg">
            <div className="flex items-center space-x-3">
              <div className="bg-white/20 p-2 rounded-xl cursor-pointer" onClick={() => setShowHistory(!showHistory)}>
                <MessageCircle className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-bold text-sm tracking-wide">IndustriFix Support</h3>
                <div className="flex items-center space-x-1">
                    <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></span>
                    <span className="text-[10px] text-blue-100 uppercase font-bold">AI Online</span>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
                <button 
                    onClick={startNewChat}
                    className="p-1.5 hover:bg-white/20 rounded-lg transition text-[10px] font-bold uppercase"
                >
                    New Chat
                </button>
                <button onClick={() => setIsOpen(false)} className="hover:bg-white/10 p-2 rounded-full transition">
                <Minimize2 className="w-5 h-5" />
                </button>
            </div>
          </div>

          {/* History Overlay */}
          {showHistory && (
            <div className="absolute inset-x-0 top-[68px] bottom-0 bg-white z-20 animate-in fade-in slide-in-from-top-2 duration-300 flex flex-col">
                <div className="p-4 border-b flex justify-between items-center bg-gray-50">
                    <h4 className="font-bold text-gray-700 text-sm">Recent Conversations</h4>
                    <button onClick={() => setShowHistory(false)} className="text-gray-400 hover:text-gray-600">
                        <X className="w-4 h-4" />
                    </button>
                </div>
                <div className="flex-1 overflow-y-auto p-2">
                    {sessions.length === 0 ? (
                        <div className="text-center py-12 text-gray-400 text-sm italic">
                            No past conversations
                        </div>
                    ) : (
                        sessions.map(s => (
                            <button 
                                key={s.id}
                                onClick={() => loadHistory(s.id)}
                                className={`w-full text-left p-3 rounded-xl transition mb-1 group ${currentSessionId === s.id ? 'bg-blue-50 border-blue-100' : 'hover:bg-gray-50'}`}
                            >
                                <div className="font-semibold text-gray-800 text-sm truncate">{s.title}</div>
                                <div className="text-[10px] text-gray-400 mt-1">{new Date(s.created_at).toLocaleString()}</div>
                            </button>
                        ))
                    )}
                </div>
            </div>
          )}

          {/* Context Banner */}
          {contextName && (
             <div className="bg-blue-50 border-b border-blue-100 p-2 px-4 flex items-center justify-between">
                <div className="flex items-center space-x-2 overflow-hidden">
                    <LinkIcon className="w-3 h-3 text-blue-600 flex-shrink-0" />
                    <span className="text-[10px] font-bold text-blue-700 uppercase tracking-tighter truncate">
                        Referencing: {contextName}
                    </span>
                </div>
                <button 
                    onClick={() => setUseContext(!useContext)}
                    className={`px-2 py-0.5 rounded text-[10px] font-bold transition ${useContext ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'}`}
                >
                    {useContext ? 'ENABLED' : 'DISABLED'}
                </button>
             </div>
          )}

          {/* Messages */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50/50">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`flex items-start max-w-[80%] space-x-2 ${msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                  <div className={`p-2 rounded-lg flex-shrink-0 mt-1 ${msg.role === 'user' ? 'bg-blue-100' : 'bg-indigo-100'}`}>
                    {msg.role === 'user' ? <User className="w-4 h-4 text-blue-600" /> : <Bot className="w-4 h-4 text-indigo-600" />}
                  </div>
                  <div className={`p-3 rounded-2xl text-sm shadow-sm ${
                    msg.role === 'user' 
                    ? 'bg-blue-600 text-white rounded-tr-none' 
                    : 'bg-white border border-gray-100 text-gray-800 rounded-tl-none'
                  }`}>
                    {msg.content || (msg.role === 'assistant' && <Loader2 className="w-4 h-4 animate-spin" />)}
                  </div>
                </div>
              </div>
            ))}
            {isTyping && messages[messages.length-1].content === '' && (
                <div className="flex justify-start">
                    <div className="bg-white p-3 rounded-2xl rounded-tl-none border border-gray-100 shadow-sm">
                        <Loader2 className="w-4 h-4 animate-spin text-indigo-600" />
                    </div>
                </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 bg-white border-t border-gray-100">
            <div className="mb-2 flex items-center space-x-2 text-[10px] text-gray-400">
                <Info className="w-3 h-3" />
                <span>Answers based on manuals {useContext && contextName ? `+ ${contextName} context` : ''}</span>
            </div>
            <div className="relative">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Ask about maintenance..."
                className="w-full pl-4 pr-12 py-3 bg-gray-100 border-none rounded-2xl text-sm focus:ring-2 focus:ring-blue-500 focus:bg-white transition"
              />
              <button 
                onClick={handleSend}
                disabled={!input.trim() || isTyping}
                className="absolute right-2 top-1.5 p-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 transition"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bubble Toggle */}
      {!isOpen && (
        <button 
          onClick={() => setIsOpen(true)}
          className="group relative flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-600 to-indigo-700 text-white rounded-full shadow-2xl hover:scale-110 active:scale-95 transition-all duration-300 overflow-hidden"
        >
          <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <MessageCircle className="w-8 h-8 group-hover:rotate-12 transition-transform" />
        </button>
      )}
    </div>
  );
}

