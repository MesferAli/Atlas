import React from "react";
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { z } from "zod";
import { ProblemScene } from "./scenes/ProblemScene";
import { PainScene } from "./scenes/PainScene";
import { SolutionScene } from "./scenes/SolutionScene";
import { ResultScene } from "./scenes/ResultScene";
import { OutroScene } from "./scenes/OutroScene";
import { GlobalStyles } from "./components/GlobalStyles";

// Zod schema for props validation
export const jazzaamVideoSchema = z.object({
  timing: z.object({
    problemStart: z.number(),
    painStart: z.number(),
    solutionStart: z.number(),
    resultStart: z.number(),
    outroStart: z.number(),
  }),
});

type JazzaamVideoProps = z.infer<typeof jazzaamVideoSchema>;

export const JazzaamVideo: React.FC<JazzaamVideoProps> = ({ timing }) => {
  const { fps, durationInFrames } = useVideoConfig();

  // Convert seconds to frames
  const toFrames = (seconds: number) => Math.round(seconds * fps);

  const scenes = {
    problem: {
      start: toFrames(timing.problemStart),
      duration: toFrames(timing.painStart - timing.problemStart),
    },
    pain: {
      start: toFrames(timing.painStart),
      duration: toFrames(timing.solutionStart - timing.painStart),
    },
    solution: {
      start: toFrames(timing.solutionStart),
      duration: toFrames(timing.resultStart - timing.solutionStart),
    },
    result: {
      start: toFrames(timing.resultStart),
      duration: toFrames(timing.outroStart - timing.resultStart),
    },
    outro: {
      start: toFrames(timing.outroStart),
      duration: durationInFrames - toFrames(timing.outroStart),
    },
  };

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#031400",
        direction: "rtl",
      }}
    >
      <GlobalStyles />

      {/* Scene 1: Problem - The Hook */}
      <Sequence from={scenes.problem.start} durationInFrames={scenes.problem.duration}>
        <ProblemScene />
      </Sequence>

      {/* Scene 2: Pain - The Struggle */}
      <Sequence from={scenes.pain.start} durationInFrames={scenes.pain.duration}>
        <PainScene />
      </Sequence>

      {/* Scene 3: Solution - Jazzaam Appears */}
      <Sequence from={scenes.solution.start} durationInFrames={scenes.solution.duration}>
        <SolutionScene />
      </Sequence>

      {/* Scene 4: Result - The Transformation */}
      <Sequence from={scenes.result.start} durationInFrames={scenes.result.duration}>
        <ResultScene />
      </Sequence>

      {/* Scene 5: Outro - Call to Action */}
      <Sequence from={scenes.outro.start} durationInFrames={scenes.outro.duration}>
        <OutroScene />
      </Sequence>
    </AbsoluteFill>
  );
};
