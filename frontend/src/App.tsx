import { useCallback, useEffect, useState } from "react";
import {
  checkAuth,
  fetchToday,
  logout,
  TodayData,
} from "./api/client";
import LoginPage from "./components/LoginPage";
import PhotoGallery from "./components/PhotoGallery";
import TodayView from "./components/TodayView";

type Tab = "today" | "photos";

export default function App() {
  const [authed, setAuthed] = useState<boolean | null>(null);
  const [tab, setTab] = useState<Tab>("today");
  const [today, setToday] = useState<TodayData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadToday = useCallback(async (refreshBubble = false) => {
    setError(null);
    try {
      const data = await fetchToday(refreshBubble);
      // #region agent log
      fetch(
        "http://127.0.0.1:7310/ingest/2755dbd7-3726-4125-837b-538630925f1b",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Debug-Session-Id": "397eeb",
          },
          body: JSON.stringify({
            sessionId: "397eeb",
            runId: "post-fix",
            hypothesisId: "F",
            location: "App.tsx:loadToday",
            message: "fetchToday_ok",
            data: {
              refreshBubble,
              bubbleLen: data.bubble_text.length,
              bubblePrefix: data.bubble_text.slice(0, 40),
            },
            timestamp: Date.now(),
          }),
        }
      ).catch(() => {});
      // #endregion
      setToday(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Hiba.");
    }
  }, []);

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
          className={tab === "photos" ? "active" : ""}
          onClick={() => setTab("photos")}
        >
          Képek
        </button>
      </nav>

      {error && <p className="error-text">{error}</p>}

      {tab === "today" && today && (
        <TodayView
          data={today}
          onHedgehogTap={() => void loadToday(true)}
        />
      )}

      {tab === "today" && !today && !error && (
        <p className="muted">Fahéj ébredezik…</p>
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
      `}</style>
    </div>
  );
}
