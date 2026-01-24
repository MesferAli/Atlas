import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { XCircleLogo } from "../components/XCircleLogo";
import { FadeInText } from "../components/AnimatedText";

export const OutroScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Animations
  const fadeIn = interpolate(frame, [0, 30], [0, 1], {
    extrapolateRight: "clamp",
  });

  const logoScale = spring({
    frame,
    fps,
    config: {
      damping: 30,
      stiffness: 60,
    },
  });

  // Pulsing glow effect
  const glowPulse = 0.5 + Math.sin(frame * 0.08) * 0.2;

  // CTA button animation
  const ctaAppear = spring({
    frame: frame - 60,
    fps,
    config: {
      damping: 25,
      stiffness: 80,
    },
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#031400",
        opacity: fadeIn,
        direction: "rtl",
      }}
    >
      {/* Main content */}
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 40,
        }}
      >
        {/* Jazzaam Logo/Name */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 16,
            transform: `scale(${logoScale})`,
          }}
        >
          {/* Jazzaam Icon */}
          <div
            style={{
              width: 120,
              height: 120,
              borderRadius: 28,
              background: "linear-gradient(135deg, #47C647 0%, #32C9C5 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: `0 0 ${60 * glowPulse}px rgba(71, 198, 71, 0.5)`,
            }}
          >
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
              <path
                d="M10 25H17M53 25H60M10 31H17M53 31H60"
                stroke="#031400"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
          </div>

          {/* Arabic Name */}
          <FadeInText
            text="جزّام"
            fontSize={80}
            fontWeight={700}
            gradient
            delay={20}
            fontFamily="arabic"
          />

          {/* Tagline */}
          <FadeInText
            text="وكيل المبيعات الذكي"
            fontSize={28}
            fontWeight={500}
            color="#9CA3AF"
            delay={40}
            fontFamily="arabic"
          />
        </div>

        {/* CTA Button */}
        <div
          style={{
            marginTop: 20,
            opacity: Math.max(0, ctaAppear),
            transform: `translateY(${interpolate(Math.max(0, ctaAppear), [0, 1], [20, 0])}px)`,
          }}
        >
          <div
            style={{
              padding: "20px 48px",
              background: "linear-gradient(135deg, #47C647 0%, #32C9C5 100%)",
              borderRadius: 16,
              boxShadow: `0 0 ${40 * glowPulse}px rgba(71, 198, 71, 0.4)`,
            }}
          >
            <span
              style={{
                fontFamily: "var(--font-arabic)",
                fontSize: 24,
                fontWeight: 700,
                color: "#031400",
              }}
            >
              ابدأ الآن
            </span>
          </div>
        </div>

        {/* URL */}
        <div
          style={{
            opacity: interpolate(frame, [80, 100], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        >
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 20,
              color: "#47C647",
              letterSpacing: 1,
            }}
          >
            jazzaam.xcircle.ai
          </span>
        </div>
      </div>

      {/* XCircle Logo - Bottom */}
      <div
        style={{
          position: "absolute",
          bottom: 60,
          left: "50%",
          transform: "translateX(-50%)",
          display: "flex",
          alignItems: "center",
          gap: 16,
          opacity: interpolate(frame, [90, 110], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-arabic)",
            fontSize: 16,
            color: "#6B7280",
          }}
        >
          من عائلة
        </span>
        <XCircleLogo size={60} delay={0} />
        <span
          style={{
            fontFamily: "var(--font-english)",
            fontSize: 18,
            fontWeight: 600,
            background: "linear-gradient(135deg, #47C647 0%, #32C9C5 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
          }}
        >
          XCircle
        </span>
      </div>

      {/* Decorative elements */}
      {/* Top-left corner accent */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: 200,
          height: 200,
          background:
            "radial-gradient(circle at top left, rgba(71, 198, 71, 0.1) 0%, transparent 70%)",
        }}
      />

      {/* Bottom-right corner accent */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          right: 0,
          width: 200,
          height: 200,
          background:
            "radial-gradient(circle at bottom right, rgba(50, 201, 197, 0.1) 0%, transparent 70%)",
        }}
      />

      {/* Center glow */}
      <div
        style={{
          position: "absolute",
          top: "40%",
          left: "50%",
          width: 600,
          height: 400,
          transform: "translate(-50%, -50%)",
          background: `radial-gradient(ellipse, rgba(71, 198, 71, ${0.08 * glowPulse}) 0%, transparent 60%)`,
          pointerEvents: "none",
        }}
      />

      {/* Subtle particle effect (simulated with positioned dots) */}
      {[...Array(12)].map((_, i) => {
        const angle = (i / 12) * Math.PI * 2;
        const radius = 300 + Math.sin(frame * 0.02 + i) * 50;
        const x = Math.cos(angle + frame * 0.005) * radius;
        const y = Math.sin(angle + frame * 0.005) * radius;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              top: "50%",
              left: "50%",
              width: 4,
              height: 4,
              borderRadius: "50%",
              background: i % 2 === 0 ? "#47C647" : "#32C9C5",
              transform: `translate(${x}px, ${y}px)`,
              opacity: 0.3 + Math.sin(frame * 0.1 + i) * 0.2,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
