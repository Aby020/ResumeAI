/**
 * Resume API — CRUD + analysis endpoints.
 */

import type {
  Resume,
  ResumeAnalysis,
  ResumeCreatePayload,
} from '../../types/models'
import { apiFetch } from './client'

export async function listResumes(): Promise<Resume[]> {
  return apiFetch<Resume[]>('/resumes/')
}

export async function getResume(id: number): Promise<Resume> {
  return apiFetch<Resume>(`/resumes/${id}/`)
}

export async function createResume(payload: ResumeCreatePayload): Promise<Resume> {
  const formData = new FormData()
  formData.append('title', payload.title)
  formData.append('file', payload.file)
  if (payload.job_description) {
    formData.append('job_description', payload.job_description)
  }
  if (payload.job_image) {
    formData.append('job_image', payload.job_image)
  }

  return apiFetch<Resume>('/resumes/', {
    method: 'POST',
    body: formData,
  })
}

export async function deleteResume(id: number): Promise<void> {
  await apiFetch<void>(`/resumes/${id}/`, {
    method: 'DELETE',
  })
}

export async function getAnalysis(id: number): Promise<ResumeAnalysis> {
  return apiFetch<ResumeAnalysis>(`/resumes/${id}/analysis/`)
}