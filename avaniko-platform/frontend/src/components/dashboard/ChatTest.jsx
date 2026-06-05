import { useState, useRef, useEffect } from "react";
import { useAuth } from "../../store/auth";
import { streamChat } from "../../lib/api";
import { Send, Bot, User } from "lucide-react";
import toast from "react-hot-toast";

export default function ChatTest() {
  const [messages, setMessages]   = useState([]);
  const [input, setInput]         = useState("");
  const [streaming, setStreaming] = useState(false);
  const [model, setModel]         = useState("qwen3-moe");
  const [projectId, setProjectId] = useState("");
  const [projects, setProjects]   = useState([]); // Should be fetched from API in real usage or passed down
  const { apiKey }                = useAuth();
  const bottomRef                 = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const send = async (e) => {
    e?.preventDefault();
    if (!input.trim() || streaming) return;
    if (!apiKey) return toast.error("Set your API key in the API Keys tab first");

    const userMsg = { role: "user", content: input };
    const history = [...messages, userMsg];
    setMessages(history);
    setInput("");
    setStreaming(true);

    const assistantMsg = { role: "assistant", content: "" };
    setMessages([...history, assistantMsg]);

    try {
      for await (const token of streamChat({
        apiKey, messages: history, model, projectId: projectId || undefined
      })) {
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            content: updated[updated.length - 1].content + token
          };
          return updated;
        });
      }
    } catch (err) {
      toast.error("Stream failed: " + err.message);
    } finally {
      setStreaming(false);
    }
  };

  return (
    <div className="h-[calc(100vh-2rem)] flex flex-col p-4 md:p-8 animate-fade-up">
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-4 flex-shrink-0 gap-4">
        <div>
          <h1 className="text-3xl font-bold font-display text-white">Chat Playground</h1>
          <p className="text-gray-400 text-sm mt-1">Test your models and projects directly.</p>
        </div>
        <div className="flex gap-3">
          <select value={model} onChange={e => setModel(e.target.value)}
            className="input-premium rounded-xl px-4 py-2 text-sm appearance-none min-w-[150px]">
            <option value="qwen3-moe">Qwen3 Mixture of Experts</option>
            <option value="llama-3.1-70b">Llama 3.1 70B</option>
            <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
          </select>
          <select value={projectId} onChange={e => setProjectId(e.target.value)}
            className="input-premium rounded-xl px-4 py-2 text-sm appearance-none min-w-[150px]">
            <option value="">No Project (Base Model)</option>
            {projects.map(p => <option key={p.project_id} value={p.project_id}>{p.name}</option>)}
          </select>
        </div>
      </div>

      <div className="flex-1 glass rounded-2xl border-gradient overflow-hidden flex flex-col relative shadow-2xl">
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-purple-500/5 rounded-full blur-3xl pointer-events-none"></div>
        
        <div className="flex-1 overflow-y-auto p-6 space-y-6 z-10 relative" id="chat-messages">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-gray-500 opacity-50">
              <Bot size={48} className="mb-4 text-indigo-400/50" />
              <p>Start typing to test the API.</p>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"} ${m.role === "user" ? "msg-user" : "msg-ai"}`}>
              <div className={`max-w-[80%] rounded-2xl px-5 py-3 shadow-lg ${
                m.role === "user" 
                  ? "bg-gradient-to-br from-indigo-600 to-purple-600 text-white rounded-br-none" 
                  : "bg-[#050505]/60 border border-white/10 text-gray-200 rounded-bl-none backdrop-blur-md"
              }`}>
                {m.role === "assistant" && <Bot size={14} className="inline mr-2 text-indigo-400 mb-1" />}
                <span className="whitespace-pre-wrap leading-relaxed">{m.content}</span>
                {streaming && i === messages.length - 1 && m.role === "assistant" && (
                  <span className="inline-block w-1 h-4 bg-indigo-400 ml-1 animate-pulse align-middle" />
                )}
              </div>
            </div>
          ))}
          {streaming && messages[messages.length - 1]?.role === "user" && (
            <div className="flex justify-start msg-ai">
              <div className="bg-[#050505]/60 border border-white/10 text-gray-400 rounded-2xl rounded-bl-none px-5 py-4 flex gap-1.5 backdrop-blur-md">
                <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></span>
                <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></span>
                <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="p-4 border-t border-white/5 bg-black/20 backdrop-blur-md z-10">
          <form onSubmit={send} className="flex gap-3">
            <input
              value={input} onChange={e => setInput(e.target.value)}
              placeholder="Message Avaniko AI..."
              className="flex-1 input-premium rounded-xl px-5 py-4 shadow-inner"
            />
            <button type="submit" disabled={!input.trim() || streaming}
              className="btn-glow text-white px-6 rounded-xl flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed">
              <Send size={18} className={input.trim() && !streaming ? "text-white" : "text-gray-400"} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
