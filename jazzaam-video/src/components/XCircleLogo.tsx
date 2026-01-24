import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

interface XCircleLogoProps {
  size?: number;
  delay?: number;
}

export const XCircleLogo: React.FC<XCircleLogoProps> = ({
  size = 400,
  delay = 0
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const adjustedFrame = Math.max(0, frame - delay);

  // Drawing animation progress
  const drawProgress = spring({
    frame: adjustedFrame,
    fps,
    config: {
      damping: 40,
      stiffness: 60,
      mass: 1.5,
    },
  });

  // Glow animation
  const glowIntensity = interpolate(drawProgress, [0.7, 1], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Scale animation
  const scale = spring({
    frame: adjustedFrame,
    fps,
    config: {
      damping: 25,
      stiffness: 50,
    },
  });

  // Staggered appearance for the two arms
  const leftArmOpacity = interpolate(drawProgress, [0, 0.5], [0, 1], {
    extrapolateRight: "clamp",
  });

  const rightArmOpacity = interpolate(drawProgress, [0.2, 0.7], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        width: size,
        height: size,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        transform: `scale(${scale})`,
      }}
    >
      <svg
        viewBox="0 0 300 280"
        width={size}
        height={size * 0.93}
        style={{
          filter: `drop-shadow(0 0 ${35 * glowIntensity}px rgba(71, 198, 71, 0.6))`,
        }}
      >
        <defs>
          {/* XCircle Brand Gradient - Teal (bottom) to Green (top) */}
          <linearGradient id="xcircle-gradient" x1="0%" y1="100%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#32C9C5" />
            <stop offset="50%" stopColor="#3DD66A" />
            <stop offset="100%" stopColor="#47C647" />
          </linearGradient>

          {/* Glow Filter */}
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="4" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        <g filter={glowIntensity > 0.5 ? "url(#glow)" : undefined}>
          {/*
            XCircle Logo - The X with Hook (المشعاب)
            Based on the actual brand logo:
            - Left arm: diagonal slash from top-left to bottom-right
            - Right arm: diagonal from bottom-left going up, with curved hook at top-right
          */}

          {/* Left arm of X - from top-left to bottom-right */}
          <path
            d={`
              M 22 22
              L 42 22
              L 160 160
              L 258 275
              L 238 275
              L 140 160
              Z
            `}
            fill="url(#xcircle-gradient)"
            opacity={leftArmOpacity}
          />

          {/* Right arm of X - from bottom-left going up with the iconic hook (المشعاب) */}
          <path
            d={`
              M 22 275
              L 42 275
              L 140 160
              L 225 55
              Q 245 28 270 28
              Q 295 28 295 58
              L 295 130
              L 270 130
              L 270 63
              Q 270 50 258 50
              Q 248 50 238 63
              L 160 160
              L 62 275
              Z
            `}
            fill="url(#xcircle-gradient)"
            opacity={rightArmOpacity}
          />
        </g>
      </svg>
    </div>
  );
};

// Animated version with stroke drawing effect (like hand-drawn branding mark)
export const XCircleLogoAnimated: React.FC<XCircleLogoProps> = ({
  size = 400,
  delay = 0
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const adjustedFrame = Math.max(0, frame - delay);

  // Drawing progress - smooth and deliberate
  const drawProgress = spring({
    frame: adjustedFrame,
    fps,
    config: {
      damping: 35,
      stiffness: 50,
      mass: 2,
    },
  });

  // Stroke drawing animation
  const pathLength = 1400;
  const strokeDashoffset = interpolate(drawProgress, [0, 0.75], [pathLength, 0], {
    extrapolateRight: "clamp",
  });

  // Fill appears after stroke completes
  const fillOpacity = interpolate(drawProgress, [0.7, 1], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Glow intensity
  const glowIntensity = interpolate(drawProgress, [0.8, 1], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Scale entrance
  const scale = spring({
    frame: adjustedFrame,
    fps,
    config: {
      damping: 30,
      stiffness: 60,
    },
  });

  return (
    <div
      style={{
        width: size,
        height: size,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        transform: `scale(${scale})`,
      }}
    >
      <svg
        viewBox="0 0 300 280"
        width={size}
        height={size * 0.93}
        style={{
          filter: `drop-shadow(0 0 ${40 * glowIntensity}px rgba(71, 198, 71, 0.6))`,
        }}
      >
        <defs>
          <linearGradient id="xcircle-gradient-anim" x1="0%" y1="100%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#32C9C5" />
            <stop offset="50%" stopColor="#3DD66A" />
            <stop offset="100%" stopColor="#47C647" />
          </linearGradient>

          <filter id="glow-anim" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="5" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Stroke outline - draws like a branding iron/وسم */}
        <path
          d={`
            M 32 22
            L 150 160
            L 248 275
            M 32 275
            L 150 160
            L 232 60
            Q 250 35 275 35
            Q 295 35 295 60
            L 295 130
          `}
          fill="none"
          stroke="url(#xcircle-gradient-anim)"
          strokeWidth="24"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={pathLength}
          strokeDashoffset={strokeDashoffset}
        />

        {/* Filled logo - fades in after stroke */}
        <g
          opacity={fillOpacity}
          filter={glowIntensity > 0.5 ? "url(#glow-anim)" : undefined}
        >
          {/* Left arm */}
          <path
            d={`
              M 22 22
              L 42 22
              L 160 160
              L 258 275
              L 238 275
              L 140 160
              Z
            `}
            fill="url(#xcircle-gradient-anim)"
          />

          {/* Right arm with hook */}
          <path
            d={`
              M 22 275
              L 42 275
              L 140 160
              L 225 55
              Q 245 28 270 28
              Q 295 28 295 58
              L 295 130
              L 270 130
              L 270 63
              Q 270 50 258 50
              Q 248 50 238 63
              L 160 160
              L 62 275
              Z
            `}
            fill="url(#xcircle-gradient-anim)"
          />
        </g>
      </svg>
    </div>
  );
};
