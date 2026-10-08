/** Studio client for POST /uploads/videos: one walkthrough video for a listing ('Start marketing' turns it into a reel). */
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

export async function uploadVideo(file: File): Promise<UploadedVideo> {
  if (isFixtureMode()) return { url: URL.createObjectURL(file), seconds: 0, width: 0, height: 0 }
  if (file.size > MAX_VIDEO_MB * 1024 * 1024) throw new ApiError(413, `This video is too large. Keep it under ${MAX_VIDEO_MB} MB.`)
  const form = new FormData()
  form.append('file', file)
  const headers: Record<string, string> = { Accept: 'application/json' }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  let res: Response
  try {
    res = await fetch(`${API_BASE_URL}/api/v1/uploads/videos`, { method: 'POST', headers, body: form })
  } catch {
    throw new ApiError(0, 'Cannot reach the server. Check your internet.')
  }
  const text = await res.text()
  let data: unknown = null
  try { data = text ? JSON.parse(text) : null } catch { data = null }
  if (!res.ok) throw parseErrorBody(data, res.status)
  return data as UploadedVideo
}
