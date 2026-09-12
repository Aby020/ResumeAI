import { useEffect, useState, type ReactNode } from 'react'
import { WorkspaceShell } from '../../components/workspace/WorkspaceShell'
import { EmptyWorkspace } from '../../components/dashboard/EmptyWorkspace'
import { LoadingState } from '../../components/ui/LoadingState'
import { ErrorState } from '../../components/ui/ErrorState'
import { useAuth } from '../../contexts/AuthContext'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { getDashboard } from '../../lib/api/dashboard'
import { ApiError } from '../../types/api-error'
import type { Dashboard } from '../../types/models'
import { analyzeDashboard } from './dashboard-view'

type LoadState = 'loading' | 'error' | 'ready'

/**
 * Career Intelligence Workspace — the authenticated dashboard.
 *
 * Every number on the page comes from `GET /api/dashboard/`; nothing is
 * invented. The workspace answers: how strong is my resume (career signal),
 * how well does it match (job match), what should I do next (next best
 * action), and what did I analyze recently. The same composition renders for
 * first-time and returning users — empty states flow from the real data.
 */
export function DashboardPage() {
  useDocumentTitle('Dashboard')
  const { user } = useAuth()

  const [data, setData] = useState<Dashboard | null>(null)
  const [loadState, setLoadState] = useState<LoadState>('loading')
  const [errorMessage, setErrorMessage] = useState('')
  // Bumped by the retry action so the fetch effect re-runs.
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let active = true
    async function run(): Promise<void> {
      try {
        const result = await getDashboard()
        if (!active) return
        setData(result)
        setLoadState('ready')
      } catch (error) {
        if (!active) return
        const message =
          error instanceof ApiError && error.message
            ? error.message
            : "We couldn't reach your career data right now."
        setErrorMessage(message)
        setLoadState('error')
      }
    }
    void run()
    return () => {
      active = false
    }
  }, [attempt])

  const name = user?.first_name?.trim() || user?.username || 'there'

  let content: ReactNode

  if (loadState === 'loading') {
    content = <LoadingState label="Reading your career signal…" className="min-h-[60vh]" />
  } else if (loadState === 'error') {
    content = (
      <ErrorState
        title="Couldn't read your career signal"
        description={errorMessage}
        onRetry={() => {
          setLoadState('loading')
          setErrorMessage('')
          setAttempt((a) => a + 1)
        }}
      />
    )
  } else if (data) {
    const view = analyzeDashboard(data)
    content = <EmptyWorkspace view={view} userName={name} />
  }

  return <WorkspaceShell>{content}</WorkspaceShell>
}