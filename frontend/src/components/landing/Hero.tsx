import { Link } from 'react-router-dom'
import { motion } from 'motion/react'
import { buttonClasses } from '../ui/Button'
import { Container } from '../shared/Container'
import { staggerContainer, staggerChild } from '../../motion/variants'
import { ProductCard } from './ProductCard'

/**
 * Two-column hero. Copy leads on the left; the product is demonstrated on the
 * right with the analysis preview, so the visitor sees what ResumeAI does in
 * the first screenful rather than reading about it.
 */
export function Hero() {
  return (
    <section className="relative overflow-hidden border-b border-line bg-bg">
      {/* Soft, restrained backdrop glows */}
      <div aria-hidden="true" className="pointer-events-none absolute inset-0">
        <div className="absolute -top-24 right-[-12%] h-[26rem] w-[26rem] rounded-full bg-primary-faint blur-3xl" />
        <div className="absolute left-[-14%] top-40 h-[22rem] w-[22rem] rounded-full bg-primary-glow blur-3xl" />
      </div>

      <Container className="relative grid items-center gap-14 py-16 sm:py-20 lg:grid-cols-[1.02fr_0.98fr] lg:gap-16 lg:py-24">
        {/* Copy */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="max-w-xl"
        >
          <motion.p
            variants={staggerChild}
            className="flex items-center gap-3 font-mono text-xs font-medium uppercase tracking-[0.2em] text-primary"
          >
            <span aria-hidden="true" className="h-px w-6 bg-primary" />
            Career intelligence · ATS · Job matching
          </motion.p>
          <motion.h1
            variants={staggerChild}
            className="mt-5 font-display text-4xl font-bold leading-[1.08] tracking-tight text-ink sm:text-5xl lg:text-[3.4rem]"
          >
            A resume built to get <span className="text-primary">read</span>, not rejected.
          </motion.h1>
          <motion.p variants={staggerChild} className="mt-6 text-base leading-relaxed text-text-soft sm:text-lg">
            ResumeAI scores your resume the way ATS systems and recruiters do — then shows you
            what's working, what's missing, and the exact edits that move the number.
          </motion.p>
          <motion.div variants={staggerChild} className="mt-8 flex flex-wrap items-center gap-3">
            <Link to="/sign-up" className={buttonClasses('primary', 'lg')}>
              Analyze my resume
              <span aria-hidden="true">→</span>
            </Link>
            <a href="#how-it-works" className={buttonClasses('secondary', 'lg')}>
              See how it works
            </a>
          </motion.div>
          <motion.p variants={staggerChild} className="mt-6 text-sm text-muted">
            Free to try · No credit card · About 30 seconds
          </motion.p>
        </motion.div>

        {/* Product visualization */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, ease: 'easeOut', delay: 0.2 }}
          className="lg:justify-self-end"
        >
          <ProductCard />
          <p className="mt-3 text-center text-xs text-muted">
            Illustrative analysis preview — your results will differ
          </p>
        </motion.div>
      </Container>
    </section>
  )
}