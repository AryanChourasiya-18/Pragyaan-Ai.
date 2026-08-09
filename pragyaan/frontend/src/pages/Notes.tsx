import { useState } from "react";
import { useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import { api } from "../lib/api";

const KINDS = [
  { key: "revision", label: "Revision notes" },
  { key: "last_minute", label: "Last-minute notes" },
  { key: "formula_sheet", label: "Formula sheet" },
  { key: "definitions", label: "Important definitions" },
  { key: "cheat_sheet", label: "Cheat sheet" },
];

export default function Notes() {
  const { documentId } = useParams();
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeKind, setActiveKind] = useState("");

  async function generate(kind: string) {
    if (!documentId) return;
    setActiveKind(kind);
    setLoading(true);
    try {
      const { data } = await api.post("/notes/generate", { document_id: documentId, kind });
      setContent(data.content_markdown);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl">
      <div className="eyebrow mb-2">Notes Generator</div>
      <h1 className="text-3xl mb-8">Turn this PDF into study notes</h1>

      <div className="flex flex-wrap gap-2 mb-6">
        {KINDS.map((k) => (
          <button
            key={k.key}
            onClick={() => generate(k.key)}
            className={`px-4 py-2 rounded-lg text-sm border ${
              activeKind === k.key ? "bg-marigold text-ink border-marigold" : "border-ink-border text-muted"
            }`}
            disabled={loading}
          >
            {k.label}
          </button>
        ))}
      </div>

      <div className="card p-6 min-h-[300px]">
        {loading ? (
          <p className="text-muted">Generating…</p>
        ) : content ? (
          <div className="prose prose-invert max-w-none">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        ) : (
          <p className="text-muted">Pick a note type above.</p>
        )}
      </div>
    </div>
  );
}
