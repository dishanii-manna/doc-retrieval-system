/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        serif: ["Georgia", "Times New Roman", "serif"],
        mono:  ["Fira Code", "monospace"],
      },
      colors: {
        parchment: "#f5f0e8",
        ink:       "#1a1208",
        sepia:     "#8b6914",
      }
    }
  },
  plugins: []
}
