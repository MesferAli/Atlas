import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

interface AnimatedCounterProps {
  value: number;
  suffix?: string;
  prefix?: string;
  fontSize?: number;
  color?: string;
  delay?: number;
  duration?: number;
  gradient?: boolean;
}

export const AnimatedCounter: React.FC<AnimatedCounterProps> = ({
  value,
  suffix = "",
  prefix = "",
  fontSize = 72,
  color = "var(--text-primary)",
  delay = 0,
  duration = 60,
  gradient = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const adjustedFrame = Math.max(0, frame - delay);

  // Appear animation
  const appear = spring({
    frame: adjustedFrame,
    fps,
    config: {
      damping: 30,
      stiffness: 80,
    },
  });

  // Count up animation
  const progress = interpolate(adjustedFrame, [0, duration], [0, 1], {
    extrapolateRight: "clamp",
  });

  const currentValue = Math.round(progress * value);

  const style: React.CSSProperties = {
    fontFamily: "var(--font-mono)",
    fontSize,
    fontWeight: 700,
    opacity: appear,
    transform: `scale(${appear})`,
    textAlign: "center",
    display: "inline-block",
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
    <span style={style}>
      {prefix}
      {currentValue}
      {suffix}
    </span>
  );
};

// Stat card component
interface StatCardProps {
  value: number;
  label: string;
  suffix?: string;
  prefix?: string;
  delay?: number;
}

export const StatCard: React.FC<StatCardProps> = ({
  value,
  label,
  suffix = "",
  prefix = "",
  delay = 0,
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

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 12,
        padding: 32,
        background: "rgba(255, 255, 255, 0.03)",
        borderRadius: 16,
        border: "1px solid rgba(71, 198, 71, 0.2)",
        opacity: appear,
        transform: `translateY(${interpolate(appear, [0, 1], [40, 0])}px)`,
      }}
    >
      <AnimatedCounter
        value={value}
        suffix={suffix}
        prefix={prefix}
        fontSize={56}
        delay={delay}
        gradient
      />
      <div
        style={{
          fontFamily: "var(--font-arabic)",
          fontSize: 20,
          color: "var(--text-secondary)",
        }}
      >
        {label}
      </div>
    </div>
  );
};
