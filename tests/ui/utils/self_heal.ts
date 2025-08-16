import type { Page, Locator } from '@playwright/test';
import fs from 'fs';
import path from 'path';

export type Candidate =
  | { description: string; css: string }
  | { description: string; role: string; name: string | RegExp }
  | { description: string; text: string };

function toLocator(page: Page, c: Candidate): Locator {
  if ('css' in c) return page.locator(c.css).first();
  if ('role' in c) return page.getByRole(c.role as any, { name: c.name as any }).first();
  // text selector fallback
  return page.locator(`text=${c.text}`).first();
}

async function isVisible(locator: Locator): Promise<boolean> {
  try {
    await locator.waitFor({ state: 'visible', timeout: 1500 });
    return true;
  } catch {
    return false;
  }
}

function writeSuggestion(entry: any) {
  try {
    const outDir = path.join(process.cwd(), 'test_reports');
    const outFile = path.join(outDir, 'self_heal_suggestions.json');
    if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
    const prev = fs.existsSync(outFile) ? JSON.parse(fs.readFileSync(outFile, 'utf8')) : [];
    prev.push({ time: new Date().toISOString(), ...entry });
    fs.writeFileSync(outFile, JSON.stringify(prev, null, 2));
  } catch {
    // ignore
  }
}

// Learned selectors store (persisted via PRs from suggestions)
type LearnedMap = Record<string, Candidate[]>;
const learnedFile = path.join(process.cwd(), 'tests', 'ui', 'utils', 'learned_selectors.json');
let learned: LearnedMap = {};
try {
  if (fs.existsSync(learnedFile)) {
    learned = JSON.parse(fs.readFileSync(learnedFile, 'utf8')) as LearnedMap;
  }
} catch {
  learned = {};
}

function getLearnedCandidates(context?: string): Candidate[] {
  if (!context) return [];
  return Array.isArray(learned[context]) ? learned[context] : [];
}

export async function clickSmart(page: Page, candidates: Candidate[], context?: string): Promise<boolean> {
  const all = [...getLearnedCandidates(context), ...candidates];
  for (const c of all) {
    const loc = toLocator(page, c);
    if ((await loc.count()) && (await isVisible(loc))) {
      await loc.click();
      return true;
    }
  }

  // Collect nearby suggestions to help self-heal
  const anchors = await page.$$eval('a, button', (els) =>
    els.slice(0, 200).map((e) => ({ text: (e as HTMLElement).innerText?.trim(), tag: e.tagName, css: e.getAttribute('class') || '' }))
  );
  writeSuggestion({ type: 'click', context, candidates, nearby: anchors });
  return false;
}

export async function fillSmart(page: Page, value: string, candidates: Candidate[], context?: string): Promise<boolean> {
  const all = [...getLearnedCandidates(context), ...candidates];
  for (const c of all) {
    const loc = toLocator(page, c);
    if ((await loc.count()) && (await isVisible(loc))) {
      await loc.fill(value);
      return true;
    }
  }
  const inputs = await page.$$eval('input, textarea, [contenteditable="true"]', (els) =>
    els.slice(0, 200).map((e) => ({ placeholder: (e as HTMLInputElement).placeholder, name: (e as HTMLInputElement).name }))
  );
  writeSuggestion({ type: 'fill', context, valuePreview: value?.slice(0, 20), candidates, nearby: inputs });
  return false;
}

export async function ensureVisible(page: Page, candidates: Candidate[], context?: string): Promise<Locator | null> {
  const all = [...getLearnedCandidates(context), ...candidates];
  for (const c of all) {
    const loc = toLocator(page, c);
    if ((await loc.count()) && (await isVisible(loc))) return loc;
  }
  writeSuggestion({ type: 'ensureVisible', context, candidates });
  return null;
}
