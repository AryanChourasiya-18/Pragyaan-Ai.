import { NavLink } from "react-router-dom";
import { useAuth } from "../lib/auth";

const links = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/upload", label: "Upload PDFs" },
  { to: "/flashcards", label: "Flashcards" },
  { to: "/planner", label: "Study Planner" },
];

export default function Sidebar() {
  const { user, logout } = useAuth();

  return (
    <aside className="w-64 shrink-0 border-r border-ink-border bg-ink-surface flex flex-col">
      <div className="px-6 py-7 border-b border-ink-border">
        <div className="eyebrow mb-1">Pragyaan</div>
        <div className="text-lg font-display font-semibold">Study, from your own notes</div>
      </div>

      <nav className="flex-1 px-3 py-6 space-y-1">
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.end}
            className={({ isActive }) =>
              `block px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-marigold/10 text-marigold"
                  : "text-muted hover:text-parchment hover:bg-ink-raised"
              }`
            }
          >
            {l.label}
          </NavLink>
        ))}
      </nav>

      <div className="h-10 bg-jali bg-jali opacity-60" />

      <div className="px-6 py-5 border-t border-ink-border flex items-center justify-between">
        <div className="text-sm">
          <div className="font-medium">{user?.full_name || user?.email}</div>
          <div className="text-muted capitalize text-xs">{user?.role}</div>
        </div>
        <button onClick={logout} className="text-xs text-muted hover:text-rose">
          Log out
        </button>
      </div>
    </aside>
  );
}
