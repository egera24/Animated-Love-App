import { useCallback, useEffect, useState } from "react";
import {
  checkAuth,
  fetchToday,
  logout,
  refreshBubble,
  TodayData,
} from "./api/client";
import CharacterSwitcher from "./character/CharacterSwitcher";
import { useCharacterSelection } from "./character/useCharacterSelection";
import ChatView from "./components/ChatView";
import LoginPage from "./components/LoginPage";
import PhotoGallery from "./components/PhotoGallery";
import TodayView from "./components/TodayView";

type Tab = "today" | "chat" | "photos";

export default function App() {
  const [authed, setAuthed] = useState<boolean | null>(null);
  const [tab, setTab] = useState<Tab>("today");
  const [today, setToday] = useState<TodayData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [bubbleLoading, setBubbleLoading] = useState(false);
  const [character, setCharacter] = useCharacterSelection();

  const loadToday = useCallback(async () => {
    setError(null);
    try {
      const data = await fetchToday();
      setToday(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Hiba.");
    }
  }, []);

  const onHedgehogTap = useCallback(async () => {
    if (!today) return;
    setError(null);
    setBubbleLoading(true);
    try {
      const fresh = await refreshBubble();
      setToday({
        ...today,
        bubble_text: fresh.bubble_text,
        mood: fresh.mood,
        expression: fresh.expression,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Hiba.");
    } finally {
      setBubbleLoading(false);
    }
  }, [today]);

  useEffect(() => {
    checkAuth()
      .then((ok) => {
        setAuthed(ok);
        if (ok) void loadToday();
      })
      .catch(() => setAuthed(false));
  }, [loadToday]);

  async function handleLogout() {
    await logout();
    setAuthed(false);
    setToday(null);
  }

  if (authed === null) {
    return <p className="muted" style={{ textAlign: "center", marginTop: "4rem" }}>Betöltés…</p>;
  }

  if (!authed) {
    return (
      <LoginPage
        onSuccess={() => {
          setAuthed(true);
          void loadToday();
        }}
      />
    );
  }

  return (
    <div className="app-shell">
      <button type="button" className="logout-btn" onClick={() => void handleLogout()}>
        Kilépés
      </button>

      <header className="app-header">
        <h1>Fahéj</h1>
        <p className="app-subtitle">Szia, {today?.recipient_name ?? "Edina"}!</p>
      </header>

      <nav className="tab-bar" aria-label="Főmenü">
        <button
          type="button"
          className={tab === "today" ? "active" : ""}
          onClick={() => setTab("today")}
        >
          Ma
        </button>
        <button
          type="button"
          className={tab === "chat" ? "active" : ""}
          onClick={() => setTab("chat")}
        >
          Beszélgetés
        </button>
        <button
          type="button"
          className={tab === "photos" ? "active" : ""}
          onClick={() => setTab("photos")}
        >
          Képek
        </button>
      </nav>

      <CharacterSwitcher value={character} onChange={setCharacter} />

      {error && <p className="error-text">{error}</p>}

      {tab === "today" && today && (
        <TodayView
          data={today}
          characterId={character}
          bubbleLoading={bubbleLoading}
          onHedgehogTap={() => void onHedgehogTap()}
        />
      )}

      {tab === "today" && !today && !error && (
        <p className="muted">Fahéj ébredezik…</p>
      )}

      {tab === "chat" && (
        <ChatView
          characterId={character}
          characterName={
            character === "hedgehog" ? today?.hedgehog_name ?? "Fahéj" : "Ő"
          }
        />
      )}

      {tab === "photos" && <PhotoGallery />}

      <style>{`
        .app-header h1 {
          margin: 0;
          font-size: 1.75rem;
          color: var(--color-honey-dark);
        }
        .app-subtitle {
          margin: 0.25rem 0 0;
          color: var(--color-text-muted);
        }
        .special-badge {
          text-align: center;
          background: var(--color-blush);
          padding: 0.5rem 1rem;
          border-radius: 999px;
          font-weight: 700;
          color: var(--color-accent-deep);
        }
        .weather-card {
          background: var(--color-surface);
          border-radius: var(--radius-md);
          padding: 1rem;
          box-shadow: var(--shadow-soft);
        }
        .weather-card h3 {
          margin: 0 0 0.5rem;
          font-size: 1rem;
          color: var(--color-sage);
        }
        .weather-card p {
          margin: 0;
        }
        .content-card {
          background: var(--color-surface);
          border-radius: var(--radius-md);
          padding: 1rem;
          box-shadow: var(--shadow-soft);
          margin-top: 0.75rem;
        }
        .content-card h3 {
          margin: 0 0 0.5rem;
          font-size: 1rem;
          color: var(--color-honey-dark);
        }
        .content-card-body {
          margin: 0;
          white-space: pre-line;
          line-height: 1.5;
        }
        .content-links {
          margin: 0.6rem 0 0;
          padding-left: 1.1rem;
          display: flex;
          flex-direction: column;
          gap: 0.3rem;
        }
        .content-links li {
          font-size: 0.9rem;
          line-height: 1.35;
        }
        .content-links a {
          color: var(--color-accent-deep);
          text-decoration: none;
        }
        .content-links a:hover {
          text-decoration: underline;
        }
      `}</style>
    </div>
  );
}
