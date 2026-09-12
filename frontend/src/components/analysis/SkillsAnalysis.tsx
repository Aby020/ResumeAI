import { Link } from 'react-router-dom'
import type { ReactNode } from 'react'
import type { JobMatchDetails } from '../../types/models'
import { Panel } from '../ui/Panel'
import { SectionLabel } from '../ui/SectionLabel'
import { buttonClasses } from '../ui/Button'
import { cn } from '../../lib/utils/cn'

interface SkillsAnalysisProps {
  /** True when the analysis was run against a real job description. */
  hasJobContext: boolean
  matchingSkills: string[]
  missingSkills: string[]
  extraSkills: string[]
  jobMatchDetails: JobMatchDetails
}

type ChipsTone = 'match' | 'missing' | 'extra' | 'role'

const chipsTone: Record<ChipsTone, string> = {
  match: 'border-primary/40 bg-primary-faint text-primary',
  missing: 'border-warning/40 bg-warning-soft text-warning',
  extra: 'border-line-strong bg-surface-2 text-text-soft',
  role: 'border-line-strong bg-surface-2 text-text-soft',
}

function SkillChips({ skills, tone }: { skills: string[]; tone: ChipsTone }) {
  if (skills.length === 0) {
    return <p className="text-sm text-muted">None found.</p>
  }
  return (
    <ul className="flex flex-wrap gap-1.5">
      {skills.map((skill) => (
        <li
          key={skill}
          className={cn('rounded-md border px-2 py-1 text-xs font-medium', chipsTone[tone])}
        >
          {skill}
        </li>
      ))}
    </ul>
  )
}

function SkillGroup({
  label,
  count,
  children,
}: {
  label: string
  count: number
  children: ReactNode
}) {
  return (
    <div>
      <p className="font-mono text-xs uppercase tracking-[0.2em] text-muted">
        {label}
        <span className="ml-2 tabular-nums text-primary">{count}</span>
      </p>
      <div className="mt-3">{children}</div>
    </div>
  )
}

/**
 * Skills analysis — two clearly-differentiated groups (matching / missing)
 * plus the extra skills on the resume. Deeper role-requirement detail from
 * `job_match_details` appears as a secondary block only when a job
 * description exists — no JD means an honest empty state, never invented
 * missing skills.
 */
export function SkillsAnalysis({
  hasJobContext,
  matchingSkills,
  missingSkills,
  extraSkills,
  jobMatchDetails,
}: SkillsAnalysisProps) {
  const requirementRows: { label: string; items: string[] }[] = [
    { label: 'Required skills', items: jobMatchDetails.missing_required_skills },
    { label: 'Preferred skills', items: jobMatchDetails.missing_preferred_skills },
    { label: 'Experience', items: jobMatchDetails.missing_experience },
    { label: 'Certifications', items: jobMatchDetails.missing_certifications },
    { label: 'Technologies', items: jobMatchDetails.missing_technologies },
  ].filter((row) => row.items.length > 0)

  if (!hasJobContext) {
    return (
      <Panel header={<SectionLabel>Skills analysis</SectionLabel>}>
        <div className="flex flex-col items-start gap-5 p-6 lg:flex-row lg:items-center lg:justify-between lg:p-7">
          <div>
            <p className="font-display text-lg font-semibold text-ink">
              Add a job description to compare skills
            </p>
            <p className="mt-1 max-w-md text-sm leading-relaxed text-muted">
              Matching and missing skills are computed against a target role. Upload your
              resume with a job description to unlock this analysis.
            </p>
          </div>
          <Link to="/upload" className={buttonClasses('secondary', 'md', 'shrink-0')}>
            Upload with a job description
            <span aria-hidden="true">→</span>
          </Link>
        </div>
      </Panel>
    )
  }

  return (
    <Panel header={<SectionLabel>Skills analysis</SectionLabel>}>
      <div className="space-y-8 p-6 lg:p-7">
        <div className="grid gap-8 md:grid-cols-2">
          <SkillGroup label="Matching skills" count={matchingSkills.length}>
            <SkillChips skills={matchingSkills} tone="match" />
          </SkillGroup>
          <SkillGroup label="Missing skills" count={missingSkills.length}>
            <SkillChips skills={missingSkills} tone="missing" />
          </SkillGroup>
        </div>

        {requirementRows.length > 0 && (
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.2em] text-muted">
              Role requirements you&rsquo;re missing
            </p>
            <div className="mt-4 grid gap-6 md:grid-cols-2">
              {requirementRows.map((row) => (
                <SkillGroup key={row.label} label={row.label} count={row.items.length}>
                  <SkillChips skills={row.items} tone="role" />
                </SkillGroup>
              ))}
            </div>
          </div>
        )}

        <SkillGroup label="Extra skills" count={extraSkills.length}>
          <SkillChips skills={extraSkills} tone="extra" />
        </SkillGroup>
      </div>
    </Panel>
  )
}