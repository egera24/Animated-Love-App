import { Expression } from "./types";

type Props = {
  mood: string;
  expression: Expression;
  isSpeaking?: boolean;
  name?: string;
  onTap?: () => void;
};

const EXPRESSION_EMOJI: Record<Expression, string> = {
  celebrate: "🥳",
  comfort: "🤗",
  melancholy: "🙂",
  happy: "😄",
  curious: "🤔",
  neutral: "🙂",
  talking: "😊",
};

/**
 * Temporary stand-in for the "avatar of you" character. The proper animated
 * figure is a later phase; this keeps the switcher functional meanwhile and
 * still reflects mood/expression so the rest of the app can be built and tested.
 */
export default function SelfAvatarPlaceholder({
  expression,
  isSpeaking,
  name = "Ő",
  onTap,
}: Props) {
  return (
    <div className="self-avatar-stage">
      <button
        type="button"
        className={`self-avatar${isSpeaking ? " is-speaking" : ""}`}
        data-expression={expression}
        onClick={onTap}
        aria-label={name}
      >
        <span className="self-avatar__face">{EXPRESSION_EMOJI[expression]}</span>
        <span className="self-avatar__badge">hamarosan</span>
      </button>
    </div>
  );
}
