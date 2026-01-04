/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./frontend/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Deep Space Backgrounds
        bg: {
          900: '#000212', // Deepest void
          800: '#020617', // Darker navy
          700: '#0f172a', // Slate tone
        },
        // Cosmic Accents (Aurora)
        primary: {
          300: '#64ffda', // Cyan Glow - High energy
          400: '#22d3ee', // Cyan
          500: '#06b6d4', // Cyan base
          600: '#0891b2',
        },
        secondary: {
          300: '#c084fc', // Purple Glow
          400: '#a855f7', // Purple
          500: '#9333ea', // Deep Purple
        },
        accent: {
          red: '#f43f5e',   // Error/Stop
          pink: '#ff0080',  // Cyberpunk pink
          gold: '#fbbf24',  // Warmth
        },
        glass: {
          100: 'rgba(255, 255, 255, 0.05)',
          200: 'rgba(255, 255, 255, 0.1)',
          300: 'rgba(255, 255, 255, 0.15)',
          border: 'rgba(255, 255, 255, 0.1)',
        }
      },
      fontFamily: {
        sans: ['"Inter"', 'system-ui', 'sans-serif'],
        display: ['"Outfit"', 'sans-serif'], // For Headings
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.6s ease-out forwards',
        'slide-up': 'slideUp 0.6s ease-out forwards',
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'glow': 'glow 3s ease-in-out infinite alternate',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 10px rgba(100, 255, 218, 0.2)' },
          '100%': { boxShadow: '0 0 25px rgba(100, 255, 218, 0.6)' },
        }
      },
      backgroundImage: {
        'cosmic-gradient': 'linear-gradient(to bottom right, #000212, #020617, #0f172a)',
        'aurora-text': 'linear-gradient(to right, #64ffda, #a855f7)',
        'glass-gradient': 'linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.02) 100%)',
      }
    },
  },
  plugins: [],
}

