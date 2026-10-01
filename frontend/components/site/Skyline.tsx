import React from 'react'

const TOWERS: number[][] = [[0, 46, 70], [78, 74, 60], [146, 58, 80], [234, 92, 64], [306, 64, 72], [386, 84, 60], [454, 52, 84], [546, 78, 66], [620, 96, 62], [690, 60, 76], [774, 80, 64], [846, 66, 70]]

/** The PUNE Property skyline: dark towers with lit windows. Colours default to the brand navy + gold; agent heroes pass their preset's. */
export default function Skyline({ className = 'block h-16 w-full sm:h-20', tower = '#09152c', lit = '#f0b440' }: { className?: string; tower?: string; lit?: string }) {
  return (
    <svg viewBox="0 0 920 100" preserveAspectRatio="none" aria-hidden="true" className={className}>
      {TOWERS.map(([x, h, w], i) => (
        <g key={i}>
          <rect x={x} y={100 - h} width={w} height={h} style={{ fill: tower }} />
          {[0, 1, 2].map((r) => [0, 1].map((c) => ((i + r * 2 + c) % 3 !== 0 ? <rect key={r + '-' + c} x={x + 10 + c * 24} y={100 - h + 10 + r * 18} width="8" height="10" style={{ fill: lit }} opacity="0.85" /> : null)))}
        </g>
      ))}
    </svg>
  )
}
