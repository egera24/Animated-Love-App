type Props = {
  text: string;
  speaker?: string;
};

export default function SpeechBubble({ text, speaker }: Props) {
  return (
    <div className="speech-bubble" role="status" aria-live="polite">
      {speaker && <p className="speech-bubble__speaker">{speaker}</p>}
      <p className="speech-bubble__text">{text}</p>
    </div>
  );
}
