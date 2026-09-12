import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { LoadingState } from '../components/ui/LoadingState'

/**
 * Guards a route for authenticated users. While the initial token-hydration
 * check runs it shows a full-page loader (never a redirect, so there's no
 * flash of the sign-in page for connected users). Unauthenticated visitors
 * get redirected to /sign-in, remembering where they were headed so the
 * eventual form can send them back after logging in.
 */
export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return <LoadingState className="min-h-dvh" />
  }

  if (!user) {
    return (
      <Navigate
        to="/sign-in"
        replace
        state={{ from: `${location.pathname}${location.search}` }}
      />
    )
  }

  return <>{children}</>
}