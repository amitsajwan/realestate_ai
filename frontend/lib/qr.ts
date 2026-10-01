/**
 * Tiny QR code encoder (byte mode, versions 1 to 40, all four error-correction levels), pure TypeScript, no dependencies.
 * Follows ISO/IEC 18004 and the structure of Project Nayuki's reference encoder (MIT). Used to draw the invite QR code on
 * /for-agents as inline SVG at render time, so a change of site address is one setting (NEXT_PUBLIC_SITE_URL).
 */

export type Ecc = 'L' | 'M' | 'Q' | 'H'

const ECC_ORDINAL: Record<Ecc, number> = { L: 0, M: 1, Q: 2, H: 3 }
const ECC_FORMAT_BITS: Record<Ecc, number> = { L: 1, M: 0, Q: 3, H: 2 }

// Index 0 is padding; [ecc][version]
const ECC_CODEWORDS_PER_BLOCK = [
  [-1, 7, 10, 15, 20, 26, 18, 20, 24, 30, 18, 20, 24, 26, 30, 22, 24, 28, 30, 28, 28, 28, 28, 30, 30, 26, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30],
  [-1, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26, 30, 22, 22, 24, 24, 28, 28, 26, 26, 26, 26, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28],
  [-1, 13, 22, 18, 26, 18, 24, 18, 22, 20, 24, 28, 26, 24, 20, 30, 24, 28, 28, 26, 30, 28, 30, 30, 30, 30, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30],
  [-1, 17, 28, 22, 16, 22, 28, 26, 26, 24, 28, 24, 28, 22, 24, 24, 30, 28, 28, 26, 28, 30, 24, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30],
]
const NUM_ERROR_CORRECTION_BLOCKS = [
  [-1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 4, 4, 4, 4, 4, 6, 6, 6, 6, 7, 8, 8, 9, 9, 10, 12, 12, 12, 13, 14, 15, 16, 17, 18, 19, 19, 20, 21, 22, 24, 25],
  [-1, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5, 5, 8, 9, 9, 10, 10, 11, 13, 14, 16, 17, 17, 18, 20, 21, 23, 25, 26, 28, 29, 31, 33, 35, 37, 38, 40, 43, 45, 47, 49],
  [-1, 1, 1, 2, 2, 4, 4, 6, 6, 8, 8, 8, 10, 12, 16, 12, 17, 16, 18, 21, 20, 23, 23, 25, 27, 29, 34, 34, 35, 38, 40, 43, 45, 48, 51, 53, 56, 59, 62, 65, 68],
  [-1, 1, 1, 2, 4, 4, 4, 5, 6, 8, 8, 11, 11, 16, 16, 18, 16, 19, 21, 25, 25, 25, 34, 30, 32, 35, 37, 40, 42, 45, 48, 51, 54, 57, 60, 63, 66, 70, 74, 77, 81],
]

function numRawDataModules(ver: number): number {
  let result = (16 * ver + 128) * ver + 64
  if (ver >= 2) {
    const numAlign = Math.floor(ver / 7) + 2
    result -= (25 * numAlign - 10) * numAlign - 55
    if (ver >= 7) result -= 36
  }
  return result
}

const numDataCodewords = (ver: number, ecc: Ecc): number =>
  Math.floor(numRawDataModules(ver) / 8) - ECC_CODEWORDS_PER_BLOCK[ECC_ORDINAL[ecc]][ver] * NUM_ERROR_CORRECTION_BLOCKS[ECC_ORDINAL[ecc]][ver]

// ---- Reed-Solomon over GF(2^8 / 0x11D) ----
function rsMultiply(x: number, y: number): number {
  let z = 0
  for (let i = 7; i >= 0; i--) {
    z = (z << 1) ^ ((z >>> 7) * 0x11d)
    z ^= ((y >>> i) & 1) * x
  }
  return z & 0xff
}

function rsDivisor(degree: number): number[] {
  const result: number[] = new Array(degree - 1).fill(0).concat([1])
  let root = 1
  for (let i = 0; i < degree; i++) {
    for (let j = 0; j < result.length; j++) {
      result[j] = rsMultiply(result[j], root)
      if (j + 1 < result.length) result[j] ^= result[j + 1]
    }
    root = rsMultiply(root, 0x02)
  }
  return result
}

function rsRemainder(data: number[], divisor: number[]): number[] {
  const result = divisor.map(() => 0)
  for (const b of data) {
    const factor = b ^ (result.shift() as number)
    result.push(0)
    divisor.forEach((coef, i) => (result[i] ^= rsMultiply(coef, factor)))
  }
  return result
}

function utf8Bytes(s: string): number[] {
  const out: number[] = []
  const enc = encodeURI(s)
  for (let i = 0; i < enc.length; i++) {
    if (enc[i] === '%') {
      out.push(parseInt(enc.substring(i + 1, i + 3), 16))
      i += 2
    } else out.push(enc.charCodeAt(i))
  }
  return out
}

/** Encode text as a QR code. Returns a square matrix, true = dark module. */
export function encodeQr(text: string, ecc: Ecc = 'M'): boolean[][] {
  const data = utf8Bytes(text)
  let ver = 1
  for (; ; ver++) {
    if (ver > 40) throw new Error('Text too long for a QR code')
    const ccBits = ver <= 9 ? 8 : 16
    if (4 + ccBits + data.length * 8 <= numDataCodewords(ver, ecc) * 8) break
  }
  // Bit stream: mode 0100 (byte), count, data, terminator, padding
  const bits: number[] = []
  const append = (val: number, len: number) => {
    for (let i = len - 1; i >= 0; i--) bits.push((val >>> i) & 1)
  }
  append(0x4, 4)
  append(data.length, ver <= 9 ? 8 : 16)
  data.forEach((b) => append(b, 8))
  const capacity = numDataCodewords(ver, ecc) * 8
  append(0, Math.min(4, capacity - bits.length))
  append(0, (8 - (bits.length % 8)) % 8)
  for (let pad = 0xec; bits.length < capacity; pad ^= 0xec ^ 0x11) append(pad, 8)
  const codewords: number[] = []
  for (let i = 0; i < bits.length; i += 8) codewords.push(bits.slice(i, i + 8).reduce((a, b) => (a << 1) | b, 0))

  // Split into blocks, add ECC, interleave
  const o = ECC_ORDINAL[ecc]
  const numBlocks = NUM_ERROR_CORRECTION_BLOCKS[o][ver]
  const blockEccLen = ECC_CODEWORDS_PER_BLOCK[o][ver]
  const rawCodewords = Math.floor(numRawDataModules(ver) / 8)
  const numShortBlocks = numBlocks - (rawCodewords % numBlocks)
  const shortBlockLen = Math.floor(rawCodewords / numBlocks)
  const blocks: number[][] = []
  const divisor = rsDivisor(blockEccLen)
  for (let i = 0, k = 0; i < numBlocks; i++) {
    const dat = codewords.slice(k, k + shortBlockLen - blockEccLen + (i < numShortBlocks ? 0 : 1))
    k += dat.length
    const eccBytes = rsRemainder(dat, divisor)
    if (i < numShortBlocks) dat.push(0)
    blocks.push(dat.concat(eccBytes))
  }
  const all: number[] = []
  for (let i = 0; i < blocks[0].length; i++) {
    blocks.forEach((block, j) => {
      if (i !== shortBlockLen - blockEccLen || j >= numShortBlocks) all.push(block[i])
    })
  }

  // Function patterns
  const size = ver * 4 + 17
  const modules: boolean[][] = Array.from({ length: size }, () => new Array(size).fill(false))
  const isFn: boolean[][] = Array.from({ length: size }, () => new Array(size).fill(false))
  const set = (x: number, y: number, dark: boolean) => {
    modules[y][x] = dark
    isFn[y][x] = true
  }
  for (let i = 0; i < size; i++) {
    set(6, i, i % 2 === 0)
    set(i, 6, i % 2 === 0)
  }
  const finder = (x: number, y: number) => {
    for (let dy = -4; dy <= 4; dy++)
      for (let dx = -4; dx <= 4; dx++) {
        const dist = Math.max(Math.abs(dx), Math.abs(dy))
        const xx = x + dx
        const yy = y + dy
        if (xx >= 0 && xx < size && yy >= 0 && yy < size) set(xx, yy, dist !== 2 && dist !== 4)
      }
  }
  finder(3, 3)
  finder(size - 4, 3)
  finder(3, size - 4)
  const alignPos: number[] = []
  if (ver > 1) {
    const numAlign = Math.floor(ver / 7) + 2
    const step = ver === 32 ? 26 : Math.ceil((ver * 4 + 4) / (numAlign * 2 - 2)) * 2
    alignPos.push(6)
    for (let pos = size - 7; alignPos.length < numAlign; pos -= step) alignPos.splice(1, 0, pos)
  }
  const n = alignPos.length
  for (let i = 0; i < n; i++)
    for (let j = 0; j < n; j++) {
      if ((i === 0 && j === 0) || (i === 0 && j === n - 1) || (i === n - 1 && j === 0)) continue
      for (let dy = -2; dy <= 2; dy++)
        for (let dx = -2; dx <= 2; dx++) set(alignPos[i] + dx, alignPos[j] + dy, Math.max(Math.abs(dx), Math.abs(dy)) !== 1)
    }
  const drawFormat = (mask: number) => {
    const d = (ECC_FORMAT_BITS[ecc] << 3) | mask
    let rem = d
    for (let i = 0; i < 10; i++) rem = (rem << 1) ^ ((rem >>> 9) * 0x537)
    const b = ((d << 10) | rem) ^ 0x5412
    const bit = (i: number) => ((b >>> i) & 1) !== 0
    for (let i = 0; i <= 5; i++) set(8, i, bit(i))
    set(8, 7, bit(6))
    set(8, 8, bit(7))
    set(7, 8, bit(8))
    for (let i = 9; i < 15; i++) set(14 - i, 8, bit(i))
    for (let i = 0; i < 8; i++) set(size - 1 - i, 8, bit(i))
    for (let i = 8; i < 15; i++) set(8, size - 15 + i, bit(i))
    set(8, size - 8, true)
  }
  drawFormat(0) // reserve the areas; redrawn after masking
  if (ver >= 7) {
    let rem = ver
    for (let i = 0; i < 12; i++) rem = (rem << 1) ^ ((rem >>> 11) * 0x1f25)
    const b = (ver << 12) | rem
    for (let i = 0; i < 18; i++) {
      const dark = ((b >>> i) & 1) !== 0
      const a = size - 11 + (i % 3)
      const c = Math.floor(i / 3)
      set(a, c, dark)
      set(c, a, dark)
    }
  }

  // Data, zigzag
  let i = 0
  for (let right = size - 1; right >= 1; right -= 2) {
    if (right === 6) right = 5
    for (let vert = 0; vert < size; vert++)
      for (let j = 0; j < 2; j++) {
        const x = right - j
        const upward = ((right + 1) & 2) === 0
        const y = upward ? size - 1 - vert : vert
        if (!isFn[y][x] && i < all.length * 8) {
          modules[y][x] = ((all[i >>> 3] >>> (7 - (i & 7))) & 1) !== 0
          i++
        }
      }
  }

  const applyMask = (mask: number) => {
    for (let y = 0; y < size; y++)
      for (let x = 0; x < size; x++) {
        let invert: boolean
        switch (mask) {
          case 0: invert = (x + y) % 2 === 0; break
          case 1: invert = y % 2 === 0; break
          case 2: invert = x % 3 === 0; break
          case 3: invert = (x + y) % 3 === 0; break
          case 4: invert = (Math.floor(x / 3) + Math.floor(y / 2)) % 2 === 0; break
          case 5: invert = ((x * y) % 2) + ((x * y) % 3) === 0; break
          case 6: invert = (((x * y) % 2) + ((x * y) % 3)) % 2 === 0; break
          default: invert = (((x + y) % 2) + ((x * y) % 3)) % 2 === 0
        }
        if (!isFn[y][x] && invert) modules[y][x] = !modules[y][x]
      }
  }

  const penalty = (): number => {
    let result = 0
    const runPenalty = (line: boolean[]) => {
      let p = 0
      let runColor = false
      let runLen = 0
      const history = [0, 0, 0, 0, 0, 0, 0]
      const addHistory = (len: number) => {
        if (history[0] === 0) len += size
        history.pop()
        history.unshift(len)
      }
      const countPatterns = (): number => {
        const k = history[1]
        const core = k > 0 && history[2] === k && history[3] === k * 3 && history[4] === k && history[5] === k
        return (core && history[0] >= k * 4 && history[6] >= k ? 1 : 0) + (core && history[6] >= k * 4 && history[0] >= k ? 1 : 0)
      }
      for (const c of line) {
        if (c === runColor) {
          runLen++
          if (runLen === 5) p += 3
          else if (runLen > 5) p++
        } else {
          addHistory(runLen)
          if (!runColor) p += countPatterns() * 40
          runColor = c
          runLen = 1
        }
      }
      // terminate
      if (runColor) {
        addHistory(runLen)
        runLen = 0
      }
      runLen += size
      addHistory(runLen)
      p += countPatterns() * 40
      return p
    }
    for (let y = 0; y < size; y++) result += runPenalty(modules[y])
    for (let x = 0; x < size; x++) result += runPenalty(modules.map((row) => row[x]))
    for (let y = 0; y < size - 1; y++)
      for (let x = 0; x < size - 1; x++) {
        const c = modules[y][x]
        if (c === modules[y][x + 1] && c === modules[y + 1][x] && c === modules[y + 1][x + 1]) result += 3
      }
    const dark = modules.reduce((s, row) => s + row.filter(Boolean).length, 0)
    const total = size * size
    const k = Math.ceil(Math.abs(dark * 20 - total * 10) / total) - 1
    return result + k * 10
  }

  let best = 0
  let minPenalty = Infinity
  for (let m = 0; m < 8; m++) {
    applyMask(m)
    drawFormat(m)
    const p = penalty()
    if (p < minPenalty) {
      best = m
      minPenalty = p
    }
    applyMask(m) // undo (XOR)
  }
  applyMask(best)
  drawFormat(best)
  return modules
}

/** The QR code as one SVG path (1 unit per module, `quiet` modules of white border). */
export function qrSvgPath(matrix: boolean[][], quiet = 4): { path: string; size: number } {
  const parts: string[] = []
  matrix.forEach((row, y) =>
    row.forEach((dark, x) => {
      if (dark) parts.push(`M${x + quiet} ${y + quiet}h1v1h-1z`)
    }),
  )
  return { path: parts.join(''), size: matrix.length + quiet * 2 }
}
