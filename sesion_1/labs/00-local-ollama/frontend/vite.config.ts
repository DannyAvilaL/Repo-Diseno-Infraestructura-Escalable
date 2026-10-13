import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// El proxy evita CORS en desarrollo y mantiene el backend en 127.0.0.1.
export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: { "/v1": "http://127.0.0.1:8000", "/readyz": "http://127.0.0.1:8000" },
  },
});
