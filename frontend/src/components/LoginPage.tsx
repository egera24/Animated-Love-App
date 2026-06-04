import { FormEvent, useState } from "react";
import { login } from "../api/client";

type Props = {
  onSuccess: () => void;
};

export default function LoginPage({ onSuccess }: Props) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(password);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Hiba történt.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <h1>Fahéj 🦔</h1>
      <p>Egy kis süni Edinának — add meg a jelszót.</p>
      <form onSubmit={handleSubmit}>
        <input
          type="password"
          placeholder="Jelszó"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          required
        />
        {error && <p className="error-text">{error}</p>}
        <button type="submit" disabled={loading}>
          {loading ? "Belépés…" : "Belépés"}
        </button>
      </form>
    </div>
  );
}
