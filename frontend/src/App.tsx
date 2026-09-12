import { BrowserRouter } from 'react-router-dom'
import { MotionConfig } from 'motion/react'
import { ThemeProvider } from './contexts/ThemeContext'
import { AuthProvider } from './contexts/AuthContext'
import { AppRoutes } from './routes'

/**
 * Provider composition:
 *
 *   ThemeProvider — applies the Career Signal design tokens to <html>
 *   AuthProvider  — owns the session (tokens + current user)
 *   MotionConfig  — the animation foundation's global kill switch:
 *                   reducedMotion="user" short-circuits every animation for
 *                   users who prefer less motion (nothing per-animation
 *                   needed)
 *   BrowserRouter — client-side routing (public + protected routes)
 */
export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <MotionConfig reducedMotion="user">
          <BrowserRouter>
            <AppRoutes />
          </BrowserRouter>
        </MotionConfig>
      </AuthProvider>
    </ThemeProvider>
  )
}