import React from 'react'
import { encodeQr, qrSvgPath } from '@/lib/qr'

/** A QR code drawn as inline SVG on the server (no image file, no client JavaScript). Navy on white, with a quiet zone. */
export default function InviteQr({ value, label, className = '' }: { value: string; label: string; className?: string }) {
  const { path, size } = qrSvgPath(encodeQr(value, 'M'))
  return (
    <svg role="img" aria-label={label} data-testid="invite-qr" data-value={value} viewBox={`0 0 ${size} ${size}`}
      shapeRendering="crispEdges" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width={size} height={size} fill="#ffffff" />
      <path d={path} fill="#102340" />
    </svg>
  )
}
