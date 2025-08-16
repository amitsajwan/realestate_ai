// Process self-heal suggestions and produce a PR-ready summary.
// Optionally writes learned selectors for immediate use.

const fs = require('fs');
const path = require('path');

const suggestionsFile = path.join(process.cwd(), 'test_reports', 'self_heal_suggestions.json');
const learnedFile = path.join(process.cwd(), 'tests', 'ui', 'utils', 'learned_selectors.json');

function main() {
  if (!fs.existsSync(suggestionsFile)) {
    console.log('No self-heal suggestions found.');
    return;
  }
  const data = JSON.parse(fs.readFileSync(suggestionsFile, 'utf8'));
  const grouped = {};
  for (const s of data) {
    const key = s.context || s.type;
    grouped[key] = grouped[key] || { context: key, samples: [] };
    grouped[key].samples.push({ candidates: s.candidates, nearby: s.nearby, valuePreview: s.valuePreview });
  }

  const outDir = path.join(process.cwd(), 'test_reports');
  const summaryFile = path.join(outDir, 'self_heal_summary.md');
  const lines = ['# Self-heal Suggestions', ''];
  Object.values(grouped).forEach((g) => {
    lines.push(`## Context: ${g.context}`);
    lines.push('Suggested candidate updates:');
    // Heuristic: prefer role/text first from nearby anchors
    const best = [];
    for (const sample of g.samples) {
      const fromCandidates = (sample.candidates || []).slice(0, 3).map((c) => ({ source: 'candidate', c }));
      const fromNearby = (sample.nearby || [])
        .filter((n) => n.text && n.text.length <= 40)
        .slice(0, 3)
        .map((n) => ({ source: 'nearby', c: { description: 'nearby-text', text: n.text } }));
      best.push(...fromCandidates, ...fromNearby);
    }
    // Dedup by JSON string
    const dedup = Array.from(new Map(best.map((x) => [JSON.stringify(x.c), x])).values()).map((x) => x.c);
    lines.push('```json');
    lines.push(JSON.stringify(dedup, null, 2));
    lines.push('```');
    lines.push('');

    // Update learned selectors file
    let learned = {};
    if (fs.existsSync(learnedFile)) learned = JSON.parse(fs.readFileSync(learnedFile, 'utf8'));
    learned[g.context] = dedup;
    fs.mkdirSync(path.dirname(learnedFile), { recursive: true });
    fs.writeFileSync(learnedFile, JSON.stringify(learned, null, 2));
  });

  fs.writeFileSync(summaryFile, lines.join('\n'));
  console.log('Wrote:', summaryFile);
  console.log('Updated learned selectors:', learnedFile);
}

main();
