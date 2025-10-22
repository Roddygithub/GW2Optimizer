/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Guild Wars 2 Official Colors
        gw2: {
          gold: '#C59A4E',
          blue: '#4A90E2',
          red: '#E74C3C',
          green: '#2ECC71',
          purple: '#9B59B6',
          orange: '#E67E22',
        },
        // Profession Colors
        profession: {
          guardian: '#72C1D9',
          warrior: '#FFD166',
          engineer: '#D09C59',
          ranger: '#8CDC82',
          thief: '#C08F95',
          elementalist: '#F68A87',
          mesmer: '#B679D5',
          necromancer: '#52A76F',
          revenant: '#D16E5A',
        },
        // Dark Theme
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        chart: {
          '1': 'hsl(var(--chart-1))',
          '2': 'hsl(var(--chart-2))',
          '3': 'hsl(var(--chart-3))',
          '4': 'hsl(var(--chart-4))',
          '5': 'hsl(var(--chart-5))',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gw2-pattern': "url('/patterns/gw2-bg.png')",
      },
      boxShadow: {
        'gw2': '0 4px 20px rgba(197, 154, 78, 0.3)',
        'glow': '0 0 20px rgba(74, 144, 226, 0.5)',
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
