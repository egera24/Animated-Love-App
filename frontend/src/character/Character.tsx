import HedgehogStage from "../hedgehog/HedgehogStage";
import SelfAvatarPlaceholder from "./SelfAvatarPlaceholder";
import { CharacterProps } from "./types";

/**
 * Stable rendering contract for the companion figure. The app talks to this
 * component only in terms of {mood, expression, isSpeaking}; swapping in a
 * proper animated figure later (Rive / 3D) means adding a new branch here
 * without touching chat, mood, or content logic.
 */
export default function Character({
  characterId,
  mood,
  expression,
  isSpeaking,
  name,
  onTap,
}: CharacterProps) {
  if (characterId === "self") {
    return (
      <SelfAvatarPlaceholder
        mood={mood}
        expression={expression}
        isSpeaking={isSpeaking}
        name={name}
        onTap={onTap}
      />
    );
  }

  return (
    <HedgehogStage
      mood={mood}
      expression={expression}
      isSpeaking={isSpeaking}
      name={name}
      onTap={onTap}
    />
  );
}
