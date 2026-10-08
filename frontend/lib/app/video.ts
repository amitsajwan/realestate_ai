/** Studio client for a listing's project files: POST /uploads/videos (the walkthrough video, made into a reel) and
 * POST /uploads/brochures (the builder's PDF). */
import { API_BASE_URL } from '@/lib/config/api'
import { ApiError, parseErrorBody } from './api'
import { isFixtureMode } from './client'
import { getToken } from './session'

export const MAX_VIDEO_MB = 200

export interface UploadedVideo {
  url: string
  seconds: number
  width: number
  height: number
}

export const MAX_BROCHURE_MB = 30

export interface UploadedBrochure {
  url: string
  pages: number
}

export async function uploadVideo(file: File): Promise<UploadedVideo> {
  if (isFixtureMode()) return { url: URL.createObjectURL(file), seconds: 0, width: 0, height: 0 }
  if (file.size > MAX_VIDEO_MB * 1024 * 1024) throw new ApiError(413, `This video is too large. Keep it under ${MAX_VIDEO_MB} MB.`)
  return postFile<UploadedVideo>('/uploads/videos', file)
}

/** The builder's brochure (PDF) for a listing: 'Start marketing' reads it into pictures and the builder's claims. */
export async function uploadBrochure(file: File): Promise<UploadedBrochure> {
  if (isFixtureMode()) return { url: URL.createObjectURL(file), pages: 1 }
  if (file.size > MAX_BROCHURE_MB * 1024 * 1024) throw new ApiError(413, `This PDF is too large. Keep it under ${MAX_BROCHURE_MB} MB.`)
  return postFile<UploadedBrochure>('/uploads/brochures', file)
}

async function postFile<T>(path: string, file: File): Promise<T> {
  const form = new FormData()
  form.append('file', file)
  const headers: Record<string, string> = { Accept: 'application/json' }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  let res: Response
  try {
    res = await fetch(`${API_BASE_URL}/api/v1${path}`, { method: 'POST', headers, body: form })
  } catch {
    throw new ApiError(0, 'Cannot reach the server. Check your internet.')
  }
  const text = await res.text()
  let data: unknown = null
  try { data = text ? JSON.parse(text) : null } catch { data = null }
  if (!res.ok) throw parseErrorBody(data, res.status)
  return data as T
}
