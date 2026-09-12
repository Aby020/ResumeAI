import { useDocumentTitle } from '../../hooks/useDocumentTitle'
import { LandingNav } from '../../components/landing/LandingNav'
import { Hero } from '../../components/landing/Hero'
import { Capabilities } from '../../components/landing/Capabilities'
import { HowItWorks } from '../../components/landing/HowItWorks'
import { Insights } from '../../components/landing/Insights'
import { Progress } from '../../components/landing/Progress'
import { FinalCta } from '../../components/landing/FinalCta'
import { LandingFooter } from '../../components/landing/LandingFooter'

/**
 * Premium ResumeAI landing page. Editorial, data-driven, career-focused.
 * Sections alternate paper / band surfaces with a deep-teal CTA and footer.
 */
export function LandingPage() {
  useDocumentTitle('')

  return (
    <div className="flex min-h-dvh scroll-smooth flex-col bg-bg">
      <LandingNav />
      <main className="flex-1">
        <Hero />
        <Capabilities />
        <HowItWorks />
        <Insights />
        <Progress />
        <FinalCta />
      </main>
      <LandingFooter />
    </div>
  )
}