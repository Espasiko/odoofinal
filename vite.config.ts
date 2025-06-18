import { defineConfig } from 'vite';
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  define: {
    'process.env': {},
    global: 'globalThis',
  },
  server: {
    port: 3001,
    host: "0.0.0.0",
    strictPort: true,
    open: false,
    hmr: {
      overlay: false,
      clientPort: 3001,
      host: "localhost"
    },
    headers: {
      'X-Content-Type-Options': 'nosniff',
      'X-Frame-Options': 'DENY',
      'X-XSS-Protection': '1; mode=block',
      'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https: blob:; connect-src 'self' http://localhost:8069 http://localhost:8000 http://localhost:8001 http://localhost:3000 http://localhost:3001;"
    },
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false,
      },
      "/odoo": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/odoo/, '')
      },
    },
    allowedHosts: [
      "localhost",
      "3000-ishxvgs1vcbjdsxvwnkcc-72b27711.manusvm.computer",
      "3001-ishxvgs1vcbjdsxvwnkcc-72b27711.manusvm.computer"
    ]
  },
  build: {
    sourcemap: false,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }
  }
});
