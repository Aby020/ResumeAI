/**
 * Reusable Motion variants (Motion v13).
 *
 * These are the only animation patterns the foundation exposes. They are
 * deliberately conservative — nothing "neon", nothing long — in line with the
 * Career Signal direction. The global reduced-motion kill switch lives in
 * App.tsx (`MotionConfig reducedMotion="user"`), so every pattern here
 * short-circuits to a single dissolve for users who ask for less motion —
 * no per-variant concern.
 */

import type { Variants } from 'motion/react'

/** Fade + rise. Used for blocks (cards, headings) entering a viewport. */
export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 16 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: 'easeOut' },
  },
}

/** Fade only. For elements already in layout that simply need to appear. */
export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.35, ease: 'easeOut' } },
}

/**
 * Container that staggers its children. Pair children variants with
 * `staggerChild` (or `fadeUp`) and give each child `variants={...}` with
 * `initial="hidden" whileInView="visible"`.
 */
export const staggerContainer: Variants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.08, delayChildren: 0.05 },
  },
}

/** Child of `staggerContainer` — same curve as fadeUp, no own delay. */
export const staggerChild: Variants = {
  hidden: { opacity: 0, y: 12 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, ease: 'easeOut' },
  },
}

/**
 * Route-level transition for the router (AnimatePresence keyed on location).
 * Initial/enter animate the incoming page up; exit eases the outgoing page
 * down. Keep durations short so navigation feels crisp, not slow-motion.
 */
export const pageTransition: Variants = {
  initial: { opacity: 0, y: 8 },
  enter: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3, ease: 'easeOut' },
  },
  exit: {
    opacity: 0,
    y: -8,
    transition: { duration: 0.18, ease: 'easeIn' },
  },
}

/** Subtle lift on hover — reserved for interactive cards, not buttons. */
export const hoverLift: Variants = {
  rest: { y: 0 },
  hover: { y: -2, transition: { duration: 0.18, ease: 'easeOut' } },
}