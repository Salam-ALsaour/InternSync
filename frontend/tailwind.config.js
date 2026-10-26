/** Design system tokens (Design 8.2). */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: { sans: ['"IBM Plex Sans Arabic"', "system-ui", "sans-serif"] },
      colors: {
        primary: { DEFAULT: "#1F3864", active: "#2E4D84" },
        ground: "#F4F6F9",
        line: "#DCE2EA",
        ink: { DEFAULT: "#1A2233", muted: "#566173" },
        advisory: { fg: "#9A4410", bg: "#FFF4E8" },
      },
      borderRadius: { card: "12px", ctl: "8px" },
    },
  },
  plugins: [],
};
