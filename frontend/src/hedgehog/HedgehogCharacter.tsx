import "./hedgehog.css";

type Props = {
  mood: string;
  name?: string;
  onClick?: () => void;
};

export default function HedgehogCharacter({
  mood,
  name = "Fahéj",
  onClick,
}: Props) {
  return (
    <div className="hedgehog-stage">
      <svg
        className="hedgehog-svg"
        data-mood={mood}
        viewBox="0 0 240 220"
        role="img"
        aria-label={`${name}, a süni`}
        onClick={onClick}
        onKeyDown={(e) => e.key === "Enter" && onClick?.()}
        tabIndex={onClick ? 0 : undefined}
      >
        {/* Ground shadow */}
        <ellipse cx="120" cy="200" rx="70" ry="10" fill="#e8d5c8" opacity="0.5" />

        {/* Quills back */}
        <g className="hog-quills">
          {[...Array(12)].map((_, i) => {
            const angle = -60 + i * 10;
            const rad = (angle * Math.PI) / 180;
            const x1 = 120 + Math.cos(rad) * 35;
            const y1 = 100 + Math.sin(rad) * 25;
            const x2 = 120 + Math.cos(rad) * 75;
            const y2 = 85 + Math.sin(rad) * 55;
            return (
              <line
                key={i}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke="#8b6914"
                strokeWidth="3"
                strokeLinecap="round"
              />
            );
          })}
        </g>

        {/* Body */}
        <g className="hog-body">
          <ellipse cx="120" cy="125" rx="58" ry="52" fill="#d4a574" />
          <ellipse cx="120" cy="130" rx="42" ry="38" fill="#e8c9a0" />
          {/* Belly */}
          <ellipse cx="120" cy="138" rx="28" ry="24" fill="#fff5eb" />
        </g>

        {/* Face */}
        <g className="hog-face">
          <ellipse cx="120" cy="108" rx="38" ry="32" fill="#e8c9a0" />
          {/* Cheek blush */}
          <ellipse cx="95" cy="115" rx="10" ry="6" fill="#f5c4c4" opacity="0.6" />
          <ellipse cx="145" cy="115" rx="10" ry="6" fill="#f5c4c4" opacity="0.6" />

          {/* Eyes open */}
          <g className="hog-eyes-open">
            <ellipse cx="102" cy="102" rx="7" ry="9" fill="#4a3f55" />
            <ellipse cx="138" cy="102" rx="7" ry="9" fill="#4a3f55" />
            <circle cx="104" cy="100" r="2.5" fill="#fff" />
            <circle cx="140" cy="100" r="2.5" fill="#fff" />
          </g>
          {/* Eyes sleepy */}
          <g className="hog-eyes-sleepy">
            <path
              d="M 95 104 Q 102 108 109 104"
              stroke="#4a3f55"
              strokeWidth="2.5"
              fill="none"
              strokeLinecap="round"
            />
            <path
              d="M 131 104 Q 138 108 145 104"
              stroke="#4a3f55"
              strokeWidth="2.5"
              fill="none"
              strokeLinecap="round"
            />
          </g>

          {/* Nose */}
          <g className="hog-nose">
            <ellipse cx="120" cy="118" rx="8" ry="6" fill="#4a3f55" />
            <ellipse cx="120" cy="117" rx="3" ry="2" fill="#6b5b7a" opacity="0.5" />
          </g>

          {/* Smile */}
          <path
            d="M 108 128 Q 120 136 132 128"
            stroke="#4a3f55"
            strokeWidth="2"
            fill="none"
            strokeLinecap="round"
          />
        </g>

        {/* Legs */}
        <g className="hog-legs">
          <ellipse cx="88" cy="168" rx="12" ry="8" fill="#c4956a" />
          <ellipse cx="152" cy="168" rx="12" ry="8" fill="#c4956a" />
          <ellipse cx="105" cy="172" rx="10" ry="7" fill="#c4956a" />
          <ellipse cx="135" cy="172" rx="10" ry="7" fill="#c4956a" />
        </g>

        {/* Celebrate sparkles */}
        <g className="hog-sparkles">
          <text x="50" y="60" fontSize="18">
            ✨
          </text>
          <text x="175" y="55" fontSize="16">
            ✨
          </text>
          <text x="120" y="35" fontSize="20">
            🎉
          </text>
        </g>
      </svg>
    </div>
  );
}
