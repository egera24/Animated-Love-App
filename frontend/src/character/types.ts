export type Expression =
  | "celebrate"
  | "comfort"
  | "melancholy"
  | "happy"
  | "curious"
  | "neutral"
  | "talking";

export type CharacterId = "hedgehog" | "self";

export type CharacterProps = {
  characterId: CharacterId;
  /** Calendar/weather mood (drives placeholder animations). */
  mood: string;
  /** Semantic facial expression (used by the proper animated figure later). */
  expression: Expression;
  /** True while the character is "speaking" a reply. */
  isSpeaking?: boolean;
  name?: string;
  onTap?: () => void;
};

export const CHARACTERS: { id: CharacterId; label: string }[] = [
  { id: "hedgehog", label: "Fahéj" },
  { id: "self", label: "Ő" },
];
