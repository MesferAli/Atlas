import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { XCircleLogoAnimated } from "../components/XCircleLogo";
import { JazzaamLogo } from "../components/JazzaamLogo";
import { FadeInText } from "../components/AnimatedText";

// Chat message component
const ChatMessage: React.FC<{
  message: string;
  isBot: boolean;
  delay: number;
  showTyping?: boolean;
}> = ({ message, isBot, delay, showTyping = false }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const adjustedFrame = Math.max(0, frame - delay);

  const appear = spring({
    frame: adjustedFrame,
    fps,
    config: {
      damping: 25,
      stiffness: 100,
    },
  });

  // Typing animation
  const typingDots = Math.floor((frame / 10) % 4);
  const dots = ".".repeat(typingDots);

  // Character reveal for message
  const charsToShow = Math.floor(
    interpolate(adjustedFrame, [0, message.length * 2], [0, message.length], {
      extrapolateRight: "clamp",
    })
  );

  const displayMessage = message.slice(0, charsToShow);

  return (
    <div
      style={{
        display: "flex",
        justifyContent: isBot ? "flex-start" : "flex-end",
        opacity: appear,
        transform: `translateY(${interpolate(appear, [0, 1], [20, 0])}px)`,
      }}
    >
      <div
        style={{
          maxWidth: "75%",
          padding: "16px 24px",
          borderRadius: isBot ? "20px 20px 20px 4px" : "20px 20px 4px 20px",
          background: isBot
            ? "linear-gradient(135deg, rgba(71, 198, 71, 0.15) 0%, rgba(50, 201, 197, 0.15) 100%)"
            : "rgba(255, 255, 255, 0.08)",
          border: isBot
            ? "1px solid rgba(71, 198, 71, 0.3)"
            : "1px solid rgba(255, 255, 255, 0.1)",
        }}
      >
        {isBot && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              marginBottom: 8,
            }}
          >
            <div
              style={{
                width: 24,
                height: 24,
                borderRadius: 6,
                background: "linear-gradient(135deg, #47C647 0%, #32C9C5 100%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 12,
              }}
            >
              🤖
            </div>
            <span
              style={{
                fontFamily: "var(--font-arabic)",
                fontSize: 14,
                color: "#47C647",
                fontWeight: 600,
              }}
            >
              جزّام
            </span>
          </div>
        )}
        <p
          style={{
            fontFamily: "var(--font-arabic)",
            fontSize: 20,
            color: "#F5F5F5",
            margin: 0,
            lineHeight: 1.6,
            direction: "rtl",
          }}
        >
          {showTyping && charsToShow < message.length
            ? displayMessage + dots
            : displayMessage}
        </p>
      </div>
    </div>
  );
};

// Feature highlight component
const FeatureHighlight: React.FC<{
  icon: string;
  title: string;
  delay: number;
}> = ({ icon, title, delay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const adjustedFrame = Math.max(0, frame - delay);

  const appear = spring({
    frame: adjustedFrame,
    fps,
    config: {
      damping: 30,
      stiffness: 100,
    },
  });

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        padding: "12px 20px",
        background: "rgba(71, 198, 71, 0.08)",
        borderRadius: 12,
        border: "1px solid rgba(71, 198, 71, 0.2)",
        opacity: appear,
        transform: `scale(${appear})`,
      }}
    >
      <span style={{ fontSize: 24 }}>{icon}</span>
      <span
        style={{
          fontFamily: "var(--font-arabic)",
          fontSize: 16,
          color: "#F5F5F5",
          fontWeight: 500,
        }}
      >
        {title}
      </span>
    </div>
  );
};

export const SolutionScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Chat conversation
  const chatMessages = [
    {
      message: "مرحباً! لاحظت أن العميل أحمد لم يرد على عرض السعر منذ ٣ أيام.",
      isBot: true,
      delay: 60,
    },
    {
      message: "أقترح إرسال متابعة مخصصة الآن مع تذكير بالعرض الخاص.",
      isBot: true,
      delay: 120,
    },
    {
      message: "موافق، أرسل المتابعة",
      isBot: false,
      delay: 180,
    },
    {
      message: "تم إرسال المتابعة بنجاح! سأُخطرك عند الرد. ✓",
      isBot: true,
      delay: 210,
    },
  ];

  const features = [
    { icon: "🔄", title: "متابعة آلية 24/7", delay: 280 },
    { icon: "🧠", title: "فهم السياق", delay: 310 },
    { icon: "🔗", title: "ربط CRM", delay: 340 },
    { icon: "📈", title: "اقتراحات ذكية", delay: 370 },
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

  // Logo reveal (first part of scene)
  const showChat = frame > 50;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#031400",
        opacity: fadeIn * fadeOut,
        direction: "rtl",
      }}
    >
      {/* XCircle Logo reveal */}
      {!showChat && (
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
          }}
        >
          <XCircleLogoAnimated size={300} delay={0} />
        </div>
      )}

      {/* Jazzaam Introduction */}
      {showChat && (
        <>
          {/* Header with Jazzaam branding */}
          <div
            style={{
              position: "absolute",
              top: 40,
              left: 0,
              right: 0,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              gap: 16,
            }}
          >
            <FadeInText
              text="جزّام"
              fontSize={48}
              fontWeight={700}
              gradient
              delay={0}
              fontFamily="arabic"
            />
            <span
              style={{
                fontFamily: "var(--font-english)",
                fontSize: 20,
                color: "#9CA3AF",
                opacity: interpolate(frame - 50, [20, 40], [0, 1], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                }),
              }}
            >
              AI Sales Agent
            </span>
          </div>

          {/* Chat UI */}
          <div
            style={{
              position: "absolute",
              top: 140,
              left: "50%",
              transform: "translateX(-50%)",
              width: "60%",
              maxWidth: 700,
              background: "rgba(0, 0, 0, 0.3)",
              borderRadius: 24,
              padding: 32,
              border: "1px solid rgba(71, 198, 71, 0.15)",
            }}
          >
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: 20,
              }}
            >
              {chatMessages.map((msg, index) => (
                <ChatMessage
                  key={index}
                  message={msg.message}
                  isBot={msg.isBot}
                  delay={msg.delay - 50}
                  showTyping={msg.isBot}
                />
              ))}
            </div>
          </div>

          {/* Feature highlights */}
          <div
            style={{
              position: "absolute",
              bottom: 60,
              left: "50%",
              transform: "translateX(-50%)",
              display: "flex",
              flexWrap: "wrap",
              gap: 16,
              justifyContent: "center",
              maxWidth: "80%",
            }}
          >
            {features.map((feature, index) => (
              <FeatureHighlight
                key={index}
                icon={feature.icon}
                title={feature.title}
                delay={feature.delay - 50}
              />
            ))}
          </div>
        </>
      )}

      {/* Ambient glow */}
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          width: 600,
          height: 600,
          transform: "translate(-50%, -50%)",
          background:
            "radial-gradient(circle, rgba(71, 198, 71, 0.08) 0%, transparent 70%)",
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};
