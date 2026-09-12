/**
 * Central API fetch wrapper — the single point of contact between
 * application code and the Django REST API.
 *
 * Handles:
 *   - Environment-aware base URL: same-origin `/api` in development (proxied
 *     to Django by the Vite dev server — no CORS), `VITE_API_URL` in
 *     production builds (no hardcoded production secrets)
 *   - JSON request / response by default; FormData body sent without setting
 *     Content-Type (the browser sets the correct multipart boundary)
 *   - JWT `Authorization: Bearer <token>` header when a token is available
 *   - Automatic single-retry on 401: refresh the access token (via the
 *     refresh token) then replay the original request once
 *   - Consistent error shape via `ApiError` (status / detail / field errors);
 *     fetch/network-level failures become a clear "Unable to reach ResumeAI"
 *     error instead of the generic "Something went wrong" fallback
 *   - A concurrency guard: if multiple requests 401 at the same time they
 *     share a single refresh promise, avoiding a refresh-token flood
 *
 * Every function in sibling modules (`auth.ts`, `resumes.ts`, …) calls
 * `apiFetch` — they never `fetch` directly.
 */

import { ApiError } from '../../types/api-error'
import { tokenStorage } from './token-storage'

// Base URL, environment-aware:
//   - Development: same-origin `/api`; the Vite dev server proxies it to the
//     Django backend (see vite.config.ts), so requests are not cross-origin
//     and there is no IPv4/IPv6 loopback ambiguity.
//   - Production build: `VITE_API_URL` is required at build time (e.g.
//     https://api.example.com/api). No production URL is hardcoded here;
//     without `VITE_API_URL` a build serves same-origin `/api`, which is
//     correct only when the SPA is hosted alongside the API.
const API_URL: string =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/+$/, '') ??
  '/api'

// Network-level failures (CORS block, refused connection, DNS error, mixed
// content) surface as a browser TypeError rather than an HTTP response. They
// must not collapse into the generic "Something went wrong" fallback, so they
// become a distinct, actionable ApiError.
const NETWORK_ERROR_MESSAGE =
  'Unable to reach ResumeAI. Please check the server connection and try again.'

function networkError(): ApiError {
  return new ApiError({
    status: null,
    detail: NETWORK_ERROR_MESSAGE,
  })
}

// ── In-flight refresh guard ────────────────────────────────────────────
// When a 401 fires, `doRefresh` runs once; subsequent 401s in the same
// burst chain onto the same promise, preventing a token flood.
let _refreshing: Promise<string | null> | null = null

async function doRefresh(): Promise<string | null> {
  const refresh = tokenStorage.getRefreshToken()
  if (!refresh) {
    tokenStorage.clear()
    return null
  }

  try {
    const res = await fetch(`${API_URL}/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    })
    if (!res.ok) {
      tokenStorage.clear()
      return null
    }
    const data = (await res.json()) as { access: string }
    tokenStorage.setAccessToken(data.access)
    return data.access
  } catch {
    tokenStorage.clear()
    return null
  }
}

// ── Error builder ──────────────────────────────────────────────────────
function buildApiError(status: number, body: unknown): ApiError {
  if (!body || typeof body !== 'object') {
    return new ApiError({ status })
  }

  const b = body as Record<string, unknown>
  let detail: string | null = null
  const fieldErrors: Record<string, string | string[]> = {}

  for (const [key, value] of Object.entries(b)) {
    if (key === 'detail' && typeof value === 'string') {
      detail = value
      continue
    }

    // DRF field-level: { field: ["msg"] } or { field: "msg" }
    if (typeof value === 'string') {
      fieldErrors[key] = value
      continue
    }
    if (Array.isArray(value)) {
      fieldErrors[key] = value.map(String)
      continue
    }
    // Nested object or non-standard shape — serialize as a last resort
    fieldErrors[key] = JSON.stringify(value)
  }

  return new ApiError({
    status,
    detail,
    fieldErrors: Object.keys(fieldErrors).length > 0 ? fieldErrors : null,
  })
}

// ── The fetch wrapper ──────────────────────────────────────────────────

interface RequestOptions extends Omit<RequestInit, 'method' | 'body' | 'headers'> {
  method?: string
  body?: unknown
  headers?: HeadersInit
}

/**
 * Make an authenticated request to the Django API.
 *
 * Returns the parsed JSON body, or `undefined` for 204 No Content.
 * Throws `ApiError` on non-2xx responses.
 */
export async function apiFetch<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { body, headers: extraHeaders, ...rest } = options

  const headers = new Headers()

  // Attach JWT when available
  const access = tokenStorage.getAccessToken()
  if (access) {
    headers.set('Authorization', `Bearer ${access}`)
  }

  // Set Content-Type; FormData is excluded so the browser can set the
  // correct multipart boundary automatically.
  const isFormData = body instanceof FormData
  if (body && !isFormData) {
    headers.set('Content-Type', 'application/json')
  }

  if (extraHeaders) {
    for (const [key, value] of new Headers(extraHeaders).entries()) {
      headers.set(key, value)
    }
  }

  // Run one request (also reused for the 401 retry below).
  const request = (): Promise<Response> =>
    fetch(`${API_URL}${path}`, {
      ...rest,
      headers,
      body: isFormData ? body : body ? JSON.stringify(body) : undefined,
    })

  let res: Response
  try {
    res = await request()
  } catch {
    // The API could not be reached at all — this is not an HTTP error.
    throw networkError()
  }

  // ── 401 single-retry with refresh ─────────────────────────────────
  if (res.status === 401 && tokenStorage.getRefreshToken()) {
    if (!_refreshing) {
      _refreshing = doRefresh().finally(() => {
        _refreshing = null
      })
    }
    const newToken = await _refreshing

    if (newToken) {
      headers.set('Authorization', `Bearer ${newToken}`)
      try {
        res = await request()
      } catch {
        throw networkError()
      }
    }
  }

  // ── Error handling ────────────────────────────────────────────────
  if (!res.ok) {
    const json = await res.json().catch(() => null)
    throw buildApiError(res.status, json)
  }

  // 204 No Content (e.g. logout)
  if (res.status === 204) return undefined as T

  return res.json() as Promise<T>
}