import { useCallback, useState } from 'react'

/**
 * useState persisted to localStorage. Safe in private browsing (writes fail
 * silently, reads fall back to the default).
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T,
): [T, (value: T | ((prev: T) => T)) => void] {
  const [stored, setStored] = useState<T>(() => {
    try {
      const raw = window.localStorage.getItem(key)
      return raw !== null ? (JSON.parse(raw) as T) : initialValue
    } catch {
      return initialValue
    }
  })

  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      setStored((prev) => {
        const next =
          typeof value === 'function'
            ? (value as (prev: T) => T)(prev)
            : value
        try {
          window.localStorage.setItem(key, JSON.stringify(next))
        } catch {
          /* storage unavailable — state stays in memory */
        }
        return next
      })
    },
    [key],
  )

  return [stored, setValue]
}