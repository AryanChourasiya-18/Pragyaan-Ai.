import { FormEvent, useState } from "react";
import { useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import { api } from "../lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: { page: number; snippet: string }[];
}

const SUMMARY_STYLES = [
  { key: "bullet_points", label: "Bullet points" },
  { key: "100_words", label: "100 words" },
  { key: "500_words", label: "500 words" },
  { key: "beginner", label: "Beginner" },
  { key: "advanced", label: "Advanced" },
  { key: "eli10", label: "ELI10" },
];

export default function Chat() {
  const { documentId } = useParams();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [summary, setSummary] = useState("");
  const [summaryLoading, setSummaryLoading] = useState(false);

  async function sendMessage(e: FormEvent) {
    e.preventDefault();
    if (!input.trim() || !documentId) return;
    const userMsg: Message = { role: "user", content: input };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setSending(true);
    try {
      const { data } = await api.post("/ai/chat", { document_id: documentId, message: userMsg.content });
      setMessages((m) => [...m, { role: "assistant", content: data.answer, sources: data.sources }]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: "Something went wrong answering that — try again." }]);
    } finally {
      setSending(false);
    }
  }

  async function generateSummary(style: string) {
    if (!documentId) return;
    setSummaryLoading(true);
    try {
      const { data } = await api.post("/ai/summary", { document_id: documentId, style });
      setSummary(data.summary);
    } finally {
      setSummaryLoading(false);
    }
  }

  return (
    <div className="grid grid-cols-3 gap-6 h-full">
      <div className="col-span-2 flex flex-col h-[calc(100vh-4rem)]">
        <div className="eyebrow mb-2">Chat with this PDF</div>
        <h1 className="text-2xl mb-6">Ask anything from the document</h1>

        <div className="flex-1 overflow-y-auto space-y-4 pr-2">
          {messages.length === 0 && (
            <p className="text-muted text-sm">
              Try: "Explain Newton's Third Law" — answers are grounded strictly in this PDF, with page citations.
            </p>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`card p-4 ${m.role === "user" ? "border-marigold/40" : ""}`}>
              <div className="text-xs text-muted mb-1 uppercase tracking-wide">
                {m.role === "user" ? "You" : "Pragyaan"}
              </div>
              <div className="prose prose-invert prose-sm max-w-none">
                <ReactMarkdown>{m.content}</ReactMarkdown>
              </div>
              {m.sources && m.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-ink-border text-xs text-muted space-y-1">
                  {m.sources.map((s, si) => (
                    <div key={si}>Page {s.page}: "{s.snippet}…"</div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        <form onSubmit={sendMessage} className="flex gap-2 mt-4">
          <input
            className="input flex-1"
            placeholder="Ask a question about this PDF…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={sending}
          />
          <button className="btn-primary" disabled={sending}>
            {sending ? "…" : "Send"}
          </button>
        </form>
      </div>

      <div>
        <div className="eyebrow mb-2">AI Summary</div>
        <div className="card p-5 mb-4">
          <div className="flex flex-wrap gap-2 mb-4">
            {SUMMARY_STYLES.map((s) => (
              <button
                key={s.key}
                onClick={() => generateSummary(s.key)}
                className="btn-ghost text-xs px-3 py-1.5"
                disabled={summaryLoading}
              >
                {s.label}
              </button>
            ))}
          </div>
          {summaryLoading ? (
            <p className="text-muted text-sm">Generating…</p>
          ) : summary ? (
            <div className="prose prose-invert prose-sm max-w-none">
              <ReactMarkdown>{summary}</ReactMarkdown>
            </div>
          ) : (
            <p className="text-muted text-sm">Pick a style to generate a summary.</p>
          )}
        </div>
      </div>
    </div>
  );
}
