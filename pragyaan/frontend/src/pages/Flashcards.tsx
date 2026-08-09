import { useEffect, useState } from "react";
import { api, FlashcardItem } from "../lib/api";

export default function Flashcards() {
  const [cards, setCards] = useState<FlashcardItem[]>([]);
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadDue(); }, []);

  async function loadDue() {
    setLoading(true);
    const { data } = await api.get("/flashcards/due");
    setCards(data);
    setIndex(0);
    setFlipped(false);
    setLoading(false);
  }

  async function rate(quality: number) {
    const card = cards[index];
    if (!card) return;
    await api.post("/flashcards/review", { flashcard_id: card.id, quality });
    setFlipped(false);
    if (index + 1 < cards.length) {
      setIndex(index + 1);
    } else {
      loadDue();
    }
  }

  const current = cards[index];

  return (
    <div className="max-w-xl">
      <div className="eyebrow mb-2">Flashcards</div>
      <h1 className="text-3xl mb-8">Due for review</h1>

      {loading ? (
        <p className="text-muted">Loading…</p>
      ) : !current ? (
        <div className="card p-10 text-center text-muted">
          Nothing due right now — generate flashcards from a PDF's chat page, or come back later.
        </div>
      ) : (
        <>
          <div
            onClick={() => setFlipped((f) => !f)}
            className="card p-10 min-h-[220px] flex items-center justify-center text-center cursor-pointer select-none"
          >
            <p className="text-xl">{flipped ? current.back : current.front}</p>
          </div>
          <p className="text-center text-xs text-muted mt-2">
            {index + 1} / {cards.length} · tap card to {flipped ? "hide" : "reveal"} answer
          </p>

          {flipped && (
            <div className="grid grid-cols-4 gap-2 mt-5">
              <button onClick={() => rate(1)} className="btn-ghost text-sm border-rose/50 text-rose">Again</button>
              <button onClick={() => rate(3)} className="btn-ghost text-sm">Hard</button>
              <button onClick={() => rate(4)} className="btn-ghost text-sm">Good</button>
              <button onClick={() => rate(5)} className="btn-ghost text-sm border-teal/50 text-teal">Easy</button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
