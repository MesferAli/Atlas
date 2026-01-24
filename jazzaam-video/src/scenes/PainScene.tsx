import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { FadeInText } from "../components/AnimatedText";

// Pain point item component
const PainPoint: React.FC<{
  icon: string;
  text: string;
  delay: number;
}> = ({ icon, text, delay }) => {
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

  const shake = Math.sin(frame * 0.3) * 2;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 20,
        padding: "20px 32px",
        background: "rgba(255, 68, 68, 0.08)",
        borderRadius: 12,
        border: "1px solid rgba(255, 68, 68, 0.2)",
        opacity: appear,
        transform: `translateX(${interpolate(appear, [0, 1], [50, 0])}px) translateX(${shake}px)`,
      }}
    >
      <span style={{ fontSize: 36 }}>{icon}</span>
      <span
        style={{
          fontFamily: "var(--font-arabic)",
          fontSize: 28,
          color: "#F5F5F5",
          fontWeight: 500,
        }}
      >
        {text}
      </span>
    </div>
  );
};

export const PainScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const painPoints = [
    { icon: "😓", text: "فريق المبيعات منهك من المتابعات اليدوية", delay: 15 },
    { icon: "📉", text: "العملاء ينسون بسرعة", delay: 45 },
    { icon: "💸", text: "الفرص تضيع كل يوم", delay: 75 },
    { icon: "⏰", text: "لا وقت كافي للجميع", delay: 105 },
  ];

  // Scene transition
  const fadeIn = interpolate(frame, [0, 15], [0, 1], {
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
          top: 80,
          left: 0,
          right: 0,
          textAlign: "center",
        }}
      >
        <FadeInText
          text="الواقع المؤلم"
          fontSize={56}
          fontWeight={700}
          gradient
          delay={0}
          fontFamily="arabic"
        />
      </div>

      {/* Pain points list */}
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          display: "flex",
          flexDirection: "column",
          gap: 24,
          width: "70%",
          maxWidth: 800,
        }}
      >
        {painPoints.map((point, index) => (
          <PainPoint
            key={index}
            icon={point.icon}
            text={point.text}
            delay={point.delay}
          />
        ))}
      </div>

      {/* Stress indicator - pulsing red glow */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: `radial-gradient(circle at center, transparent 30%, rgba(255, 68, 68, ${0.05 + Math.sin(frame * 0.1) * 0.03}) 100%)`,
          pointerEvents: "none",
        }}
      />

      {/* Bottom message */}
      <div
        style={{
          position: "absolute",
          bottom: 80,
          left: 0,
          right: 0,
          textAlign: "center",
        }}
      >
        <FadeInText
          text="هل هناك حل؟"
          fontSize={36}
          fontWeight={600}
          color="#9CA3AF"
          delay={150}
          fontFamily="arabic"
        />
      </div>
    </AbsoluteFill>
  );
};
