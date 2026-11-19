import { CheckCircle2, ChevronLeft, Circle, EyeOff, Lightbulb, Play, RotateCcw } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { BLUEPRINTS, IDIOMS } from '../data/blueprints';
import { LESSONS } from '../data/lessons';
import { runTests, warmUp, type RunResult } from '../lib/pyrunner';
import { getLocal, setLocal } from '../lib/storage';
import type { Blueprint } from '../types';
import CodeEditor from './CodeEditor';
import { Button, Card, PageTitle } from './ui';

// localStorage keys
const STATUS = 'pyforge.blueprints'; // per problem: when it was passed with hints and when blind
const IDIOM_HINTS = 'pyforge.idiomHints'; // idiom id -> times a hint was needed for it
const LOG = 'pyforge.blueprint.log'; // passes, for the daily checklist

export interface BpStatus { guided?: number; blind?: number; clean?: boolean; hints?: number }
type Level = 0 | 1 | 2 | 3;

const lessonName = (id: string) => LESSONS.find((l) => l.id === id)?.name ?? id;
const norm = (line: string) => line.replace(/#.*$/, '').replace(/\s+/g, ' ').trim();
const indent = (text: string, pad = '    ') => text.split('\n').map((l) => (l ? pad + l : l)).join('\n');

export const getStatus = () => getLocal<Record<string, BpStatus>>(STATUS, {});
export const getIdiomHints = () => getLocal<Record<string, number>>(IDIOM_HINTS, {});
export const blueprintLog = () => getLocal<{ at: number; id: string; blind: boolean }[]>(LOG, []);

function starter(p: Blueprint, blind: boolean) {
  if (blind) return `${p.signature}\n    \n`;
  return `${p.signature}\n${p.steps.map((s, i) => `    # Step ${i + 1}: ${s.text}`).join('\n')}\n`;
}

/** The next problem worth doing: unfinished guided first, then a blind pass you haven't done. */
export function nextBlueprint(preferPattern?: string): Blueprint {
  const st = getStatus();
  const pool = BLUEPRINTS.filter((p) => !st[p.id]?.blind);
  return pool.find((p) => p.pattern === preferPattern && !st[p.id]?.guided)
    ?? pool.find((p) => !st[p.id]?.guided)
    ?? pool[0] ?? BLUEPRINTS[0];
}

// ───────────────────────── Common mistake checker ─────────────────────────
interface Lint { line?: number; msg: string }

/** Strip strings and comments so keyword checks don't fire inside them. */
const codeOnly = (l: string) => l.replace(/(["'])(?:\\.|(?!\1).)*\1/g, '""').replace(/#.*$/, '');

export function lint(code: string, p: Blueprint): Lint[] {
  const out: Lint[] = [];
  const lines = code.split('\n');
  const setVars = new Set<string>();
  lines.forEach((raw) => { const m = codeOnly(raw).match(/(\w+)\s*=\s*set\(/); if (m) setVars.add(m[1]); });
  lines.forEach((raw, i) => {
    const l = codeOnly(raw);
    const n = i + 1;
    if (raw.includes('____')) out.push({ line: n, msg: 'This line still has a ____ blank. Fill it in from the step hint.' });
    if (/\[\s*\[\s*\]\s*\]\s*\*/.test(l)) out.push({ line: n, msg: '[[]] * n makes n copies of the SAME list, so appending to one bucket appends to all of them. Use [[] for _ in range(n)].' });
    if (/\b(true|false)\b/.test(l)) out.push({ line: n, msg: 'Python capitalizes booleans: True and False.' });
    if (/\b(null|nil|undefined)\b/.test(l)) out.push({ line: n, msg: 'Python uses None for "no value".' });
    if (/\.push\(/.test(l)) out.push({ line: n, msg: 'Python lists use .append(), not .push().' });
    if (/\.length\b/.test(l)) out.push({ line: n, msg: 'Use len(x) for the length, not x.length.' });
    if (/&&|\|\|/.test(l)) out.push({ line: n, msg: 'Python spells these as and / or.' });
    if (/!\s*[a-zA-Z_(]/.test(l) && !/!=/.test(l)) out.push({ line: n, msg: 'Python uses not, not !.' });
    if (/\belse\s+if\b/.test(l)) out.push({ line: n, msg: 'Python spells else if as elif.' });
    if (/\w(\+\+|--)/.test(l)) out.push({ line: n, msg: 'Python has no ++ or --. Use x += 1.' });
    if (/=\s*[\w.[\]]+\.sort\(/.test(l)) out.push({ line: n, msg: '.sort() sorts in place and returns None. Call it on its own line, or use sorted(x) to get a new list.' });
    for (const v of setVars) if (new RegExp(`\\b${v}\\.append\\(`).test(l)) out.push({ line: n, msg: `${v} is a set. Sets use .add(), lists use .append().` });
    const t = l.trim();
    if (/^(def|if|elif|else|for|while|try|except|finally|class|with)\b/.test(t) && !t.includes(':') && !/[(\[{,\\]$/.test(t)) out.push({ line: n, msg: `A line starting with ${t.split(/\W/)[0]} has to end with a colon.` });
    if (/^(if|elif|while)\b[^=!<>]*[^=!<>]=[^=]/.test(t)) out.push({ line: n, msg: 'Use == to compare. A single = assigns.' });
  });
  // The function itself must keep the right name, or the tests can't find it.
  const fname = p.signature.match(/def (\w+)/)![1];
  if (!new RegExp(`def ${fname}\\s*\\(`).test(code)) out.push({ line: 1, msg: `Keep the function name ${fname}. The tests call it by that name.` });
  return out;
}

const ident = (s: string) => new Set(s.match(/[A-Za-z_]\w*/g) ?? []);
function dist(a: string, b: string) {
  const d = Array.from({ length: a.length + 1 }, (_, i) => [i, ...Array(b.length).fill(0)]);
  for (let j = 1; j <= b.length; j++) d[0][j] = j;
  for (let i = 1; i <= a.length; i++) for (let j = 1; j <= b.length; j++) d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
  return d[a.length][b.length];
}

/** Turn a raw Python error into a hint aimed at the actual mistake. */
export function explainError(err: string, code: string, p: Blueprint): string | null {
  const name = err.match(/NameError: name '(\w+)' is not defined/);
  if (name) {
    const bad = name[1];
    const known = [...new Set([...ident(code), ...ident(p.solution), 'True', 'False', 'None'])].filter((w) => w !== bad);
    const best = known.map((w) => ({ w, d: w.toLowerCase() === bad.toLowerCase() ? 0 : dist(w, bad) })).sort((a, b) => a.d - b.d)[0];
    if (best && best.d <= 2) return `${bad} isn't defined. Did you mean ${best.w}?${best.w.toLowerCase() === bad.toLowerCase() ? ' Python names are case sensitive.' : ''}`;
    return `${bad} isn't defined yet. Check which step creates it, and that it's spelled the same everywhere.`;
  }
  const attr = err.match(/'(\w+)' object has no attribute '(\w+)'/);
  if (attr) {
    const [, type, a] = attr;
    const fix: Record<string, string> = { 'set.append': '.add()', 'list.add': '.append()', 'dict.append': 'd[key] = value', 'str.append': 'string concatenation (+) or a list', 'list.push': '.append()', 'list.length': 'len(x)', 'str.length': 'len(s)' };
    return `A ${type} has no .${a}.${fix[`${type}.${a}`] ? ` Use ${fix[`${type}.${a}`]} instead.` : ''}`;
  }
  if (/IndentationError|unindent/.test(err)) return 'Indentation is off. Each line inside the function starts with 4 spaces, and each block inside a loop or if adds 4 more. Code for a step goes under its comment at the same indent.';
  if (/IndexError/.test(err)) return 'An index went past the end. Check range() bounds: range(a, b) stops BEFORE b, and the last index is len(x) - 1.';
  if (/KeyError/.test(err)) return 'A dict key was read before it was set. Use d.get(key, 0), or a defaultdict.';
  if (/TypeError: unhashable type: 'list'/.test(err)) return 'Lists can\'t be dict keys or set items. Convert with tuple(...).';
  if (/'NoneType' object is not (iterable|subscriptable)/.test(err)) return 'Something returned None. Common causes: x = x.sort(), or a path through the function with no return.';
  if (/RecursionError/.test(err)) return 'The recursion never stops. The base case has to come first and catch the empty case.';
  return null;
}

// ───────────────────────── Page ─────────────────────────
export default function BlueprintBuilder({ initial }: { initial?: string }) {
  const [sel, setSel] = useState<string | undefined>(initial && BLUEPRINTS.some((b) => b.id === initial) ? initial : undefined);
  const [status, setStatus] = useState(getStatus);
  const [idiomFilter, setIdiomFilter] = useState<string>();
  useEffect(() => { warmUp().catch(() => {}); }, []);

  const p = BLUEPRINTS.find((b) => b.id === sel);
  if (p) return <Workbench key={p.id} p={p} onBack={() => { setSel(undefined); setStatus(getStatus()); }} onNext={(id) => { setStatus(getStatus()); setSel(id); }} />;

  const groups = LESSONS.map((l) => ({ l, list: BLUEPRINTS.filter((b) => b.pattern === l.id && (!idiomFilter || b.steps.some((s) => s.idioms.includes(idiomFilter)))) })).filter((g) => g.list.length);
  const blindCount = BLUEPRINTS.filter((b) => status[b.id]?.blind).length;
  const guidedCount = BLUEPRINTS.filter((b) => status[b.id]?.guided).length;

  return (
    <div className="max-w-5xl">
      <PageTitle sub="For when you know the logic but freeze on a blank editor. Each problem is broken into plain English steps. Type the code for each step, with hints that get more specific only when you ask. Then do it again with no blueprint.">Blueprint builder</PageTitle>
      <div className="mb-6 grid gap-4 sm:grid-cols-[1fr_1.3fr]">
        <Card className="p-5">
          <h3 className="mb-3 text-sm font-semibold text-zinc-100">How to practice</h3>
          <ol className="list-decimal space-y-1.5 pl-5 text-sm text-zinc-300">
            <li>Read the steps. Type each one under its comment. Hints go from a nudge, to a fill in the blank, to the exact lines you type yourself.</li>
            <li>Run the tests. The checker explains the usual slips in plain English.</li>
            <li>Once it passes, do the blind pass: the same problem from just the function line.</li>
          </ol>
          <div className="mt-4 flex gap-6 border-t border-zinc-800 pt-3 text-sm">
            <span className="text-zinc-400"><span className="tnum font-semibold text-zinc-100">{guidedCount}</span>/{BLUEPRINTS.length} with blueprint</span>
            <span className="text-zinc-400"><span className="tnum font-semibold text-emerald-300">{blindCount}</span>/{BLUEPRINTS.length} blind</span>
          </div>
        </Card>
        <WeakIdioms onPick={(id) => setIdiomFilter(idiomFilter === id ? undefined : id)} active={idiomFilter} />
      </div>
      {idiomFilter && (
        <p className="mb-4 text-sm text-zinc-400">Showing problems that use <span className="text-zinc-100">{IDIOMS[idiomFilter]?.label}</span>. <button className="link" onClick={() => setIdiomFilter(undefined)}>Show all</button></p>
      )}
      <div className="grid gap-5 sm:grid-cols-2">
        {groups.map(({ l, list }) => (
          <div key={l.id}>
            <h3 className="mb-2 font-medium text-zinc-300">{l.name}</h3>
            <ul className="divide-y divide-zinc-800 rounded-md border border-zinc-800 bg-zinc-900">
              {list.map((b) => {
                const s = status[b.id];
                return (
                  <li key={b.id}>
                    <button onClick={() => setSel(b.id)} className="flex w-full items-center gap-2 px-3 py-2 text-left text-[15px] hover:bg-zinc-950/50">
                      {s?.blind ? <CheckCircle2 size={15} className="shrink-0 text-emerald-400" /> : s?.guided ? <CheckCircle2 size={15} className="shrink-0 text-amber-400" /> : <Circle size={15} className="shrink-0 text-zinc-600" />}
                      <span className="flex-1 text-zinc-200">{b.title}</span>
                      <span className="text-xs text-zinc-500">{s?.blind ? 'blind done' : s?.guided ? 'blind pass next' : ''}</span>
                      <span className={`text-xs ${b.difficulty === 'easy' ? 'text-emerald-400' : 'text-amber-400'}`}>{b.difficulty}</span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}

/** The Python phrases you've needed hints for most. Also shown on Stats and Syntax recall. */
export function WeakIdioms({ onPick, active, compact }: { onPick?: (id: string) => void; active?: string; compact?: boolean }) {
  const counts = getIdiomHints();
  const top = Object.entries(counts).filter(([id]) => IDIOMS[id]).sort((a, b) => b[1] - a[1]).slice(0, compact ? 4 : 6);
  const [shown, setShown] = useState<string>();
  return (
    <Card className="p-5">
      <h3 className="mb-1 text-sm font-semibold text-zinc-100">Python phrases you needed hints for</h3>
      {!top.length ? (
        <p className="text-sm text-zinc-400">Nothing yet. Every hint you open in Blueprint builder is counted against the Python phrases that step uses, so your weak spots show up here.</p>
      ) : (
        <>
          <p className="mb-3 text-sm text-zinc-500">{onPick ? 'Pick one to see the problems that use it.' : 'Click one to see the exact syntax.'}</p>
          <ul className="space-y-1.5">
            {top.map(([id, n]) => (
              <li key={id}>
                <button onClick={() => (onPick ? onPick(id) : setShown(shown === id ? undefined : id))} className={`flex w-full items-center justify-between gap-3 rounded-md px-2 py-1 text-left text-sm hover:bg-zinc-950/60 ${active === id ? 'bg-violet-500/10 text-violet-200' : 'text-zinc-300'}`}>
                  <span>{IDIOMS[id].label}</span>
                  <span className="rounded bg-amber-500/10 px-1.5 font-mono text-xs text-amber-300">×{n}</span>
                </button>
                {(shown === id || active === id) && <pre className="mt-1 rounded-md bg-zinc-950 px-3 py-2 font-mono text-[12.5px] text-emerald-200">{IDIOMS[id].example}</pre>}
              </li>
            ))}
          </ul>
        </>
      )}
    </Card>
  );
}

function Workbench({ p, onBack, onNext }: { p: Blueprint; onBack: () => void; onNext: (id: string) => void }) {
  const prev = getStatus()[p.id];
  const [blind, setBlind] = useState(!!prev?.guided && !prev?.blind);
  const [code, setCode] = useState(() => starter(p, !!prev?.guided && !prev?.blind));
  const [levels, setLevels] = useState<Level[]>(() => p.steps.map(() => 0));
  const [busy, setBusy] = useState(false);
  const [r, setR] = useState<RunResult>();
  const [ranLint, setRanLint] = useState<Lint[]>([]);
  const [pasteNote, setPasteNote] = useState(false);
  const [passed, setPassed] = useState(false);
  const hintsUsed = levels.reduce<number>((a, l) => a + l, 0);

  // Which reference lines are already in the editor, ignoring spacing. Many correct answers exist,
  // so this is only used to point at the step that probably needs another look.
  const typed = useMemo(() => new Set(code.split('\n').map(norm).filter(Boolean)), [code]);
  const stepMatch = p.steps.map((s) => { const ls = s.code.split('\n').map(norm).filter(Boolean); return { got: ls.filter((x) => typed.has(x)).length, of: ls.length }; });

  const reset = (b: boolean) => { setBlind(b); setCode(starter(p, b)); setLevels(p.steps.map(() => 0)); setR(undefined); setRanLint([]); setPassed(false); };

  function hint(i: number) {
    const next = Math.min(3, levels[i] + 1) as Level;
    if (next === levels[i]) return;
    setLevels(levels.map((l, j) => (j === i ? next : l)));
    const counts = getIdiomHints();
    for (const id of p.steps[i].idioms) counts[id] = (counts[id] ?? 0) + 1;
    setLocal(IDIOM_HINTS, counts);
    if (next === 2) insertTemplate(i);
  }

  /** Level 2: drop the fill in the blank template right under the step's comment. */
  function insertTemplate(i: number) {
    const tmpl = indent(p.steps[i].template);
    const lines = code.split('\n');
    const at = lines.findIndex((l) => l.trim().startsWith(`# Step ${i + 1}:`));
    if (at >= 0) {
      // skip anything already typed under this step, up to the next step comment
      let end = at + 1;
      while (end < lines.length && !lines[end].trim().startsWith('# Step ') && lines[end].trim()) end++;
      lines.splice(end, 0, tmpl);
      setCode(lines.join('\n'));
    } else setCode(code.replace(/\s*$/, '') + '\n' + tmpl + '\n');
  }

  async function run() {
    const l = lint(code, p);
    setRanLint(l);
    if (l.some((x) => x.msg.includes('____'))) { setR(undefined); return; }
    setBusy(true);
    const src = code + (p.postlude ? '\n\n' + p.postlude + '\n' : '');
    const res = await runTests(src, p.func, 'code', p.tests, p.expected, 'exact');
    setBusy(false);
    setR(res);
    const ok = !res.compileError && !res.timeout && !res.loadError && res.results.length > 0 && res.results.every((t) => t.ok);
    if (ok && !passed) {
      setPassed(true);
      const all = getStatus();
      const cur = all[p.id] ?? {};
      all[p.id] = blind ? { ...cur, blind: Date.now(), guided: cur.guided ?? Date.now() } : { ...cur, guided: Date.now(), clean: hintsUsed === 0, hints: hintsUsed };
      setLocal(STATUS, all);
      setLocal(LOG, [...blueprintLog().slice(-200), { at: Date.now(), id: p.id, blind }]);
    }
  }

  const firstErr = r?.compileError ?? r?.results.find((t) => t.error)?.error;
  const friendly = firstErr ? explainError(firstErr, code, p) : null;
  const failing = r && !r.compileError && r.results.some((t) => !t.ok);
  const suspect = failing && !blind ? stepMatch.findIndex((m) => m.got < m.of) : -1;
  const liveLint = lint(code, p).filter((x) => !x.msg.includes('____') && !x.msg.startsWith('Keep the function'));
  const shownLint = r || ranLint.length ? ranLint : liveLint;
  const nextP = BLUEPRINTS[(BLUEPRINTS.indexOf(p) + 1) % BLUEPRINTS.length];

  return (
    <div className="max-w-6xl">
      <button onClick={onBack} className="mb-3 flex items-center gap-1 text-sm text-zinc-400 hover:text-zinc-100"><ChevronLeft size={15} />All blueprints</button>
      <div className="mb-4 flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <h2 className="text-2xl font-bold tracking-tight text-zinc-100">{p.title}</h2>
        <span className="text-sm text-zinc-500">{lessonName(p.pattern)} · {p.difficulty}</span>
        <span className={`rounded-full px-2 py-0.5 text-xs ${blind ? 'bg-emerald-500/10 text-emerald-300' : 'bg-violet-500/10 text-violet-200'}`}>{blind ? 'Blind pass: no blueprint' : 'With blueprint'}</span>
      </div>
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.25fr)]">
        <div className="space-y-4">
          <Card className="p-4">
            <p className="text-[15px] text-zinc-200">{p.statement}</p>
            <p className="mt-2 font-mono text-[13px] text-zinc-400">{p.example}</p>
            <a href={`https://neetcode.io/problems/${p.nc}`} target="_blank" rel="noreferrer" className="link mt-2 inline-block text-sm">NeetCode page and video</a>
          </Card>
          {blind ? (
            <Card className="p-4">
              <h3 className="mb-1 text-sm font-semibold text-zinc-100">No steps this time</h3>
              <p className="text-sm text-zinc-400">Write it from the function line. Say the 4 steps to yourself first, then type. This pass is what makes it stick.</p>
              <ol className="mt-3 list-decimal space-y-1 pl-5 text-sm text-zinc-500">
                {p.steps.map((s, i) => <li key={i} className="blur-[3px] transition hover:blur-0" title="Hover only if you're really stuck">{s.text}</li>)}
              </ol>
              <button onClick={() => reset(false)} className="link mt-3 text-sm">Stuck? Go back to the blueprint</button>
            </Card>
          ) : (
            <ol className="space-y-3">
              {p.steps.map((s, i) => {
                const lv = levels[i];
                const m = stepMatch[i];
                return (
                  <li key={i}>
                    <Card className={`p-4 ${suspect === i ? 'border-amber-500/50' : ''}`}>
                      <div className="flex items-start gap-3">
                        <span className={`mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full text-xs font-semibold ${m.got === m.of ? 'bg-emerald-500/15 text-emerald-300' : 'bg-zinc-800 text-zinc-300'}`}>{i + 1}</span>
                        <div className="min-w-0 flex-1">
                          <p className="text-[15px] text-zinc-100">{s.text}</p>
                          {suspect === i && <p className="mt-1 text-sm text-amber-300">Tests are failing and this step looks different from the blueprint. Check it first.</p>}
                          {lv >= 1 && <p className="mt-2 text-sm text-zinc-300"><span className="font-medium text-amber-300">Clue: </span>{s.clue}</p>}
                          {lv >= 2 && (
                            <div className="mt-2">
                              <div className="text-xs text-zinc-500">{lv === 2 ? 'Added to your editor. Fill the ____ blanks:' : 'Fill in the blank:'}</div>
                              <pre className="mt-1 overflow-x-auto rounded-md bg-zinc-950 px-3 py-2 font-mono text-[12.5px] text-zinc-300">{s.template}</pre>
                            </div>
                          )}
                          {lv >= 3 && (
                            <div className="mt-2">
                              <div className="text-xs text-zinc-500">Exact lines. Type them yourself (paste is off), then say out loud what each one does:</div>
                              <pre className="mt-1 overflow-x-auto rounded-md bg-zinc-950 px-3 py-2 font-mono text-[12.5px]">
                                {s.code.split('\n').map((ln, k) => <div key={k} className={typed.has(norm(ln)) ? 'text-emerald-300' : 'text-zinc-100'}>{ln}</div>)}
                              </pre>
                            </div>
                          )}
                          <div className="mt-2 flex items-center gap-3">
                            {lv < 3 && (
                              <button onClick={() => hint(i)} className="flex items-center gap-1 text-sm text-violet-300 hover:underline">
                                <Lightbulb size={14} />{lv === 0 ? 'Hint: syntax clue' : lv === 1 ? 'Hint: fill in the blank' : 'Hint: show the exact lines'}
                              </button>
                            )}
                            <span className="text-xs text-zinc-500">{m.got}/{m.of} lines match the blueprint</span>
                          </div>
                        </div>
                      </div>
                    </Card>
                  </li>
                );
              })}
            </ol>
          )}
        </div>

        <div>
          <CodeEditor value={code} onChange={(v) => { setCode(v); setPasteNote(false); }} onRun={run} errorLine={r?.line ?? r?.results.find((t) => t.line)?.line} minRows={18}
            onPaste={(e) => { e.preventDefault(); setPasteNote(true); }} />
          {pasteNote && <p className="mt-2 text-sm text-amber-300">Paste is off here. Typing it is the whole point: that's what builds the muscle memory.</p>}
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <Button onClick={run} disabled={busy}><Play size={14} />{busy ? 'Running…' : 'Run tests'}</Button>
            <span className="text-xs text-zinc-500">Ctrl or Cmd + Enter</span>
            <span className="flex-1" />
            {!blind && <Button variant="ghost" onClick={() => reset(true)}><EyeOff size={14} />Blind pass</Button>}
            <Button variant="ghost" onClick={() => reset(blind)}><RotateCcw size={14} />Start over</Button>
          </div>

          {shownLint.length > 0 && (
            <Card className="mt-3 border-amber-500/30 p-4">
              <h3 className="mb-2 text-sm font-semibold text-amber-200">Check these first</h3>
              <ul className="space-y-1 text-sm text-zinc-200">
                {shownLint.slice(0, 6).map((x, i) => <li key={i}>{x.line ? <span className="mr-2 font-mono text-xs text-zinc-500">line {x.line}</span> : null}{x.msg}</li>)}
              </ul>
            </Card>
          )}
          {busy && !r && <p className="mt-3 text-sm text-zinc-500">Starting Python the first time takes a few seconds…</p>}
          {r && <Results r={r} p={p} friendly={friendly} />}

          {passed && (
            <Card className="mt-3 border-emerald-500/40 p-4">
              <p className="font-semibold text-emerald-300">{blind ? 'Passed blind. This one is yours now.' : hintsUsed === 0 ? 'Passed with no hints.' : `Passed, using ${hintsUsed} hint level${hintsUsed === 1 ? '' : 's'}.`}</p>
              <p className="mt-1 text-sm text-zinc-300">{blind ? 'Come back to it in a few days and do it blind once more.' : 'Now type it again with no blueprint. Doing it twice is what moves it from copying to recall.'}</p>
              <div className="mt-3 flex gap-2">
                {!blind && <Button onClick={() => reset(true)}><EyeOff size={14} />Start the blind pass</Button>}
                <Button variant={blind ? 'primary' : 'ghost'} onClick={() => onNext(nextP.id)}>Next: {nextP.title}</Button>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

function Results({ r, p, friendly }: { r: RunResult; p: Blueprint; friendly: string | null }) {
  const box = 'mt-3 rounded-md border border-rose-500/30 bg-rose-500/5 p-3 text-sm text-rose-200';
  if (r.loadError) return <p className={box}>{r.loadError}</p>;
  if (r.timeout) return <p className={box}>Your code ran for more than 8 seconds. Look for a while loop whose pointer never moves.</p>;
  if (r.compileError) return (
    <div className={box}>
      <div className="font-mono">{r.compileError}{r.line ? ` (line ${r.line})` : ''}</div>
      {friendly && <div className="mt-2 text-zinc-100">{friendly}</div>}
    </div>
  );
  const passed = r.results.filter((t) => t.ok).length;
  const fmtArgs = (a: unknown[]) => a.map((x) => JSON.stringify(x)).join(', ');
  return (
    <Card className="mt-3 p-4">
      <p className={`mb-2 font-semibold ${passed === r.results.length ? 'text-emerald-300' : 'text-rose-300'}`}>{passed}/{r.results.length} tests passed</p>
      {friendly && <p className="mb-2 rounded-md border border-amber-500/40 px-3 py-2 text-sm text-zinc-100">{friendly}</p>}
      <ul className="space-y-1.5">
        {r.results.map((t, i) => (
          <li key={i} className="rounded-md bg-zinc-950 px-3 py-2 text-[13px]">
            <span className={`font-medium ${t.ok ? 'text-emerald-400' : 'text-rose-400'}`}>{t.ok ? 'Passed' : 'Failed'}</span>
            <span className="ml-2 font-mono text-zinc-500">{p.func}({fmtArgs(p.tests[i]).slice(0, 90)})</span>
            {!t.ok && (
              <div className="mt-1 font-mono text-zinc-300">
                {t.error ? <div className="text-rose-300">{t.error}{t.line ? ` (line ${t.line})` : ''}</div> : <div>Got {t.got}, expected {t.expected}</div>}
              </div>
            )}
            {t.stdout && <pre className="mt-1 whitespace-pre-wrap font-mono text-zinc-500">printed: {t.stdout}</pre>}
          </li>
        ))}
      </ul>
    </Card>
  );
}
