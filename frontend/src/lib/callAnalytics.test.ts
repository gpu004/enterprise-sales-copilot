import { expect, test } from 'vitest';
import * as hegel from '@hegeldev/hegel';
import * as gs from '@hegeldev/hegel/generators';
import fc from 'fast-check';
import { computeCallMetrics } from './callAnalytics';
import type { TranscriptUpdate } from '../types';

function transcript(words: number, speaker: string, is_final = true): TranscriptUpdate {
  return { text: Array(words).fill('word').join(' '), speaker, is_final, timestamp: '' };
}

test('Hegel: talk ratios match independently generated word totals', () =>
  hegel.test((tc) => {
    const sales = tc.draw(gs.integers({ minValue: 0, maxValue: 500 }));
    const customer = tc.draw(gs.integers({ minValue: 0, maxValue: 500 }));
    const metrics = computeCallMetrics([
      transcript(sales, 'sales'), transcript(customer, 'customer'),
      transcript(100, 'sales', false), transcript(100, ''),
    ], []);
    expect(metrics.transcriptLines).toBe(3);
    expect(metrics.repTalkRatio).toBe(sales + customer ? sales / (sales + customer) : null);
    expect(metrics.customerTalkRatio).toBe(sales + customer ? customer / (sales + customer) : null);
  }));

test('fast-check: splitting final speech preserves talk ratios', () => {
  fc.assert(fc.property(
    fc.array(fc.integer({ min: 0, max: 100 }), { maxLength: 30 }),
    fc.integer({ min: 0, max: 100 }),
    (chunks, customer) => {
      const split = computeCallMetrics([
        ...chunks.map((n) => transcript(n, 'sales')), transcript(customer, 'customer'),
      ], []);
      const joined = computeCallMetrics([
        transcript(chunks.reduce((a, b) => a + b, 0), 'sales'), transcript(customer, 'customer'),
      ], []);
      expect(split.repTalkRatio).toBe(joined.repTalkRatio);
      expect(split.customerTalkRatio).toBe(joined.customerTalkRatio);
    },
  ), { numRuns: 200 });
});
