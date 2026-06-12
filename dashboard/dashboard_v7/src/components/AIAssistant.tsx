import { useState, useRef, useEffect } from "react";
import { StockData } from "../types";
import { Send, Sparkles, User, HelpCircle, Bot, CornerDownLeft, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface AIAssistantProps {
  stock: StockData;
}

export function AIAssistant({ stock }: AIAssistantProps) {
  const isWatchlist = stock.ticker === "WATCHLIST";

  const welcomeMessage = isWatchlist
    ? `Selamat datang! Saya asisten AI Anda untuk analisis portofolio. Saya bisa menganalisis kumpulan saham di Daftar Pantau Anda.

Apa yang ingin Anda tanyakan tentang daftar pantauan Anda hari ini?`
    : `Selamat datang! Saya asisten AI Anda untuk analisis saham. Saya bisa membantu menganalisis laporan keuangan, tren makroekonomi, dan pergerakan pasar saham Indonesia. 
      
Apa yang ingin Anda tanyakan tentang **PT ${stock.name} (${stock.ticker})** hari ini?`;

  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: welcomeMessage,
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const presets = isWatchlist ? [
    { label: "Risiko Sektoral", query: `Tolong analisis risiko sektoral dari saham-saham dalam daftar pantau saya.` },
    { label: "Dampak Suku Bunga BI", query: `Bagaimana pengaruh tingkat suku bunga Bank Indonesia terhadap daftar saham pantauan ini?` },
    { label: "Evaluasi Fundamental", query: `Menurut Anda, mana saham dalam daftar pantau saya yang memiliki valuasi (PE & PBV) paling menarik saat ini?` },
  ] : [
    { label: "Analisis Margin Hutang", query: `Tolong analisis keamanan neraca dan pola rasio Hutang terhadap Ekuitas PT ${stock.name} selama 2023-2026.` },
    { label: "Dampak Suku Bunga BI", query: `Bagaimana pengaruh perubahan BI-Rate (suku bunga Bank Indonesia) dan inflasi terhadap PT ${stock.name} atau secara umum sektor ${stock.sector}?` },
    { label: "Cek Tren Keuntungan", query: `Evaluasi tren rasio laba PT ${stock.name} (seperti Margin Laba Bersih vs Pendapatan) dari laporan keuangan terbarunya.` },
  ];

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const handleSend = async (textToSend: string) => {
    if (!textToSend.trim() || isLoading) return;

    const userMsg: Message = { role: "user", content: textToSend };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("/api/gemini/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [...messages, userMsg],
          selectedStock: stock,
        }),
      });

      if (!response.ok) {
        let errMsg = "Failed to get response from AI advisor";
        try { const e = await response.json(); errMsg = e.error || errMsg; } catch {}
        throw new Error(errMsg);
      }

      const data = await response.json();
      setMessages((prev) => [...prev, { role: "assistant", content: data.content }]);
    } catch (error: any) {
      console.error(error);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Maaf, I encountered an issue: ${error.message || "Failed to process question. Please verify API keys in Settings."}` },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div id="ai-assistant-card" className="bg-[#0A0A0A] rounded-2xl border border-white/10 p-6 flex flex-col h-[550px] shadow-sm">
      {/* Header */}
      <div id="ai-assistant-heading" className="flex items-center gap-3 pb-4 border-b border-white/5 mb-4">
        <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center text-emerald-400 border border-white/10">
          <Bot className="w-5 h-5" />
        </div>
        <div>
          <h4 className="text-sm font-bold text-white flex items-center gap-1.5 font-sans">
            Asisten AI {isWatchlist ? 'Analis Portofolio' : 'Analis Saham'}
            <span className="text-[10px] bg-emerald-950/40 text-emerald-400 border border-emerald-900/30 px-2 py-0.5 rounded-full font-bold uppercase tracking-wide">
              {isWatchlist ? 'Aktif' : 'Membantu'}
            </span>
          </h4>
          <p className="text-xs text-white/40">Diskusi seputar {isWatchlist ? 'Daftar Pantau' : stock.ticker} & kondisi pasar IHSG</p>
        </div>
      </div>

      {/* Message Stream */}
      <div 
        id="messages-viewport"
        ref={containerRef}
        className="flex-1 overflow-y-auto space-y-4 pr-1 scrollbar-thin"
      >
        {messages.map((msg, index) => (
          <div
            key={index}
            id={`chat-msg-${index}`}
            className={`flex gap-3 max-w-[85%] ${
              msg.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"
            }`}
          >
            <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
              msg.role === "user" ? "bg-emerald-500 text-black" : "bg-white/10 text-white"
            }`}>
              {msg.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>
            <div className={`p-4 rounded-2xl text-sm leading-relaxed ${
              msg.role === "user" 
                ? "bg-emerald-950/40 text-white rounded-tr-none border border-emerald-500/20" 
                : "bg-white/[0.03] text-white/90 rounded-tl-none border border-white/5"
            }`}>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  h1: ({ children }) => <h1 className="text-lg font-bold text-white mt-4 mb-2">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-base font-bold text-white mt-4 mb-2">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-sm font-bold text-emerald-300 mt-3 mb-1">{children}</h3>,
                  h4: ({ children }) => <h4 className="text-sm font-semibold text-white/80 mt-2 mb-1">{children}</h4>,
                  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                  strong: ({ children }) => <strong className="font-bold text-emerald-300">{children}</strong>,
                  ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                  li: ({ children }) => <li className="text-white/90">{children}</li>,
                  hr: () => <hr className="border-white/10 my-3" />,
                  code: ({ children }) => <code className="bg-white/5 text-emerald-200 px-1.5 py-0.5 rounded text-xs">{children}</code>,
                  pre: ({ children }) => <pre className="bg-white/5 p-3 rounded-xl overflow-x-auto text-xs mb-3 border border-white/5">{children}</pre>,
                  blockquote: ({ children }) => <blockquote className="border-l-2 border-emerald-500/50 pl-4 italic text-white/60 my-2">{children}</blockquote>,
                  table: ({ children }) => <div className="overflow-x-auto mb-3"><table className="w-full text-xs border-collapse">{children}</table></div>,
                  th: ({ children }) => <th className="border border-white/10 px-2.5 py-1.5 text-left font-bold text-emerald-200 bg-white/5">{children}</th>,
                  td: ({ children }) => <td className="border border-white/10 px-2.5 py-1.5 text-white/80">{children}</td>,
                  a: ({ href, children }) => <a href={href} className="text-emerald-400 underline hover:text-emerald-300" target="_blank" rel="noopener noreferrer">{children}</a>,
                }}
              >
                {msg.content}
              </ReactMarkdown>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex gap-3 max-w-[85%] mr-auto">
            <div className="w-8 h-8 rounded-full bg-white/5 text-emerald-400 flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4 text-emerald-450 animate-pulse" />
            </div>
            <div className="p-4 rounded-2xl rounded-tl-none bg-white/[0.02] text-white/50 text-xs flex items-center gap-1.5 border border-white/10 select-none">
              <Loader2 className="w-4 h-4 text-emerald-455 animate-spin" /> Menganalisis melalui Gemini AI...
            </div>
          </div>
        )}
      </div>

      {/* Preset / Suggestions */}
      {messages.length === 1 && !isLoading && (
        <div id="ai-presets-box" className="mt-4 pt-3 border-t border-white/5">
          <span className="text-[10px] uppercase font-bold text-white/40 tracking-widest block mb-2 flex items-center gap-1.5">
            <HelpCircle className="w-4 h-4 text-emerald-400" /> Pertanyaan Populer
          </span>
          <div className="flex flex-wrap gap-2">
            {presets.map((preset, idx) => (
              <button
                key={idx}
                id={`preset-btn-${idx}`}
                onClick={() => handleSend(preset.query)}
                className="text-xs bg-white/5 hover:bg-emerald-950/30 hover:border-emerald-555 hover:text-emerald-300 px-3 py-2 rounded-xl text-left border border-white/10 text-white/70 transition-all font-medium cursor-pointer"
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Form */}
      <div id="prompt-input" className="mt-4 pt-3 border-t border-white/5 flex items-center gap-2">
        <input
          type="text"
          placeholder={isWatchlist ? "Tanyakan tentang sentimen pasar, atau strategi diversifikasi..." : `Tanyakan tentang arus kas PT ${stock.ticker}, strategi valuasi harga...`}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend(input)}
          disabled={isLoading}
          className="flex-1 text-sm px-4 py-3.5 bg-white/5 focus:bg-white/[0.08] rounded-xl outline-none focus:ring-1 focus:ring-emerald-500 border border-white/10 transition-all text-white disabled:opacity-50"
        />
        <button
          onClick={() => handleSend(input)}
          disabled={!input.trim() || isLoading}
          className="w-11 h-11 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-black flex items-center justify-center shrink-0 disabled:opacity-40 transition-all cursor-pointer shadow-sm font-semibold"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
