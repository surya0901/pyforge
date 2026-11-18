/**
 * Optional platform capabilities, available when pyforge runs as a claude.ai artifact:
 *  - db:     progress synced to the owner's account (all devices), plus the NeetCode
 *            status document that a scheduled Claude task refreshes from neetcode.io.
 *  - sample: ask Claude (AI coach, behavioral answer grading).
 * Everywhere else (GitHub Pages, local dev) these resolve to null and the app runs
 * on localStorage alone.
 */
import type { Progress } from '../types';

type Snap = { exists: boolean; data(): Record<string, unknown> | undefined; metadata: { fromCache: boolean } };
type DocRef = {
  get(): Promise<Snap>;
  set(d: Record<string, unknown>): Promise<void>;
  onSnapshot(next: (s: Snap) => void, err?: (e: { code: string }) => void): () => void;
};
type DB = { doc(path: string): DocRef };
export type SampleFn = ((input: string | { role: string; content: string }[], opts?: Record<string, unknown>) => Promise<{ text: string }>);

declare global {
  interface Window { claude?: { use(name: string): Promise<unknown> } }
}

const use = async <T,>(name: string): Promise<T | null> => {
  try {
    if (!window.claude?.use) return null;
    return ((await window.claude.use(name)) as T) ?? null;
  } catch {
    return null;
  }
};

export const getDB = () => use<DB>('db');
export const getSample = () => use<SampleFn>('sample');

export const PROGRESS_PATH = 'pyforge/progress';
export const NEETCODE_PATH = 'pyforge/neetcode';

export interface NeetcodeStatus {
  solved: string[]; // neetcode slugs
  updatedAt: string; // ISO time the sync task read neetcode.io
  source?: string;
}

/** Load cloud progress; returns it only if it is newer than the local copy. */
export async function pullProgress(local: Progress): Promise<Progress | null> {
  const db = await getDB();
  if (!db) return null;
  try {
    const snap = await db.doc(PROGRESS_PATH).get();
    if (!snap.exists) return null;
    const d = snap.data() as { json?: string; savedAt?: number } | undefined;
    if (!d?.json) return null;
    const cloud = JSON.parse(d.json) as Progress & { savedAt?: number };
    const localAt = (local as Progress & { savedAt?: number }).savedAt ?? 0;
    return (d.savedAt ?? 0) > localAt ? { ...cloud, savedAt: d.savedAt } as Progress : null;
  } catch {
    return null;
  }
}

let pushTimer: ReturnType<typeof setTimeout> | null = null;
let pushing = false;
let queued: Progress | null = null;

/** Debounced write: at most one in flight, coalesces bursts of answers. */
export function pushProgress(p: Progress) {
  queued = p;
  if (pushTimer) clearTimeout(pushTimer);
  pushTimer = setTimeout(flush, 2500);
}

async function flush() {
  if (pushing || !queued) return;
  const db = await getDB();
  if (!db) return;
  pushing = true;
  const p = queued;
  queued = null;
  try {
    const savedAt = (p as Progress & { savedAt?: number }).savedAt ?? Date.now();
    await db.doc(PROGRESS_PATH).set({ json: JSON.stringify(p), savedAt });
  } catch {
    /* offline or not permitted: local copy still holds the data */
  } finally {
    pushing = false;
    if (queued) pushTimer = setTimeout(flush, 2500);
  }
}

/** Subscribe once to the NeetCode status document. */
export async function watchNeetcode(cb: (s: NeetcodeStatus | null) => void): Promise<() => void> {
  const db = await getDB();
  if (!db) return () => {};
  return db.doc(NEETCODE_PATH).onSnapshot(
    (snap) => {
      const d = snap.exists ? (snap.data() as Partial<NeetcodeStatus>) : undefined;
      cb(d && Array.isArray(d.solved) ? { solved: d.solved as string[], updatedAt: String(d.updatedAt ?? ''), source: d.source as string } : null);
    },
    () => cb(null),
  );
}
