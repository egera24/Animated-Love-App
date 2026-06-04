type Props = {
  text: string;
  speaker?: string;
  loading?: boolean;
};

export default function SpeechBubble({ text, speaker, loading }: Props) {
  return (
    <div
      className={`speech-bubble${loading ? " speech-bubble--loading" : ""}`}
      role="status"
      aria-live="polite"
      aria-busy={loading}
    >
      {speaker && <p className="speech-bubble__speaker">{speaker}</p>}
      <p className="speech-bubble__text">
        {loading ? "Fahéj gondolkodik…" : text}
      </p>
    </div>
  );
}
