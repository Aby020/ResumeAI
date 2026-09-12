import { motion } from 'motion/react'
import { Container } from '../shared/Container'
import { SectionHeader } from './SectionHeader'
import { staggerContainer, staggerChild } from '../../motion/variants'

const STEPS = [
  {
    n: '01',
    title: 'Upload your resume',
    body: 'Drop in a PDF or DOCX. ResumeAI parses structure, text and formatting in seconds.',
  },
  {
    n: '02',
    title: 'Add a job description',
    body: 'Paste the role you are targeting — matching needs a target to match against.',
  },
  {
    n: '03',
    title: 'Analyze your resume',
    body: 'Get your ATS score, job match and a full breakdown of strengths and gaps.',
  },
  {
    n: '04',
    title: 'Improve and track progress',
    body: 'Apply targeted edits, re-analyze, and watch the score climb with every version.',
  },
]

/**
 * Four-step "how it works" flow. Editorial numbered steps under a strong
 * hairline — numerals set small and ghost-like so the sequence reads, then
 * recedes behind the headline.
 */
export function HowItWorks() {
  return (
    <section id="how-it-works" className="scroll-mt-16 border-b border-line bg-bg">
      <Container className="py-16 sm:py-24 lg:py-28">
        <SectionHeader
          eyebrow="How it works"
          title="From resume to interview, in four steps."
          description="A focused flow that takes minutes the first time and seconds on every revision."
        />
        <motion.ol
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.2 }}
          className="mt-14 grid gap-9 sm:grid-cols-2 lg:grid-cols-4 lg:gap-6"
        >
          {STEPS.map((step) => (
            <motion.li
              key={step.n}
              variants={staggerChild}
              className="border-t border-line-strong pt-6"
            >
              <span className="font-display text-4xl font-bold tabular-nums tracking-tight text-primary/25">
                {step.n}
              </span>
              <h3 className="mt-3 font-display text-lg font-bold text-ink">{step.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-text-soft">{step.body}</p>
            </motion.li>
          ))}
        </motion.ol>
      </Container>
    </section>
  )
}