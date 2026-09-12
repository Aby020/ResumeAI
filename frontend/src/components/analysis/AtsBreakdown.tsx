import type { AtsBreakdown as AtsBreakdownMap } from '../../types/models'
import { Panel } from '../ui/Panel'
import { SectionLabel } from '../ui/SectionLabel'
import { ScoreBar } from '../ui/ScoreBar'

interface AtsBreakdownProps {
  breakdown: AtsBreakdownMap
}

/**
 * The ATS rubric — every category the engine scored, rendered as the linear
 * bar visualization. Categories come straight from the API payload
 * (`{ "<Category>": { score, max } }`); nothing is invented.
 */
export function AtsBreakdown({ breakdown }: AtsBreakdownProps) {
  const categories = Object.entries(breakdown)
  if (categories.length === 0) return null

  return (
    <Panel header={<SectionLabel>ATS breakdown</SectionLabel>}>
      <div className="grid gap-x-10 gap-y-6 p-6 sm:grid-cols-2 lg:p-7">
        {categories.map(([label, category]) => (
          <ScoreBar
            key={label}
            label={label}
            score={category.score}
            max={category.max}
          />
        ))}
      </div>
    </Panel>
  )
}