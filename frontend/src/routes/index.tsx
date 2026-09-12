import { Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from './ProtectedRoute'
import { LandingPage } from '../pages/landing/LandingPage'
import { SignInPage } from '../pages/auth/SignInPage'
import { SignUpPage } from '../pages/auth/SignUpPage'
import { DashboardPage } from '../pages/dashboard/DashboardPage'
import { UploadPage } from '../pages/upload/UploadPage'
import { AnalysisPage } from '../pages/analysis/AnalysisPage'
import { HistoryPage } from '../pages/history/HistoryPage'
import { ProfilePage } from '../pages/profile/ProfilePage'
import { NotFoundPage } from '../pages/NotFoundPage'

/**
 * Route table. Public routes are open; the app routes are wrapped in
 * ProtectedRoute, which redirects unauthenticated visitors to /sign-in.
 */
export function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/sign-in" element={<SignInPage />} />
      <Route path="/sign-up" element={<SignUpPage />} />

      {/* Authenticated */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/upload"
        element={
          <ProtectedRoute>
            <UploadPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/analysis/:id"
        element={
          <ProtectedRoute>
            <AnalysisPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/history"
        element={
          <ProtectedRoute>
            <HistoryPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        }
      />

      <Route path="/404" element={<NotFoundPage />} />
      {/* Unknown deep links land on 404 rather than silently on the landing
          page, so a mistyped path is obvious. */}
      <Route path="*" element={<Navigate to="/404" replace />} />
    </Routes>
  )
}