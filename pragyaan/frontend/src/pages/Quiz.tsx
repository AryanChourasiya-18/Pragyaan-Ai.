import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, QuizItem } from "../lib/api";

const TYPES = ["mcq", "short_answer", "true_false", "fill_blank", "hots"];
const DIFFICULTIES = ["easy", "medium", "hard"];

type Stage = "config" | "taking" | "results";

interface ResultItem {
  question_id: string;
  correct: boolean;
  correct_answer: string;
  explanation?: string;
}

export default function Quiz() {
  const { documentId } = useParams();
  const [stage, setStage] = useState<Stage>("config");

  const [types, setTypes] = useState<string[]>(["mcq"]);
  const [difficulty, setDifficulty] = useState("medium");
  const [examLevel, setExamLevel] = useState("");
  const [count, setCount] = useState(10);
  const [negativeMarking, setNegativeMarking] = useState(false);
  const [generating, setGenerating] = useState(false);

  const [quiz, setQuiz] = useState<QuizItem | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [secondsLeft, setSecondsLeft] = useState<number | null>(null);
  const [results, setResults] = useState<{ score: number; total_marks: number; results: ResultItem[] } | null>(null);

  useEffect(() => {
    if (stage !== "taking" || secondsLeft === null) return;
    if (secondsLeft <= 0) { submitQuiz(); return; }
    const t = setTimeout(() => setSecondsLeft((s) => (s ?? 1) - 1), 1000);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [secondsLeft, stage]);

  function toggleType(t: string) {
    setTypes((prev) => (prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]));
  }

  async function generateQuiz() {
    if (!documentId) return;
    setGenerating(true);
    try {
      const { data } = await api.post("/quiz/generate", {
        document_id: documentId,
        question_types: types,
        difficulty,
        exam_level: examLevel || null,
        count,
        negative_marking: negativeMarking,
      });
      setQuiz(data);
      setAnswers({});
      setStage("taking");
      if (data.time_limit_seconds) setSecondsLeft(data.time_limit_seconds);
    } finally {
      setGenerating(false);
    }
  }

  async function submitQuiz() {
    if (!quiz) return;
    const payload = {
      quiz_id: quiz.id,
      answers: Object.entries(answers).map(([question_id, answer]) => ({ question_id, answer })),
    };
    const { data } = await api.post("/quiz/submit", payload);
    setResults(data);
    setStage("results");
  }

  if (stage === "config") {
    return (
      <div className="max-w-2xl">
        <div className="eyebrow mb-2">Question Generator</div>
        <h1 className="text-3xl mb-8">Build a quiz from this PDF</h1>

        <div className="card p-6 space-y-6">
          <div>
            <label className="text-sm text-muted block mb-2">Question types</label>
            <div className="flex flex-wrap gap-2">
              {TYPES.map((t) => (
                <button
                  key={t}
                  onClick={() => toggleType(t)}
                  className={`px-3 py-1.5 rounded-full text-sm border capitalize ${
                    types.includes(t) ? "bg-marigold text-ink border-marigold" : "border-ink-border text-muted"
                  }`}
                >
                  {t.replace("_", " ")}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-muted block mb-2">Difficulty</label>
              <select className="input w-full" value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
                {DIFFICULTIES.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div>
              <label className="text-sm text-muted block mb-2">Exam level (optional)</label>
              <select className="input w-full" value={examLevel} onChange={(e) => setExamLevel(e.target.value)}>
                <option value="">General</option>
                <option value="jee">JEE</option>
                <option value="neet">NEET</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 items-end">
            <div>
              <label className="text-sm text-muted block mb-2">Number of questions</label>
              <input type="number" min={3} max={30} className="input w-full" value={count}
                onChange={(e) => setCount(Number(e.target.value))} />
            </div>
            <label className="flex items-center gap-2 text-sm mb-2">
              <input type="checkbox" checked={negativeMarking} onChange={(e) => setNegativeMarking(e.target.checked)} />
              Negative marking (-0.25 per wrong)
            </label>
          </div>

          <button className="btn-primary w-full" onClick={generateQuiz} disabled={generating || types.length === 0}>
            {generating ? "Generating…" : "Generate quiz"}
          </button>
        </div>
      </div>
    );
  }

  if (stage === "taking" && quiz) {
    return (
      <div className="max-w-2xl">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl">{quiz.title}</h1>
          {secondsLeft !== null && (
            <div className="text-marigold font-mono">
              {String(Math.floor(secondsLeft / 60)).padStart(2, "0")}:{String(secondsLeft % 60).padStart(2, "0")}
            </div>
          )}
        </div>

        <div className="space-y-5">
          {quiz.questions.map((q, i) => (
            <div key={q.id} className="card p-5">
              <div className="text-xs text-muted mb-2">Q{i + 1} · {q.type.replace("_", " ")}</div>
              <p className="mb-3">{q.question_text}</p>

              {q.options ? (
                <div className="space-y-2">
                  {q.options.map((opt) => (
                    <label key={opt} className="flex items-center gap-2 text-sm cursor-pointer">
                      <input
                        type="radio"
                        name={q.id}
                        checked={answers[q.id] === opt}
                        onChange={() => setAnswers((a) => ({ ...a, [q.id]: opt }))}
                      />
                      {opt}
                    </label>
                  ))}
                </div>
              ) : (
                <input
                  className="input w-full"
                  placeholder="Your answer"
                  value={answers[q.id] || ""}
                  onChange={(e) => setAnswers((a) => ({ ...a, [q.id]: e.target.value }))}
                />
              )}
            </div>
          ))}
        </div>

        <button className="btn-primary w-full mt-6" onClick={submitQuiz}>Submit quiz</button>
      </div>
    );
  }

  if (stage === "results" && results && quiz) {
    return (
      <div className="max-w-2xl">
        <div className="eyebrow mb-2">Results</div>
        <h1 className="text-3xl mb-6">
          {results.score} / {results.total_marks}
        </h1>

        <div className="space-y-4">
          {quiz.questions.map((q) => {
            const r = results.results.find((x) => x.question_id === q.id);
            return (
              <div key={q.id} className={`card p-5 ${r?.correct ? "border-teal/50" : "border-rose/50"}`}>
                <p className="mb-2">{q.question_text}</p>
                <p className="text-sm">
                  Your answer: <span className={r?.correct ? "text-teal" : "text-rose"}>{answers[q.id] || "—"}</span>
                </p>
                {!r?.correct && (
                  <p className="text-sm text-muted">Correct answer: {r?.correct_answer}</p>
                )}
                {r?.explanation && <p className="text-sm text-muted mt-2">{r.explanation}</p>}
              </div>
            );
          })}
        </div>

        <button className="btn-ghost mt-6" onClick={() => setStage("config")}>
          Generate another quiz
        </button>
      </div>
    );
  }

  return null;
}
