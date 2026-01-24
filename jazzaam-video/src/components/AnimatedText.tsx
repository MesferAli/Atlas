import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

interface AnimatedTextProps {
  text: string;
  fontSize?: number;
  fontWeight?: number;
  color?: string;
  delay?: number;
  gradient?: boolean;
  direction?: "ltr" | "rtl";
  fontFamily?: "arabic" | "english" | "mono";
}

export const AnimatedText: React.FC<AnimatedTextProps> = ({
  text,
  fontSize = 48,
  fontWeight = 600,
  color = "var(--text-primary)",
  delay = 0,
  gradient = false,
  direction = "rtl",
  fontFamily = "arabic",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const adjustedFrame = Math.max(0, frame - delay);

  // Spring animation for appearance
  const appear = spring({
    frame: adjustedFrame,
    fps,
    config: {
      damping: 30,
      stiffness: 100,
    },
  });

  // Character-by-character animation
  const characters = text.split("");

  const getFontFamily = () => {
    switch (fontFamily) {
      case "arabic":
        return "var(--font-arabic)";
      case "english":
        return "var(--font-english)";
      case "mono":
        return "var(--font-mono)";
      default:
        return "var(--font-arabic)";
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: direction === "rtl" ? "row-reverse" : "row",
        flexWrap: "wrap",
        justifyContent: "center",
        gap: 2,
      }}
    >
      {characters.map((char, index) => {
        const charDelay = index * 2;
        const charAppear = spring({
          frame: Math.max(0, adjustedFrame - charDelay),
          fps,
          config: {
            damping: 20,
            stiffness: 150,
          },
        });

        const style: React.CSSProperties = {
          fontFamily: getFontFamily(),
          fontSize,
          fontWeight,
          display: "inline-block",
          opacity: charAppear,
          transform: `translateY(${interpolate(charAppear, [0, 1], [30, 0])}px)`,
        };

        if (gradient) {
          style.background = "linear-gradient(135deg, #47C647 0%, #32C9C5 100%)";
          style.WebkitBackgroundClip = "text";
          style.WebkitTextFillColor = "transparent";
          style.backgroundClip = "text";
        } else {
          style.color = color;
        }

        return (
          <span key={index} style={style}>
            {char === " " ? "\u00A0" : char}
          </span>
        );
      })}
    </div>
  );
};

// Simple fade-in text component
export const FadeInText: React.FC<AnimatedTextProps> = ({
  text,
  fontSize = 48,
  fontWeight = 600,
  color = "var(--text-primary)",
  delay = 0,
  gradient = false,
  fontFamily = "arabic",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const adjustedFrame = Math.max(0, frame - delay);

  const appear = spring({
    frame: adjustedFrame,
    fps,
    config: {
      damping: 30,
      stiffness: 80,
    },
  });

  const getFontFamily = () => {
    switch (fontFamily) {
      case "arabic":
        return "var(--font-arabic)";
      case "english":
        return "var(--font-english)";
      case "mono":
        return "var(--font-mono)";
      default:
        return "var(--font-arabic)";
    }
  };

  const style: React.CSSProperties = {
    fontFamily: getFontFamily(),
    fontSize,
    fontWeight,
    opacity: appear,
    transform: `translateY(${interpolate(appear, [0, 1], [20, 0])}px)`,
    textAlign: "center",
  };

  if (gradient) {
    style.background = "linear-gradient(135deg, #47C647 0%, #32C9C5 100%)";
    style.WebkitBackgroundClip = "text";
    style.WebkitTextFillColor = "transparent";
    style.backgroundClip = "text";
  } else {
    style.color = color;
  }

  return <div style={style}>{text}</div>;
};
