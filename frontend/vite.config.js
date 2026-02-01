import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      'yaml': 'yaml/dist/index.js'
    }
  },
  optimizeDeps: {
    include: ['@monaco-editor/react', 'monaco-editor']
  },
  build: {
    commonjsOptions: {
      include: [/@monaco-editor/, /node_modules/]
    }
  }
})