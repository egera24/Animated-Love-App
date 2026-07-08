import { FormEvent, useEffect, useRef, useState } from "react";
import {
  ChatHistoryItem,
  clearChatHistory,
  fetchChatHistory,
  sendChat,
} from "../api/client";
import Character from "../character/Character";
import { CharacterId, Expression } from "../character/types";
import "./chat.css";

type Props = {
  characterId: CharacterId;
  characterName: string;
};

export default function ChatView({ characterId, characterName }: Props) {
  const [messages, setMessages] = useState<ChatHistoryItem[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [mood, setMood] = useState("idle");
  const [expression, setExpression] = useState<Expression>("neutral");
  const [error, setError] = useState<string | null>(null);
  const listEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let active = true;
    fetchChatHistory(characterId)
      .then((items) => {
        if (!active) return;
        setMessages(items);
        const lastAssistant = [...items].reverse().find((m) => m.role === "assistant");
        if (lastAssistant?.expression) {
          setExpression(lastAssistant.expression as Expression);
        }
      })
      .catch(() => {
        /* empty history is fine */
      });
    return () => {
      active = false;
    };
  }, [characterId]);

  useEffect(() => {
    listEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || sending) return;
    setError(null);
    setInput("");
    setMessages((prev) => [
      ...prev,
      { role: "user", content: text, expression: null, created_at: "" },
    ]);
    setSending(true);
    try {
      const res = await sendChat(text, characterId);
      setMood(res.mood);
      setExpression(res.expression as Expression);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: res.reply,
          expression: res.expression,
          created_at: "",
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Hiba történt.");
    } finally {
      setSending(false);
    }
  }

  async function handleClear() {
    try {
      await clearChatHistory(characterId);
      setMessages([]);
      setExpression("neutral");
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="chat-view">
      <Character
        characterId={characterId}
        mood={mood}
        expression={sending ? "talking" : expression}
        isSpeaking={sending}
        name={characterName}
      />

      <div className="chat-log" role="log" aria-live="polite">
        {messages.length === 0 && !sending && (
          <p className="chat-empty">
            Írj {characterName}-nek! Itt vagyok, és szívesen beszélgetek. 💬
          </p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`chat-msg chat-msg--${m.role === "user" ? "user" : "bot"}`}
          >
            {m.content}
          </div>
        ))}
        {sending && (
          <div className="chat-msg chat-msg--bot chat-msg--typing">
            <span></span>
            <span></span>
            <span></span>
          </div>
        )}
        <div ref={listEndRef} />
      </div>

      {error && <p className="error-text">{error}</p>}

      <form className="chat-input" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Írj egy üzenetet…"
          aria-label="Üzenet"
          disabled={sending}
        />
        <button type="submit" disabled={sending || !input.trim()}>
          Küldés
        </button>
      </form>

      {messages.length > 0 && (
        <button type="button" className="chat-clear" onClick={() => void handleClear()}>
          Beszélgetés törlése
        </button>
      )}
    </div>
  );
}
