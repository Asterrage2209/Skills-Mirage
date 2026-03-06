import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, BrainCircuit } from 'lucide-react';
import { chatbotQueryApi } from '../../services/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

const initialMessage =
  "I'm the Skills Mirage Assistant. Ask about AI vulnerability, role transitions, or learning paths.";

const Chatbot = () => {
  const [messages, setMessages] = useState<Message[]>([{ id: '1', role: 'assistant', content: initialMessage }]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { id: Date.now().toString(), role: 'user', content: userMsg }]);
    setIsTyping(true);

    try {
      const res = await chatbotQueryApi({ worker_profile: {}, question: userMsg });
      setMessages((prev) => [...prev, { id: `${Date.now()}-assistant`, role: 'assistant', content: res.response || 'No response.' }]);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Chatbot request failed';
      setMessages((prev) => [...prev, { id: `${Date.now()}-assistant`, role: 'assistant', content: `Error: ${msg}` }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-8rem)] flex flex-col">
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-white mb-1">AI Assistant</h1>
        <p className="text-textSecondary text-sm">Ask questions about market signals or your personal risk profile.</p>
      </div>

      <div className="flex-1 card flex flex-col overflow-hidden bg-secondary border border-white/5">
        <div className="p-4 border-b border-white/5 flex items-center gap-3 bg-card/50">
          <div className="w-10 h-10 rounded-full bg-accent/20 flex items-center justify-center border border-accent/30">
            <BrainCircuit className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h3 className="font-bold text-white text-sm">Skills Mirage Intelligence</h3>
            <div className="flex items-center gap-2 text-xs text-green-400">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
              Online
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              <div className={`w-8 h-8 shrink-0 rounded-full flex items-center justify-center ${msg.role === 'user' ? 'bg-gradient-to-tr from-accent to-purple-500' : 'bg-card border border-white/10'}`}>
                {msg.role === 'user' ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-textSecondary" />}
              </div>

              <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${msg.role === 'user' ? 'bg-accent/20 border border-accent/20 text-white rounded-tr-none' : 'bg-card border border-white/5 text-textSecondary rounded-tl-none'}`}>
                {msg.content}
              </div>
            </div>
          ))}

          {isTyping && (
            <div className="flex gap-4">
              <div className="w-8 h-8 shrink-0 rounded-full flex items-center justify-center bg-card border border-white/10">
                <Bot className="w-4 h-4 text-textSecondary" />
              </div>
              <div className="bg-card border border-white/5 rounded-2xl rounded-tl-none px-4 py-3 flex items-center gap-1">
                <div className="w-2 h-2 bg-textSecondary rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-textSecondary rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                <div className="w-2 h-2 bg-textSecondary rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="p-4 bg-card/50 border-t border-white/5">
          <form onSubmit={handleSend} className="relative flex items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about AI vulnerability or reskilling..."
              className="w-full bg-secondary border border-white/10 rounded-full pl-5 pr-12 py-3 text-sm text-white focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/50 transition-all placeholder:text-textSecondary/50"
            />
            <button
              type="submit"
              disabled={!input.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-accent flex items-center justify-center text-white hover:bg-accent/90 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;
