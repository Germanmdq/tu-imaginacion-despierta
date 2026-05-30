/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        debug: 'violet',
        brgray: "#E3E5EE",
        brblue: "#0016EC"
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'visualizer': 'visualizer 1s ease-in-out infinite alternate',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        visualizer: {
          '0%': { transform: 'scaleY(0.2)' },
          '100%': { transform: 'scaleY(1)' },
        }
      }
    },
    fontFamily: {
      Aeonik: ["Aeonik"],
      AeonikBold: ["AeonikBold"],
      AeonikMedium : ["AeonikMedium"],
    },
  },
  plugins: [
    require('tailwindcss-3d')
  ],
};
