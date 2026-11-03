/**
 * Shrink a photo in the browser before upload. Agents shoot 3-8 MB phone photos; listing pages need ~1280px.
 * Resizing here keeps our storage/bandwidth cost small and makes uploads fast on mobile data.
 * Never blocks posting: any failure (unsupported format, no canvas) returns the original file.
 */
export const MAX_SIDE = 1280
export const JPEG_QUALITY = 0.72

/** Scale (w,h) down so the longer side is at most `max`; never upscales. */
export function fitWithin(w: number, h: number, max: number = MAX_SIDE): { width: number; height: number } {
  const scale = Math.min(1, max / Math.max(w, h))
  return { width: Math.max(1, Math.round(w * scale)), height: Math.max(1, Math.round(h * scale)) }
}

async function decode(file: File): Promise<{ source: CanvasImageSource; width: number; height: number; close?: () => void }> {
  if (typeof createImageBitmap === 'function') {
    const bmp = await createImageBitmap(file)
    return { source: bmp, width: bmp.width, height: bmp.height, close: () => bmp.close() }
  }
  const url = URL.createObjectURL(file)
  try {
    const img = new Image()
    img.decoding = 'async'
    img.src = url
    await img.decode()
    return { source: img, width: img.naturalWidth, height: img.naturalHeight }
  } finally {
    URL.revokeObjectURL(url)
  }
}

export async function compressImage(file: File, max: number = MAX_SIDE, quality: number = JPEG_QUALITY): Promise<File> {
  if (typeof document === 'undefined' || !file.type.startsWith('image/') || file.type === 'image/gif') return file
  try {
    const d = await decode(file)
    const { width, height } = fitWithin(d.width, d.height, max)
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const ctx = canvas.getContext('2d')
    if (!ctx) return file
    ctx.drawImage(d.source, 0, 0, width, height)
    d.close?.()
    const blob = await new Promise<Blob | null>((res) => canvas.toBlob(res, 'image/jpeg', quality))
    if (!blob || blob.size >= file.size) return file // already small: keep the original
    return new File([blob], file.name.replace(/\.[^.]+$/, '') + '.jpg', { type: 'image/jpeg', lastModified: Date.now() })
  } catch {
    return file
  }
}
