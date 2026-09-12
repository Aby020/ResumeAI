import type { InputHTMLAttributes, Ref } from 'react'
import { cn } from '../../lib/utils/cn'

interface AuthFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  /** Visible label, associated with the input via htmlFor. */
  label: string
  /** Field name — also used to build the input id. */
  name: string
  /** Field-level error message shown beneath the input. */
  error?: string
  /** Class applied to the wrapping div. */
  wrapperClassName?: string
  ref?: Ref<HTMLInputElement>
}

const inputBase =
  'h-11 w-full rounded-md border bg-surface px-3.5 font-normal text-text ' +
  'placeholder:text-muted/70 transition-[border-color,box-shadow,background-color] duration-base ease-out ' +
  'focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary ' +
  'disabled:opacity-60 disabled:cursor-not-allowed'

/**
 * Reusable form field for the authentication pages. Renders a labeled input
 * with the Career Signal surface styling and a compact error state. Valid /
 * invalid feedback is conveyed by border color plus the error message, so it
 * never depends on color alone.
 */
export function AuthField({
  label,
  name,
  error,
  wrapperClassName,
  className,
  ref,
  id,
  ...rest
}: AuthFieldProps) {
  const inputId = id ?? `auth-${name}`
  const describedBy = error ? `${inputId}-error` : undefined

  return (
    <div className={cn('flex flex-col gap-1.5', wrapperClassName)}>
      <label
        htmlFor={inputId}
        className="text-sm font-medium text-text-soft"
      >
        {label}
      </label>
      <input
        ref={ref}
        id={inputId}
        name={name}
        aria-invalid={Boolean(error)}
        aria-describedby={describedBy}
        className={cn(
          inputBase,
          error && 'border-danger focus:border-danger focus:ring-danger/25',
          className,
        )}
        {...rest}
      />
      {error && (
        <p
          id={describedBy}
          role="alert"
          className="text-sm text-danger"
        >
          {error}
        </p>
      )}
    </div>
  )
}