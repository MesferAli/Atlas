import React from "react";

export const GlobalStyles: React.FC = () => {
  return (
    <style>
      {`
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@200;300;400;500;600;700;800;900&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap');

        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }

        :root {
          /* XCircle Brand Colors */
          --bg-primary: #031400;
          --bg-secondary: #0A1F05;
          --accent-green: #47C647;
          --accent-teal: #32C9C5;
          --text-primary: #F5F5F5;
          --text-secondary: #9CA3AF;
          --text-muted: #6B7280;

          /* Gradient */
          --gradient-brand: linear-gradient(135deg, #47C647 0%, #32C9C5 100%);

          /* Fonts */
          --font-arabic: 'Cairo', sans-serif;
          --font-english: 'Space Grotesk', sans-serif;
          --font-mono: 'JetBrains Mono', monospace;
        }
      `}
    </style>
  );
};
