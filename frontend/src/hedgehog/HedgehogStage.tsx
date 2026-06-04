import { useEffect, useRef } from "react";
import HedgehogCharacter from "./HedgehogCharacter";
import { playMoodSound } from "./hedgehogSounds";

type Props = {
  mood: string;
  name: string;
  onTap?: () => void;
};

export default function HedgehogStage({ mood, name, onTap }: Props) {
  const prevMood = useRef<string | null>(null);

  useEffect(() => {
    if (prevMood.current !== null && prevMood.current !== mood) {
      playMoodSound(mood);
    }
    prevMood.current = mood;
  }, [mood]);

  return <HedgehogCharacter mood={mood} name={name} onClick={onTap} />;
}
