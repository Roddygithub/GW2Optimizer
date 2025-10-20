/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gw2: {
          gold: '#C89B3C',
          blue: '#1E3A8A',
          red: '#991B1B',
          dark: '#0F172A',
          light: '#F1F5F9',
        }
      }
    },
  },
  plugins: [],
}
