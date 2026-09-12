/**
 * Auth API — thin wrappers around the Django auth endpoints.
 *
 * Register returns only a User object (no tokens), so the caller must
 * log in separately after a successful registration.
 */

import type {
  AuthTokens,
  LoginPayload,
  ProfileUpdatePayload,
  RegisterPayload,
  User,
} from '../../types/models'
import { tokenStorage } from './token-storage'
import { apiFetch } from './client'

export async function login(payload: LoginPayload): Promise<AuthTokens> {
  const tokens = await apiFetch<AuthTokens>('/auth/login/', {
    method: 'POST',
    body: payload,
  })
  tokenStorage.setTokens(tokens.access, tokens.refresh)
  return tokens
}

export async function register(payload: RegisterPayload): Promise<User> {
  return apiFetch<User>('/auth/register/', {
    method: 'POST',
    body: payload,
  })
}

export async function fetchCurrentUser(): Promise<User> {
  return apiFetch<User>('/auth/me/')
}

export async function logout(): Promise<void> {
  const refresh = tokenStorage.getRefreshToken()
  if (refresh) {
    try {
      await apiFetch<void>('/auth/logout/', {
        method: 'POST',
        body: { refresh },
      })
    } catch {
      // Logging out must never fail from the client's perspective — the
      // session ends regardless (e.g. the refresh token already expired).
    }
  }
  tokenStorage.clear()
}

export async function updateProfile(payload: ProfileUpdatePayload): Promise<User> {
  return apiFetch<User>('/profile/', {
    method: 'PATCH',
    body: payload,
  })
}