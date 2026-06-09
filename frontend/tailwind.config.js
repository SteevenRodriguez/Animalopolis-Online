/** @type {import('tailwindcss').Config} */
// Paleta basada en la identidad de animalopolis.vet:
// navy #1c2949 (header), azul #0c4da2 (botones/links), coral #e06138 (acentos).
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f5fc",
          100: "#dce7f8",
          200: "#b9cef0",
          300: "#8fb0e6",
          400: "#5585d0",
          500: "#2a64b8",
          600: "#0c4da2",
          700: "#0a3f86",
          800: "#093569",
        },
        accent: {
          50: "#fdf1ec",
          100: "#fadfd4",
          400: "#e87651",
          500: "#e06138",
          600: "#da5533",
          700: "#b94427",
        },
        navy: {
          DEFAULT: "#1c2949",
          light: "#2a3a61",
          dark: "#131d36",
        },
      },
      fontFamily: {
        sans: ['"Open Sans"', "Arial", "sans-serif"],
        display: ["Montserrat", "Helvetica", "Arial", "sans-serif"],
      },
    },
  },
  plugins: [],
};
