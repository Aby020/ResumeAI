import type { ElementType, ReactNode } from 'react'
import { cn } from '../../lib/utils/cn'

interface ContainerProps {
  children: ReactNode
  className?: string
  /**
   * Semantic element. Defaults to `div`; pass `section`, `header`, `footer`
   * when the container carries meaning.
   */
  as?: ElementType
}

/** Page-width wrapper with consistent responsive gutters. */
export function Container({ children, className, as: Tag = 'div' }: ContainerProps) {
  return (
    <Tag
      className={cn(
        'mx-auto w-full max-w-6xl px-4 sm:px-6 lg:px-8',
        className,
      )}
    >
      {children}
    </Tag>
  )
}