import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, DocumentItem } from "../lib/api";

interface Summary {
  average_score: number;
  total_study_minutes: number;
  weak_subjects: string[];
  strong_subjects: string[];
}

export default function Dashboard() {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);

  useEffect(() => {
    api.get("/documents").then((r) => setDocs(r.data));
    api.get("/analytics/summary").then((r) => setSummary(r.data)).catch(() => {});
  }, []);

  return (
    <div>
      <div className="eyebrow mb-2">Dashboard</div>
      <h1 className="text-3xl mb-8">Your study desk</h1>

      <div className="grid grid-cols-3 gap-5 mb-10">
        <StatCard label="Average score" value={summary ? `${summary.average_score.toFixed(0)}%` : "—"} />
        <StatCard label="Study time logged" value={summary ? `${summary.total_study_minutes} min` : "—"} />
        <StatCard label="Documents uploaded" value={String(docs.length)} />
      </div>

      {summary && (summary.weak_subjects.length > 0 || summary.strong_subjects.length > 0) && (
        <div className="grid grid-cols-2 gap-5 mb-10">
          <div className="card p-5">
            <div className="text-xs text-muted mb-2 uppercase tracking-wide">Needs attention</div>
            <div className="text-marigold capitalize">{summary.weak_subjects.join(", ") || "—"}</div>
          </div>
          <div className="card p-5">
            <div className="text-xs text-muted mb-2 uppercase tracking-wide">Going strong</div>
            <div className="text-teal capitalize">{summary.strong_subjects.join(", ") || "—"}</div>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl">Recent PDFs</h2>
        <Link to="/upload" className="btn-ghost text-sm">Upload a PDF</Link>
      </div>

      {docs.length === 0 ? (
        <div className="card p-10 text-center text-muted">
          Nothing uploaded yet — bring in a chapter PDF to get summaries, chat, quizzes and flashcards from it.
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          {docs.map((d) => (
            <div key={d.id} className="card p-5">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="font-medium">{d.title}</div>
                  <div className="text-xs text-muted capitalize mt-0.5">
                    {d.subject} · {d.page_count} pages {d.is_ocr && "· OCR"}
                  </div>
                </div>
              </div>
              <div className="flex gap-2 text-sm">
                <Link to={`/chat/${d.id}`} className="text-marigold hover:underline">Chat</Link>
                <span className="text-ink-border">·</span>
                <Link to={`/quiz/${d.id}`} className="text-marigold hover:underline">Quiz</Link>
                <span className="text-ink-border">·</span>
                <Link to={`/notes/${d.id}`} className="text-marigold hover:underline">Notes</Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="card p-5">
      <div className="text-xs text-muted uppercase tracking-wide mb-1">{label}</div>
      <div className="text-2xl font-display">{value}</div>
    </div>
  );
}
