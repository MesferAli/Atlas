# Jazzaam Video - SaaS Explainer

فيديو ترويجي لمنتج **جزّام** (Jazzaam) - وكيل المبيعات الذكي من XCircle

## Overview

مشروع Remotion لإنتاج فيديو SaaS Explainer بتصميم Industrial Minimalist يعكس هوية XCircle البصرية.

## Tech Stack

- **Remotion** - React-based video creation
- **TypeScript** - Type safety
- **React** - Component-based UI

## Project Structure

```
jazzaam-video/
├── src/
│   ├── index.tsx          # Entry point
│   ├── Root.tsx           # Remotion root & composition config
│   ├── Composition.tsx    # Main video composition
│   ├── components/
│   │   ├── GlobalStyles.tsx    # CSS variables & fonts
│   │   ├── XCircleLogo.tsx     # XCircle logo with animation
│   │   ├── JazzaamLogo.tsx     # Jazzaam branding
│   │   ├── AnimatedText.tsx    # Text animations
│   │   └── AnimatedCounter.tsx # Number counters
│   └── scenes/
│       ├── ProblemScene.tsx    # "87% of opportunities lost"
│       ├── PainScene.tsx       # Pain points list
│       ├── SolutionScene.tsx   # Jazzaam Chat UI demo
│       ├── ResultScene.tsx     # Bar charts & stats
│       └── OutroScene.tsx      # CTA & branding
├── public/
│   └── audio/
│       └── README.md           # Audio requirements
├── STORYBOARD.md              # Full video script
├── package.json
├── tsconfig.json
└── remotion.config.ts
```

## Setup

```bash
# Install dependencies
npm install

# Start preview
npm start

# Build video
npm run build
```

## Video Specifications

| Property | Value |
|----------|-------|
| Resolution | 1920x1080 (Full HD) |
| Frame Rate | 30 FPS |
| Duration | 60 seconds |
| Format | MP4 |

## Scene Breakdown

| Scene | Duration | Description |
|-------|----------|-------------|
| Problem | 0-8s | Lost opportunities statistics |
| Pain | 8-18s | Pain points & challenges |
| Solution | 18-40s | Jazzaam introduction & Chat UI |
| Result | 40-52s | Stats & charts |
| Outro | 52-60s | CTA & branding |

## Brand Colors

```css
--bg-primary: #031400;      /* Dark green-black background */
--accent-green: #47C647;    /* XCircle green */
--accent-teal: #32C9C5;     /* XCircle teal */
--gradient: linear-gradient(135deg, #47C647, #32C9C5);
```

## Fonts

- **Arabic:** Cairo (Google Fonts)
- **English:** Space Grotesk
- **Monospace:** JetBrains Mono

## Audio Setup

1. Add audio files to `public/audio/`:
   - `beat.mp3` - Background music
   - `pop.mp3` - UI sound effect
   - `success.mp3` - Achievement sound

2. See `public/audio/README.md` for details

## Customization

### Timing Adjustments

Edit `src/Root.tsx` to change scene timing:

```typescript
defaultProps={{
  timing: {
    problemStart: 0,
    painStart: 8,
    solutionStart: 18,
    resultStart: 40,
    outroStart: 52,
  },
}}
```

### Logo Updates

The XCircle logo is in `src/components/XCircleLogo.tsx` with SVG paths matching the brand guidelines (المشعاب design).

## Production

```bash
# Render final video
npx remotion render src/index.tsx JazzaamVideo out/jazzaam-final.mp4

# High quality render
npx remotion render src/index.tsx JazzaamVideo out/jazzaam-hq.mp4 --codec h264 --crf 18
```

## License

Proprietary - XCircle Internal Use Only

---

**Built with** Remotion + React + TypeScript

**Brand:** XCircle - "خارج الدائرة"
