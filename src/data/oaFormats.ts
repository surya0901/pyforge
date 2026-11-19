import type { OAProblem } from '../types';
import { OA_PROBLEMS } from './oaProblems';

export interface OAFormat {
  id: string;
  name: string;
  blurb: string;
  basis: string; // where the format comes from
  minutes: number;
  pick: { kind: OAProblem['kind']; n: number; diff?: OAProblem['difficulty'][] }[];
}

/** Formats are modeled on public candidate reports (Glassdoor, LeetCode Discuss, Taro, techinterview.org). */
export const OA_FORMATS: OAFormat[] = [
  { id: 'debug-plus', name: 'Debugging plus coding', minutes: 40,
    blurb: 'Fix 3 broken functions, then solve 1 coding problem. The mixed HackerRank style you saw at IBM and Vanguard.',
    basis: 'Mixed debugging and coding sections, a common HackerRank setup',
    pick: [{ kind: 'debug', n: 3 }, { kind: 'code', n: 1, diff: ['easy', 'medium'] }] },
  { id: 'amazon-debug', name: 'Debugging section', minutes: 20,
    blurb: '6 short functions, each with one planted bug: flipped comparisons, off by one loops, early returns. Speed matters.',
    basis: 'Amazon\'s OA debugging section: 5 to 7 snippets in about 20 minutes',
    pick: [{ kind: 'debug', n: 6 }] },
  { id: 'ibm', name: 'IBM style OA', minutes: 60,
    blurb: '2 coding problems, easy to medium, with hidden test cases.',
    basis: 'IBM new grad reports: 2 HackerRank questions in 60 minutes',
    pick: [{ kind: 'code', n: 1, diff: ['easy'] }, { kind: 'code', n: 1, diff: ['medium'] }] },
  { id: 'vanguard', name: 'Vanguard style OA', minutes: 90,
    blurb: '3 coding problems, easy to medium, practical rather than puzzle heavy.',
    basis: 'Vanguard reports: 3 HackerRank coding problems in about 90 minutes',
    pick: [{ kind: 'code', n: 2, diff: ['easy'] }, { kind: 'code', n: 1, diff: ['medium'] }] },
  { id: 'bank', name: 'Two medium problems', minutes: 70,
    blurb: '2 medium problems back to back. Good practice for Goldman, JPMorgan and big tech OAs.',
    basis: 'Typical 60 to 90 minute HackerRank screen with 2 problems',
    pick: [{ kind: 'code', n: 2, diff: ['medium'] }] },
  { id: 'build', name: 'Practical build', minutes: 45,
    blurb: 'Build one class with several methods and edge cases, like a key-value store with transactions or an LRU cache.',
    basis: 'Practical multi-part coding at OpenAI and Jane Street',
    pick: [{ kind: 'build', n: 1 }] },
];

const shuffle = <T,>(a: T[]) => { const b = [...a]; for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [b[i], b[j]] = [b[j], b[i]]; } return b; };

/** Picks problems for a format, preferring ones you haven't fully passed. */
export function pickProblems(f: OAFormat, best: Record<string, number>): OAProblem[] {
  const used = new Set<string>();
  const out: OAProblem[] = [];
  for (const slot of f.pick) {
    const pool = shuffle(OA_PROBLEMS.filter((p) => p.kind === slot.kind && !used.has(p.id) && (!slot.diff || slot.diff.includes(p.difficulty))))
      .sort((a, b) => (best[a.id] ?? 0) - (best[b.id] ?? 0));
    for (const p of pool.slice(0, slot.n)) { used.add(p.id); out.push(p); }
  }
  return out;
}
