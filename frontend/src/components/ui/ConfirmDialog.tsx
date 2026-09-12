import { useEffect, useId, useRef, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { Button } from './Button'
import { cn } from '../../lib/utils/cn'

interface ConfirmDialogProps {
  /** When false the dialog renders nothing (it stays mounted so focus can be restored). */
  open: boolean
  /** Heading of the dialog (becomes the accessible name). */
  title: string
  /** Supporting copy describing the consequence of the action. */
  description: ReactNode
  confirmLabel?: string
  cancelLabel?: string
  /** True while the destructive request is in flight — disables both actions. */
  busy?: boolean
  /** Non-fatal error from a failed action, shown inside the dialog. */
  error?: string | null
  onConfirm: () => void
  onCancel: () => void
}

const FOCUSABLE_SELECTOR = [
  'button:not([disabled])',
  '[href]',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(', ')

/**
 * Accessible confirmation dialog for destructive actions.
 *
 * Rendered into `document.body` via a portal so it escapes any overflowing
 * ancestor. Builds on the browser's first-class modal primitives where they
 * exist: `role="dialog"` + `aria-modal` for the semantics, manual focus
 * management for the behaviour (initial focus on the safe "Cancel" action,
 * a Tab trap inside the panel, Escape and backdrop-click to cancel — all
 * suppressed while `busy` so an in-flight delete can't be dismissed out from
 * under the handler). Focus is returned to the trigger when it closes, and the
 * body scroll is locked while it is open. Motion is intentionally plain CSS
 * transitions, so the global `prefers-reduced-motion` kill switch in
 * `index.css` collapses them to near-zero automatically.
 */
export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  busy = false,
  error = null,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const titleId = useId()
  const descId = useId()

  const panelRef = useRef<HTMLDivElement>(null)
  const cancelRef = useRef<HTMLButtonElement>(null)
  const restoreFocusRef = useRef<HTMLElement | null>(null)

  // Keep the latest callback in a ref so the keydown listener can be attached
  // once per open and still read the current onCancel. Updated in an effect —
  // never during render — so it stays lint-clean and concurrent-safe.
  const onCancelRef = useRef(onCancel)
  useEffect(() => {
    onCancelRef.current = onCancel
  }, [onCancel])

  // Capture the trigger and move focus into the dialog on open.
  useEffect(() => {
    if (!open) return
    restoreFocusRef.current = document.activeElement as HTMLElement | null
    // Prefer the safe action so Enter/Space never delete by accident.
    cancelRef.current?.focus()
  }, [open])

  // Tab trap + Escape handling while open.
  useEffect(() => {
    if (!open) return
    function handleKeyDown(event: KeyboardEvent): void {
      if (event.key === 'Escape') {
        event.preventDefault()
        onCancelRef.current()
        return
      }
      if (event.key !== 'Tab' || busy) return
      const panel = panelRef.current
      if (!panel) return
      const focusables = Array.from(
        panel.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR),
      )
      if (focusables.length === 0) return
      const first = focusables[0]
      const last = focusables[focusables.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [open, busy])

  // Lock body scroll while open; restore it on close.
  useEffect(() => {
    if (!open) return
    const previous = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = previous
    }
  }, [open])

  // Return focus to the trigger when the dialog closes.
  useEffect(() => {
    if (open) return
    restoreFocusRef.current?.focus()
    restoreFocusRef.current = null
  }, [open])

  if (!open) return null

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onMouseDown={(event) => {
        // Backdrop click cancels; clicking the panel itself never does.
        if (!busy && event.target === event.currentTarget) onCancelRef.current()
      }}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descId}
        tabIndex={-1}
        className={cn(
          'w-full max-w-md rounded-lg border border-line bg-surface p-6 shadow-lg',
          'transition-[opacity,transform] duration-fast ease-out',
        )}
      >
        <div className="flex items-start gap-4">
          <span
            aria-hidden="true"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-danger-soft text-danger"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="h-4 w-4"
            >
              <path d="M3 6h18" />
              <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
              <path d="M10 11v6" />
              <path d="M14 11v6" />
            </svg>
          </span>
          <div className="min-w-0">
            <h2 id={titleId} className="font-display text-lg font-bold tracking-tight text-ink">
              {title}
            </h2>
            <div id={descId} className="mt-1.5 text-sm leading-relaxed text-text-soft">
              {description}
            </div>
          </div>
        </div>

        {error && (
          <p
            role="alert"
            className="mt-4 rounded-md bg-danger-soft px-3 py-2 text-sm font-medium text-danger"
          >
            {error}
          </p>
        )}

        <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button
            ref={cancelRef}
            variant="secondary"
            onClick={onCancel}
            disabled={busy}
          >
            {cancelLabel}
          </Button>
          <Button variant="danger" onClick={onConfirm} loading={busy} disabled={busy}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>,
    document.body,
  )
}

