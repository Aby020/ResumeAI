import type { ReactNode } from 'react'
import { WorkspaceNav } from './WorkspaceNav'

interface WorkspaceShellProps {
  children: ReactNode
}

/**
 * Authenticated workspace frame — the dedicated product shell for ResumeAI's
 * dashboard experience (distinct from the simpler PageShell used by the
 * other authenticated pages).
 *
 * The shell is deliberately thin: brand rail on top, themed <main> below, and
 * the page supplies its own sections. Other authenticated pages can adopt it
 * later by swapping their page wrapper for this component.
 */
export function WorkspaceShell({ children }: WorkspaceShellProps) {
  return (
    <div className="flex min-h-dvh flex-col bg-bg text-text">
      <WorkspaceNav />
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 pb-24 pt-8 sm:px-6 lg:px-8 lg:pt-10">
        {children}
      </main>
    </div>
  )
}