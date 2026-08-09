import { FormEvent, useState } from "react";
import { api } from "../lib/api";

const SUBJECTS = ["physics", "chemistry", "maths", "biology", "english"];

interface PlanEntry {
  day_number: number;
  date: string;
  subject: string;
  topic: string;
  task_type: string;
  completed: boolean;
}

export default function Planner() {
  const [goal, setGoal] = useState("JEE in 100 days");
  const [examDate, setExamDate] = useState("");
  const [subjects, setSubjects] = useState<string[]>(["physics", "chemistry", "maths"]);
  const [hoursPerDay, setHoursPerDay] = useState(3);
  const [plan, setPlan] = useState<PlanEntry[]>([]);
  const [loading, setLoading] = useState(false);

  function toggleSubject(s: string) {
    setSubjects((prev) => (prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]));
  }

  async function generate(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await api.post("/planner/generate", {
        goal,
        exam_date: new Date(examDate).toISOString(),
        subjects,
        hours_per_day: hoursPerDay,
      });
      setPlan(data);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl">
      <div className="eyebrow mb-2">Study Planner</div>
      <h1 className="text-3xl mb-8">AI-generated schedule</h1>

      <form onSubmit={generate} className="card p-6 space-y-5 mb-8">
        <div>
          <label className="text-sm text-muted block mb-2">Goal</label>
          <input className="input w-full" value={goal} onChange={(e) => setGoal(e.target.value)} />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-muted block mb-2">Exam date</label>
            <input type="date" className="input w-full" value={examDate}
              onChange={(e) => setExamDate(e.target.value)} required />
          </div>
          <div>
            <label className="text-sm text-muted block mb-2">Hours per day</label>
            <input type="number" min={1} max={12} className="input w-full" value={hoursPerDay}
              onChange={(e) => setHoursPerDay(Number(e.target.value))} />
          </div>
        </div>

        <div>
          <label className="text-sm text-muted block mb-2">Subjects</label>
          <div className="flex flex-wrap gap-2">
            {SUBJECTS.map((s) => (
              <button type="button" key={s} onClick={() => toggleSubject(s)}
                className={`px-3 py-1.5 rounded-full text-sm capitalize border ${
                  subjects.includes(s) ? "bg-marigold text-ink border-marigold" : "border-ink-border text-muted"
                }`}>
                {s}
              </button>
            ))}
          </div>
        </div>

        <button className="btn-primary w-full" disabled={loading || subjects.length === 0}>
          {loading ? "Building your plan…" : "Generate plan"}
        </button>
      </form>

      {plan.length > 0 && (
        <div className="space-y-2">
          {plan.map((p) => (
            <div key={p.day_number} className="card p-4 flex items-center justify-between">
              <div>
                <div className="text-xs text-muted">
                  Day {p.day_number} · {new Date(p.date).toLocaleDateString()} · <span className="capitalize">{p.task_type}</span>
                </div>
                <div className="capitalize font-medium">{p.subject}: {p.topic}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
