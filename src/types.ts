export type PatternId =
  | 'arrays'
  | 'two-pointers'
  | 'sliding-window'
  | 'stack'
  | 'binary-search'
  | 'linked-list'
  | 'trees'
  | 'tries'
  | 'heaps'
  | 'backtracking'
  | 'graphs'
  | 'adv-graphs'
  | 'dp-1d'
  | 'dp-2d'
  | 'greedy'
  | 'bits'
  | 'math'
  | 'ds-scratch';

export type CompanyId =
  | 'citadel'
  | 'hrt'
  | 'janestreet'
  | 'meta'
  | 'microsoft'
  | 'amazon'
  | 'google'
  | 'netflix'
  | 'apple'
  | 'nvidia'
  | 'openai';

export type Difficulty = 'easy' | 'medium' | 'hard';

interface Base {
  id: string;
  title: string;
  pattern: PatternId;
  companies: CompanyId[];
  difficulty: Difficulty;
}

/**
 * Syntax drill. In `code`, write __0__, __1__ ... where a blank goes.
 * Each blank lists accepted answers. An answer starting with "re:" is a
 * regex tested against the whitespace-stripped input.
 */
export interface SyntaxExercise extends Base {
  kind: 'syntax';
  prompt: string;
  code: string;
  blanks: { answers: string[]; intent: string }[];
  note?: string;
}

/** Bug hunt. `line` is 1-indexed. options[0] is the correct fix. */
export interface BugExercise extends Base {
  kind: 'bug';
  prompt: string;
  code: string;
  bugs: { line: number; options: string[]; explanation: string }[];
}

/** Pattern recognition speed drill. */
export interface PatternExercise extends Base {
  kind: 'pattern';
  statement: string;
  constraints: string;
  answerPattern: PatternId;
  answerDS: string;
  why: string;
}

export type Exercise = SyntaxExercise | BugExercise | PatternExercise;
export type Mode = 'coach' | 'path' | 'dashboard' | 'syntax' | 'bug' | 'pattern' | 'math' | 'cards' | 'design' | 'companies' | 'reference';

export interface CardState {
  reps: number;
  ease: number;
  interval: number; // days
  due: number; // epoch ms
  attempts: number;
  correct: number;
  lastResult: boolean | null;
  lastSeen: number;
}

export interface Progress {
  cards: Record<string, CardState>;
  days: string[]; // YYYY-MM-DD dates with practice
  mistakes: Record<string, number>; // diagnostic tag -> count
  math: { at: number; score: number }[]; // mental math round results
  savedAt?: number; // last local change, used to merge with the cloud copy
}
