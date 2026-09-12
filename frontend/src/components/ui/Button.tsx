import { cn } from '../../lib/utils/cn'
import type { ButtonHTMLAttributes, Ref } from 'react'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'
export type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  /** Show an inline spinner and disable the button. */
  loading?: boolean
  /** Block-level button filling its container width. */
  fullWidth?: boolean
  /** React 19 forward style ref — lets dialogs move focus onto the button. */
  ref?: Ref<HTMLButtonElement>
}

/** Spinner used by the loading state. Also exported for reuse. */
export function Spinner({ className }: { className?: string }) {
  return (
    <svg
      className={cn('animate-spin', className)}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <circle
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
        opacity="0.25"
      />
      <path
        d="M22 12a10 10 0 0 1-10 10"
        stroke="currentColor"
        strokeWidth="4"
        strokeLinecap="round"
      />
    </svg>
  )
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    'bg-primary text-on-primary hover:bg-primary-strong active:bg-primary-active',
  secondary:
    'bg-surface text-text border border-line hover:bg-surface-3 hover:border-line-strong',
  ghost: 'text-text hover:bg-surface-3',
  danger: 'bg-danger text-on-danger hover:opacity-90 active:opacity-80',
}

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'h-8 px-3 text-sm gap-1.5',
  md: 'h-10 px-4 text-sm gap-2',
  lg: 'h-12 px-6 text-base gap-2',
}

/**
 * Shared button surface. Exported so anchors and <Link>s can wear button
 * styles (there is deliberately no polymorphic `as` on <Button>).
 */
export function buttonClasses(
  variant: ButtonVariant = 'primary',
  size: ButtonSize = 'md',
  extra?: string,
): string {
  return cn(
    'inline-flex items-center justify-center rounded-md font-medium',
    'transition-[background-color,color,border-color,opacity] duration-base ease-out',
    'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary',
    variantClasses[variant],
    sizeClasses[size],
    extra,
  )
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  fullWidth = false,
  className,
  children,
  disabled,
  type = 'button',
  ref,
  ...rest
}: ButtonProps) {
  return (
    <button
      ref={ref}
      type={type}
      className={buttonClasses(variant, size, cn(fullWidth && 'w-full', className))}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading && <Spinner className="h-4 w-4" />}
      {children}
    </button>
  )
}