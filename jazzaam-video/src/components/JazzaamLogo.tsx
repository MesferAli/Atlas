import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

interface JazzaamLogoProps {
  delay?: number;
}

export const JazzaamLogo: React.FC<JazzaamLogoProps> = ({ delay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const adjustedFrame = Math.max(0, frame - delay);

  // Animation springs
  const appear = spring({
    frame: adjustedFrame,
    fps,
    config: {
      damping: 30,
      stiffness: 100,
    },
  });

  const textAppear = spring({
    frame: adjustedFrame - 15,
    fps,
    config: {
      damping: 25,
      stiffness: 80,
    },
  });

  const glowPulse = Math.sin(frame * 0.05) * 0.3 + 0.7;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 20,
        transform: `scale(${appear})`,
        opacity: appear,
      }}
    >
      {/* Jazzaam Icon */}
      <div
        style={{
          width: 120,
          height: 120,
          borderRadius: 24,
          background: "linear-gradient(135deg, #47C647 0%, #32C9C5 100%)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: `0 0 ${40 * glowPulse}px rgba(71, 198, 71, 0.4)`,
        }}
      >
        {/* AI Brain Icon */}
        <svg width="70" height="70" viewBox="0 0 70 70" fill="none">
          <path
            d="M35 10C25 10 17 18 17 28C17 35 21 41 27 44V55C27 57 29 59 31 59H39C41 59 43 57 43 55V44C49 41 53 35 53 28C53 18 45 10 35 10Z"
            stroke="#031400"
            strokeWidth="3"
            fill="none"
          />
          <circle cx="28" cy="28" r="4" fill="#031400" />
          <circle cx="42" cy="28" r="4" fill="#031400" />
          <path
            d="M28 38C28 38 32 42 35 42C38 42 42 38 42 38"
            stroke="#031400"
            strokeWidth="3"
            strokeLinecap="round"
          />
          {/* Neural connections */}
          <path
            d="M10 25H17M53 25H60M10 31H17M53 31H60"
            stroke="#031400"
            strokeWidth="2"
            strokeLinecap="round"
          />
        </svg>
      </div>

      {/* Arabic Name */}
      <div
        style={{
          fontFamily: "var(--font-arabic)",
          fontSize: 72,
          fontWeight: 700,
          background: "linear-gradient(135deg, #47C647 0%, #32C9C5 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          backgroundClip: "text",
          opacity: textAppear,
          transform: `translateY(${interpolate(textAppear, [0, 1], [20, 0])}px)`,
        }}
      >
        جزّام
      </div>

      {/* English Subtitle */}
      <div
        style={{
          fontFamily: "var(--font-english)",
          fontSize: 24,
          fontWeight: 500,
          color: "var(--text-secondary)",
          letterSpacing: 4,
          textTransform: "uppercase",
          opacity: interpolate(textAppear, [0, 1], [0, 0.8]),
          transform: `translateY(${interpolate(textAppear, [0, 1], [10, 0])}px)`,
        }}
      >
        AI Sales Agent
      </div>
    </div>
  );
};
