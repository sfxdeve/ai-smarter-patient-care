import path from "path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    // Dual-stack so sandbox IPv6 publishes ([::1]) work as well as 127.0.0.1.
    host: "::",
    port: 5173,
    strictPort: true,
    allowedHosts: true,
    hmr: {
      clientPort: 5173,
    },
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
})
