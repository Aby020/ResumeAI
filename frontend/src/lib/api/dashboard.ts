/**
 * Dashboard API — summary metrics.
 */

import type { Dashboard } from '../../types/models'
import { apiFetch } from './client'

export async function getDashboard(): Promise<Dashboard> {
  return apiFetch<Dashboard>('/dashboard/')
}