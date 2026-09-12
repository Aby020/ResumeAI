/**
 * API error contract. The Django REST API returns errors in a few shapes:
 *
 *   HttpError with a code:
 *     { "detail": "Invalid username/email or password." }          → status 401/400
 *   Field-level validation:
 *     { "password": ["Password must contain at least one number."] } → status 400
 *   Non-field validation:
 *     { "non_field_errors": ["Passwords do not match."] }            → status 400
 *   DRF default for a single body-level message:
 *     { "detail": "..." }                                           → any status
 *
 * `ApiError` normalizes all of these into one shape so UI code can check
 * `status`, read `message`, and (for form fields) index into `fieldErrors`.
 */
export interface ApiFieldErrors {
  [field: string]: string[] | string
}

export class ApiError extends Error {
  readonly status: number | null
  readonly detail: string | null
  readonly fieldErrors: ApiFieldErrors | null

  constructor(options: {
    status?: number | null
    detail?: string | null
    fieldErrors?: ApiFieldErrors | null
  }) {
    const defaultMessage =
      'Something went wrong. Please try again.'
    const detail = options.detail ?? defaultMessage
    super(detail)
    this.name = 'ApiError'
    this.status = options.status ?? null
    this.detail = detail
    this.fieldErrors = options.fieldErrors ?? null
  }

  /**
   * First human-readable message, preferring a server `detail` over the first
   * field error. Used when the UI needs a single toast/banner string.
   */
  get message(): string {
    if (this.detail) return this.detail
    const first = Object.values(this.fieldErrors ?? {})[0]
    if (Array.isArray(first)) return first[0] ?? 'Something went wrong.'
    return first ?? 'Something went wrong.'
  }

  /** Convenience: does this error carry field-level validation messages? */
  hasFieldErrors(): boolean {
    return this.fieldErrors !== null
  }

  /** Messages for one field, or [] when there are none. */
  fieldMessages(field: string): string[] {
    const value = this.fieldErrors?.[field]
    if (!value) return []
    return Array.isArray(value) ? value : [value]
  }
}