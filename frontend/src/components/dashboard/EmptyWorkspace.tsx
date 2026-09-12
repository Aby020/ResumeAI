import { Link } from 'react-router-dom'
import { WorkspaceHeader } from '../workspace/WorkspaceHeader'
import { CareerSignal } from './CareerSignal'
import { ThreeStepGuide } from './ThreeStepGuide'
import { RecentAnalyses } from './RecentAnalyses'
import { NextBestAction } from './NextBestAction'
import { QuickActions } from './QuickActions'
import { HeroVisual } from './HeroVisual'
import { buttonClasses } from '../ui/Button'
import type { DashboardView } from '../../pages/dashboard/dashboard-view'

interface EmptyWorkspaceProps {
  /** The user's displayed name, for the personalized heading. */
  userName?: string
  /** The dashboard view model; its values drive every empty state on the page. */
  view: DashboardView
}

/**
 * The dashboard body — hero + signal row + workspace grid + quick actions.
 *
 * Every section renders from the real `DashboardView`: a first-time user sees
 * the full reference composition with honest empty states (awaiting ATS, no
 * job match, empty recent analyses) rather than a huge centered placeholder;
 * a returning user sees the same composition filling in. Nothing here
 * special-cases data — the leaf components do.
 */
export function EmptyWorkspace({ userName, view }: EmptyWorkspaceProps) {
  const name = userName || 'there'

  return (
    <div>
      {/* Hero — left editorial block, right résumé visual. */}
      <section className="grid items-center gap-x-12 gap-y-8 lg:grid-cols-12">
        <div className="lg:col-span-7">
          <WorkspaceHeader
            eyebrow="Your career intelligence workspace"
            title={
              <>
                {name}, your career potential is{' '}
                <span className="text-primary">within reach.</span>
              </>
            }
            subtitle="Upload your resume and ResumeAI will score how ATS systems and recruiters read it, match it against a target job, and show you the precise edits that move the number."
          />
          <div className="mt-6 flex flex-wrap items-center gap-4">
            <Link to="/upload" className={buttonClasses('primary', 'lg')}>
              Analyze your resume
              <span aria-hidden="true">→</span>
            </Link>
            <Link to="/history" className={buttonClasses('secondary', 'lg')}>
              View history
            </Link>
          </div>
        </div>
        <div className="lg:col-span-5">
          <HeroVisual />
        </div>
      </section>

      {/* Signal row · content grid · quick actions. */}
      <div className="mt-10 space-y-12">
        <CareerSignal view={view} />

        <div className="grid gap-6 lg:grid-cols-3">
          <ThreeStepGuide />
          <RecentAnalyses view={view} />
          <NextBestAction view={view} />
        </div>

        <QuickActions />
      </div>
    </div>
  )
}