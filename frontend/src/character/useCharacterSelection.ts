import { useCallback, useEffect, useState } from "react";
import { CharacterId } from "./types";

const STORAGE_KEY = "fahej.character";

function readStored(): CharacterId {
  if (typeof window === "undefined") return "hedgehog";
  const v = window.localStorage.getItem(STORAGE_KEY);
  return v === "self" || v === "hedgehog" ? v : "hedgehog";
}

export function useCharacterSelection(): [CharacterId, (id: CharacterId) => void] {
  const [character, setCharacter] = useState<CharacterId>(readStored);

  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, character);
    } catch {
      /* ignore storage errors (private mode etc.) */
    }
  }, [character]);

  const set = useCallback((id: CharacterId) => setCharacter(id), []);
  return [character, set];
}
