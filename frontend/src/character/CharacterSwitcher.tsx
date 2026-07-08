import { CHARACTERS, CharacterId } from "./types";

type Props = {
  value: CharacterId;
  onChange: (id: CharacterId) => void;
};

export default function CharacterSwitcher({ value, onChange }: Props) {
  return (
    <div className="character-switcher" role="group" aria-label="Karakter választó">
      {CHARACTERS.map((c) => (
        <button
          key={c.id}
          type="button"
          className={value === c.id ? "active" : ""}
          onClick={() => onChange(c.id)}
          aria-pressed={value === c.id}
        >
          {c.label}
        </button>
      ))}
    </div>
  );
}
