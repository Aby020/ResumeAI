import { useState } from 'react'
import type { InputHTMLAttributes } from 'react'
import { cn } from '../../lib/utils/cn'

interface PasswordFieldProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  /** Visible label, associated with the input via htmlFor. */
  label: string
  /** Field name — also used to build the input id. */
  name: string
  /** Field-level error message shown beneath the input. */
  error?: string
  /** Class applied to the wrapping div. */
  wrapperClassName?: string
}

/**
 * Password field with an accessible show/hide toggle. The toggle is a real
 * button (keyboard-reachable, announced via aria-label) and switches the input
 * between `type="password"` and `type="text"`, so password managers and
 * autofill behave as expected.
 */
export function PasswordField({
  label,
  name,
  error,
  wrapperClassName,
  className,
  id,
  ...rest
}: PasswordFieldProps) {
  const [visible, setVisible] = useState(false)
  const inputId = id ?? `auth-${name}`
  const describedBy = error ? `${inputId}-error` : undefined

  return (
    <div className={cn('flex flex-col gap-1.5', wrapperClassName)}>
      <div className="flex items-center justify-between">
        <label htmlFor={inputId} className="text-sm font-medium text-text-soft">
          {label}
        </label>
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          className="text-xs font-medium text-primary transition-colors duration-base hover:text-primary-strong focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
          aria-label={visible ? 'Hide password' : 'Show password'}
          aria-pressed={visible}
        >
          {visible ? 'Hide' : 'Show'}
        </button>
      </div>
      <input
        id={inputId}
        name={name}
        type={visible ? 'text' : 'password'}
        aria-invalid={Boolean(error)}
        aria-describedby={describedBy}
        className={cn(
          'h-11 w-full rounded-md border bg-surface px-3.5 font-normal text-text',
          'placeholder:text-muted/70 transition-[border-color,box-shadow,background-color] duration-base ease-out',
          'focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary',
          'disabled:opacity-60 disabled:cursor-not-allowed',
          error && 'border-danger focus:border-danger focus:ring-danger/25',
          className,
        )}
        {...rest}
      />
      {error && (
        <p id={describedBy} role="alert" className="text-sm text-danger">
          {error}
        </p>
      )}
    </div>
  )
}