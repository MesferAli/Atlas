import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { FadeInText } from "../components/AnimatedText";
import { AnimatedCounter, StatCard } from "../components/AnimatedCounter";

// Animated bar chart component
const BarChart: React.FC<{
  data: { label: string; before: number; after: number }[];
  delay: number;
}> = ({ data, delay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const adjustedFrame = Math.max(0, frame - delay);

  const maxValue = Math.max(...data.map((d) => Math.max(d.before, d.after)));

  return (
    <div
      style={{
        display: "flex",
        gap: 60,
        alignItems: "flex-end",
        height: 300,
        padding: "20px 40px",
      }}
    >
      {data.map((item, index) => {
        const itemDelay = index * 20;
        const itemFrame = Math.max(0, adjustedFrame - itemDelay);

        const beforeHeight = spring({
          frame: itemFrame,
          fps,
          config: {
            damping: 30,
            stiffness: 60,
          },
        });

        const afterHeight = spring({
          frame: Math.max(0, itemFrame - 30),
          fps,
          config: {
            damping: 25,
            stiffness: 50,
          },
        });

        const labelOpacity = interpolate(itemFrame, [0, 20], [0, 1], {
          extrapolateRight: "clamp",
        });

        return (
          <div
            key={index}
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 16,
            }}
          >
            {/* Bars container */}
            <div
              style={{
                display: "flex",
                gap: 12,
                alignItems: "flex-end",
                height: 240,
              }}
            >
              {/* Before bar */}
              <div
                style={{
                  width: 50,
                  height: (item.before / maxValue) * 200 * beforeHeight,
                  background: "rgba(255, 68, 68, 0.5)",
                  borderRadius: "8px 8px 0 0",
                  position: "relative",
                }}
              >
                <span
                  style={{
                    position: "absolute",
                    top: -30,
                    left: "50%",
                    transform: "translateX(-50%)",
                    fontFamily: "var(--font-mono)",
                    fontSize: 14,
                    color: "#FF4444",
                    opacity: beforeHeight,
                  }}
                >
                  {item.before}%
                </span>
              </div>

              {/* After bar */}
              <div
                style={{
                  width: 50,
                  height: (item.after / maxValue) * 200 * afterHeight,
                  background:
                    "linear-gradient(180deg, #47C647 0%, #32C9C5 100%)",
                  borderRadius: "8px 8px 0 0",
                  boxShadow: "0 0 20px rgba(71, 198, 71, 0.3)",
                  position: "relative",
                }}
              >
                <span
                  style={{
                    position: "absolute",
                    top: -30,
                    left: "50%",
                    transform: "translateX(-50%)",
                    fontFamily: "var(--font-mono)",
                    fontSize: 14,
                    color: "#47C647",
                    opacity: afterHeight,
                  }}
                >
                  {item.after}%
                </span>
              </div>
            </div>

            {/* Label */}
            <span
              style={{
                fontFamily: "var(--font-arabic)",
                fontSize: 16,
                color: "#9CA3AF",
                opacity: labelOpacity,
                textAlign: "center",
                maxWidth: 120,
              }}
            >
              {item.label}
            </span>
          </div>
        );
      })}
    </div>
  );
};

// Growth line chart component
const GrowthChart: React.FC<{ delay: number }> = ({ delay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const adjustedFrame = Math.max(0, frame - delay);

  const drawProgress = spring({
    frame: adjustedFrame,
    fps,
    config: {
      damping: 40,
      stiffness: 50,
      mass: 1.5,
    },
  });

  // SVG path for growth line
  const pathLength = 500;
  const strokeDashoffset = interpolate(drawProgress, [0, 1], [pathLength, 0]);

  return (
    <svg width="400" height="200" viewBox="0 0 400 200">
      <defs>
        <linearGradient id="line-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#32C9C5" />
          <stop offset="100%" stopColor="#47C647" />
        </linearGradient>
        <linearGradient id="area-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="rgba(71, 198, 71, 0.3)" />
          <stop offset="100%" stopColor="rgba(71, 198, 71, 0)" />
        </linearGradient>
      </defs>

      {/* Grid lines */}
      {[0, 1, 2, 3, 4].map((i) => (
        <line
          key={i}
          x1="0"
          y1={40 * i}
          x2="400"
          y2={40 * i}
          stroke="rgba(255, 255, 255, 0.05)"
          strokeWidth="1"
        />
      ))}

      {/* Area fill */}
      <path
        d="M 0 180 Q 100 160 150 140 T 250 100 T 350 40 L 400 20 L 400 200 L 0 200 Z"
        fill="url(#area-gradient)"
        opacity={drawProgress}
      />

      {/* Growth line */}
      <path
        d="M 0 180 Q 100 160 150 140 T 250 100 T 350 40 L 400 20"
        fill="none"
        stroke="url(#line-gradient)"
        strokeWidth="4"
        strokeLinecap="round"
        strokeDasharray={pathLength}
        strokeDashoffset={strokeDashoffset}
      />

      {/* Endpoint glow */}
      <circle
        cx="400"
        cy="20"
        r={8 * drawProgress}
        fill="#47C647"
        opacity={drawProgress}
        style={{
          filter: "drop-shadow(0 0 10px rgba(71, 198, 71, 0.8))",
        }}
      />
    </svg>
  );
};

export const ResultScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const chartData = [
    { label: "معدل الاستجابة", before: 23, after: 78 },
    { label: "إغلاق الصفقات", before: 15, after: 52 },
    { label: "رضا العملاء", before: 45, after: 92 },
  ];

  // Scene transitions
  const fadeIn = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });

  const fadeOut = interpolate(
    frame,
    [durationInFrames - 20, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#031400",
        opacity: fadeIn * fadeOut,
        direction: "rtl",
      }}
    >
      {/* Header */}
      <div
        style={{
          position: "absolute",
          top: 60,
          left: 0,
          right: 0,
          textAlign: "center",
        }}
      >
        <FadeInText
          text="نتائج حقيقية"
          fontSize={56}
          fontWeight={700}
          gradient
          delay={0}
          fontFamily="arabic"
        />
        <div style={{ height: 12 }} />
        <FadeInText
          text="من اليوم الأول"
          fontSize={32}
          fontWeight={500}
          color="#9CA3AF"
          delay={15}
          fontFamily="arabic"
        />
      </div>

      {/* Stats row */}
      <div
        style={{
          position: "absolute",
          top: 180,
          left: "50%",
          transform: "translateX(-50%)",
          display: "flex",
          gap: 40,
        }}
      >
        <StatCard value={340} suffix="%" prefix="+" label="معدل الاستجابة" delay={30} />
        <StatCard value={65} suffix="%" prefix="-" label="وقت الإغلاق" delay={50} />
        <StatCard value={24} suffix="/7" label="متابعة مستمرة" delay={70} />
      </div>

      {/* Bar chart */}
      <div
        style={{
          position: "absolute",
          bottom: 100,
          left: "50%",
          transform: "translateX(-50%)",
        }}
      >
        <BarChart data={chartData} delay={90} />
      </div>

      {/* Legend */}
      <div
        style={{
          position: "absolute",
          bottom: 40,
          left: "50%",
          transform: "translateX(-50%)",
          display: "flex",
          gap: 40,
          opacity: interpolate(frame, [120, 140], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div
            style={{
              width: 16,
              height: 16,
              borderRadius: 4,
              background: "rgba(255, 68, 68, 0.5)",
            }}
          />
          <span
            style={{
              fontFamily: "var(--font-arabic)",
              fontSize: 14,
              color: "#9CA3AF",
            }}
          >
            قبل جزّام
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div
            style={{
              width: 16,
              height: 16,
              borderRadius: 4,
              background: "linear-gradient(180deg, #47C647 0%, #32C9C5 100%)",
            }}
          />
          <span
            style={{
              fontFamily: "var(--font-arabic)",
              fontSize: 14,
              color: "#9CA3AF",
            }}
          >
            بعد جزّام
          </span>
        </div>
      </div>

      {/* Ambient glow */}
      <div
        style={{
          position: "absolute",
          top: "30%",
          left: "50%",
          width: 800,
          height: 400,
          transform: "translate(-50%, -50%)",
          background:
            "radial-gradient(ellipse, rgba(71, 198, 71, 0.1) 0%, transparent 70%)",
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};
