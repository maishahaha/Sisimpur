import { defineConfig } from 'vite';
import { resolve } from 'path';
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
    base: "/",
    build: {
      manifest: "manifest.json",
      outDir: resolve("./assets"),
      rollupOptions: {
        input: {
          main: resolve("./static/js/main.js")
        }
      }
    },
    plugins: [
      tailwindcss()
    ]
  })