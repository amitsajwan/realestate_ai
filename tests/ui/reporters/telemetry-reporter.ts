import type { Reporter, TestCase, TestResult, Suite, FullConfig } from '@playwright/test/reporter';
import fs from 'fs';
import path from 'path';

class TelemetryReporter implements Reporter {
  private outDir: string;

  constructor(opts: any = {}) {
    this.outDir = opts.outDir || path.join(process.cwd(), 'test_reports');
  }

  onBegin(config: FullConfig, suite: Suite) {
    if (!fs.existsSync(this.outDir)) fs.mkdirSync(this.outDir, { recursive: true });
    fs.writeFileSync(path.join(this.outDir, 'run_meta.json'), JSON.stringify({
      startTime: new Date().toISOString(),
      total: suite.allTests().length,
    }, null, 2));
  }

  onTestEnd(test: TestCase, result: TestResult) {
    const rec = {
      title: test.title,
      file: test.location.file,
      status: result.status,
      errors: result.errors?.map(e => e.message) || [],
      duration: result.duration,
    };
    const file = path.join(this.outDir, 'results.jsonl');
    fs.appendFileSync(file, JSON.stringify(rec) + '\n');
  }
}

export default TelemetryReporter;
