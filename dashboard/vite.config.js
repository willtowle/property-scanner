import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base must match your GitHub repo name for Pages to serve assets correctly,
// e.g. base: '/property-scanner/'  — update after you create the repo.
export default defineConfig({
  plugins: [react()],
  base: './',
})
