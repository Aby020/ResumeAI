import { useEffect } from 'react'

/**
 * Sets `document.title`, restored on unmount. Title format:
 * "Page · ResumeAI" (page omitted when the page name is empty).
 */
export function useDocumentTitle(page: string): void {
  useEffect(() => {
    const previous = document.title
    document.title = page ? `${page} · ResumeAI` : 'ResumeAI'
    return () => {
      document.title = previous
    }
  }, [page])
}