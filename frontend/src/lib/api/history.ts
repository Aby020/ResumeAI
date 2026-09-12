/**
 * History API — compact, newest-first list of the user's resume analyses.
 */

import type { HistoryItem } from '../../types/models'
import { apiFetch } from './client'

export async function listHistory(): Promise<HistoryItem[]> {
  return apiFetch<HistoryItem[]>('/history/')
}