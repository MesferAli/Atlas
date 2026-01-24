import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { FadeInText } from "../components/AnimatedText";

export const ProblemScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Falling numbers animation
  const numbers = [
    { value: "87%", x: 30, delay: 0 },
    { value: "$2.1M", x: 50, delay: 15 },
    { value: "45", x: 70, delay: 30 },
  ];

  // Scene fade out
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
        opacity: fadeOut,
        direction: "rtl",
      }}
    >
      {/* Falling lost opportunity numbers */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          overflow: "hidden",
        }}
      >
        {numbers.map((num, index) => {
          const adjustedFrame = Math.max(0, frame - num.delay);

          const yPosition = interpolate(adjustedFrame, [0, 60], [-100, 600], {
            extrapolateRight: "clamp",
          });

          const opacity = interpolate(adjustedFrame, [0, 20, 50, 70], [0, 0.8, 0.8, 0], {
            extrapolateRight: "clamp",
          });

          const blur = interpolate(adjustedFrame, [40, 70], [0, 10], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });

          return (
            <div
              key={index}
              style={{
                position: "absolute",
                left: `${num.x}%`,
                top: yPosition,
                transform: "translateX(-50%)",
                fontFamily: "var(--font-mono)",
                fontSize: 72,
                fontWeight: 700,
                color: "#FF4444",
                opacity,
                filter: `blur(${blur}px)`,
                textShadow: "0 0 30px rgba(255, 68, 68, 0.5)",
              }}
            >
              {num.value}
            </div>
          );
        })}
      </div>

      {/* Main message */}
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          textAlign: "center",
          width: "80%",
        }}
      >
        <FadeInText
          text="٨٧٪ من الفرص تضيع"
          fontSize={72}
          fontWeight={700}
          color="#F5F5F5"
          delay={45}
          fontFamily="arabic"
        />

        <div style={{ height: 24 }} />

        <FadeInText
          text="بسبب ضعف المتابعة"
          fontSize={48}
          fontWeight={500}
          color="#9CA3AF"
          delay={75}
          fontFamily="arabic"
        />
      </div>

      {/* Subtle grid background */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundImage: `
            linear-gradient(rgba(71, 198, 71, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(71, 198, 71, 0.03) 1px, transparent 1px)
          `,
          backgroundSize: "50px 50px",
          opacity: interpolate(frame, [0, 30], [0, 1], {
            extrapolateRight: "clamp",
          }),
        }}
      />
    </AbsoluteFill>
  );
};
