/** Short synthetic hedgehog-ish sounds when mood changes (no audio files required). */
let audioCtx: AudioContext | null = null;

function getCtx(): AudioContext | null {
  if (typeof window === "undefined") return null;
  if (!audioCtx) {
    audioCtx = new AudioContext();
  }
  return audioCtx;
}

export function playMoodSound(mood: string): void {
  const ctx = getCtx();
  if (!ctx) return;

  if (ctx.state === "suspended") {
    void ctx.resume();
  }

  const now = ctx.currentTime;
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.connect(gain);
  gain.connect(ctx.destination);

  const presets: Record<string, { freq: number; dur: number; type: OscillatorType }> = {
    idle: { freq: 180, dur: 0.08, type: "sine" },
    happy: { freq: 320, dur: 0.1, type: "triangle" },
    curious: { freq: 260, dur: 0.07, type: "sine" },
    cozy: { freq: 140, dur: 0.12, type: "sine" },
    sleepy: { freq: 110, dur: 0.15, type: "sine" },
    celebrate: { freq: 400, dur: 0.06, type: "triangle" },
    alert: { freq: 220, dur: 0.05, type: "square" },
  };

  const p = presets[mood] ?? presets.idle;
  osc.type = p.type;
  osc.frequency.setValueAtTime(p.freq, now);
  osc.frequency.exponentialRampToValueAtTime(p.freq * 0.7, now + p.dur);

  gain.gain.setValueAtTime(0.0001, now);
  gain.gain.exponentialRampToValueAtTime(0.12, now + 0.01);
  gain.gain.exponentialRampToValueAtTime(0.0001, now + p.dur);

  osc.start(now);
  osc.stop(now + p.dur + 0.02);

  // Second tiny "sniff" for movement feel
  if (mood !== "sleepy") {
    const o2 = ctx.createOscillator();
    const g2 = ctx.createGain();
    o2.connect(g2);
    g2.connect(ctx.destination);
    o2.type = "sine";
    o2.frequency.setValueAtTime(500, now + p.dur * 0.5);
    g2.gain.setValueAtTime(0.0001, now);
    g2.gain.exponentialRampToValueAtTime(0.06, now + p.dur + 0.02);
    g2.gain.exponentialRampToValueAtTime(0.0001, now + p.dur + 0.1);
    o2.start(now + p.dur * 0.4);
    o2.stop(now + p.dur + 0.12);
  }
}
