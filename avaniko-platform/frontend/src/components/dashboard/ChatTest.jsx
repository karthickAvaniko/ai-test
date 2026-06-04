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
  const { apiKey }                = useAuth();
  const bottomRef                 = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const send = async () => {
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
        apiKey, messages: history, model
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
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-5 border-b border-gray-800 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Chat Test</h1>
          <p className="text-sm text-gray-400">Test your API key with live streaming</p>
        </div>
        <select value={model} onChange={(e) => setModel(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none">
          <option value="qwen3-moe">qwen3-moe</option>
          <option value="llama-3.1-70b">llama-3.1-70b</option>
          <option value="claude-3-5-sonnet-20241022">claude-3.5-sonnet</option>
        </select>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-600 mt-20">
            <Bot size={40} className="mx-auto mb-3 opacity-30" />
            <p>Send a message to test your API</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            {msg.role === "assistant" && (
              <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center flex-shrink-0">
                <Bot size={14} />
              </div>
            )}
            <div className={`max-w-2xl px-4 py-3 rounded-2xl text-sm whitespace-pre-wrap leading-relaxed ${
              msg.role === "user"
                ? "bg-indigo-600 text-white rounded-br-sm"
                : "bg-gray-800 text-gray-200 rounded-bl-sm"
            }`}>
              {msg.content}
              {streaming && i === messages.length - 1 && msg.role === "assistant" && (
                <span className="inline-block w-1 h-4 bg-indigo-400 ml-1 animate-pulse align-middle" />
              )}
            </div>
            {msg.role === "user" && (
              <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center flex-shrink-0">
                <User size={14} />
              </div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-800">
        <div className="flex gap-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
            placeholder="Type a message..."
            className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white focus:border-indigo-500 focus:outline-none text-sm"
          />
          <button onClick={send} disabled={streaming || !input.trim()}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-3 rounded-xl disabled:opacity-40 transition">
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
