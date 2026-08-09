import typography from "@tailwindcss/typography";

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#14141F",
          surface: "#1B1B2A",
          raised: "#232336",
          border: "#2E2E45",
        },
        marigold: {
          DEFAULT: "#E8A33D",
          soft: "#F4C783",
          deep: "#C77F1E",
        },
        teal: {
          DEFAULT: "#2F9E8F",
          soft: "#7FC9BE",
        },
        rose: {
          DEFAULT: "#C4483A",
          soft: "#E08A7D",
        },
        parchment: "#F3EFE4",
        muted: "#A9A6BF",
      },
      fontFamily: {
        display: ["Fraunces", "serif"],
        body: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      backgroundImage: {
        jali: "radial-gradient(circle at 1px 1px, rgba(232,163,61,0.14) 1px, transparent 0)",
      },
      backgroundSize: {
        jali: "18px 18px",
      },
    },
  },
  plugins: [typography],
};
