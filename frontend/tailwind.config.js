/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Branding is applied at runtime via CSS custom properties so each
        // tenant's theme is isolated (section 11). These map to the variables
        // set by the branding engine; defaults live in index.css.
        brand: {
          primary: "var(--brand-primary)",
          secondary: "var(--brand-secondary)",
        },
      },
    },
  },
  plugins: [],
};
