import React from "react";
import { Composition } from "remotion";
import { JazzaamVideo, jazzaamVideoSchema } from "./Composition";

// Video configuration
const FPS = 30;
const DURATION_SECONDS = 60;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="JazzaamVideo"
        component={JazzaamVideo}
        durationInFrames={FPS * DURATION_SECONDS}
        fps={FPS}
        width={1920}
        height={1080}
        schema={jazzaamVideoSchema}
        defaultProps={{
          timing: {
            problemStart: 0,
            painStart: 8,
            solutionStart: 18,
            resultStart: 40,
            outroStart: 52,
          },
        }}
      />
    </>
  );
};
