import { useEffect, useState } from 'react'

/**
 * Live `prefers-reduced-motion` media query. Used by the theme system for the
 * "reduce" preference and could drive animations elsewhere.
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false
    return window.matchMedia(query).matches
  })

  useEffect(() => {
    const mql = window.matchMedia(query)
    const onChange = (event: MediaQueryListEvent): void => setMatches(event.matches)

    // Listen, honoring the modern `addEventListener` API with a fallback
    // for older Safari that only supports the deprecated `addListener`.
    if (typeof mql.addEventListener === 'function') {
      mql.addEventListener('change', onChange)
      return () => mql.removeEventListener('change', onChange)
    }

    mql.addListener(onChange)
    return () => mql.removeListener(onChange)
  }, [query])

  return matches
}

/**
 * True when the user prefers reduced motion.
 */
export function useReducedMotion(): boolean {
  return useMediaQuery('(prefers-reduced-motion: reduce)')
}