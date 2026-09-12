import { useEffect, useState } from 'react'
import { animate, useMotionValue, useMotionValueEvent } from 'motion/react'
import { useReducedMotion } from './useReducedMotion'

/**
 * Counts from 0 → `target` once when mounted (or when the target changes).
 *
 * The primary use is the hero signal numbers, which sit on-screen at page
 * load. Below-the-fold values should reveal via their own `whileInView`
 * motion instead — a hidden count-up wastes the effect.
 *
 * Respects `prefers-reduced-motion`: the number jumps straight to `target`
 * (the global MotionConfig kill switch does not apply to imperative
 * `animate()` calls, so this guard is required).
 */
export function useCountUp(
  target: number,
  { duration = 0.7, delay = 0 }: { duration?: number; delay?: number } = {},
): number {
  const prefersReduced = useReducedMotion()
  const initial = prefersReduced ? target : 0
  const [value, setValue] = useState<number>(initial)
  const motionValue = useMotionValue(initial)

  useMotionValueEvent(motionValue, 'change', (v) => setValue(Math.round(v)))

  useEffect(() => {
    if (prefersReduced) {
      motionValue.set(target)
      return
    }
    const controls = animate(motionValue, target, {
      duration,
      delay,
      ease: 'easeOut',
    })
    return () => controls.stop()
  }, [motionValue, target, duration, delay, prefersReduced])

  return value
}