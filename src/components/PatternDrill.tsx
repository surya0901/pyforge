import { BookOpen, CheckCircle2, Play, Timer, XCircle } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { FINDER_BY_ID, FINDER_PATTERNS } from '../data/finder';
import { LESSON_BY_ID } from '../data/lessons';
import { shuffle } from '../lib/check';
import { highlight } from '../lib/highlight';
import type { PatternExercise } from '../types';
import { Button, Card, CompanyTags, DiffTag, Kbd } from './ui';

interface Props {
  queue: PatternExercise[];
  onResult: (id: string, quality: 0 | 1 | 2 | 3, tags: string[]) => void;
  onLearn?: (lessonId: string) => void;
}

const SESSION = 10;
const TARGETS = [{ s: 0, label: 'No target' }, { s: 60, label: '60 s' }, { s: 90, label: '90 s' }, { s: 120, label: '2 min' }];
const fmtS = (x: number) => (x >= 60 ? `${Math.floor(x / 60)}:${String(Math.round(x % 60)).padStart(2, '0')}` : `${x.toFixed(0)}s`);

export default function PatternDrill({ queue, onResult, onLearn }: Props) {
  const [idx, setIdx] = useState(0);
  const [running, setRunning] = useState(false);
  const [target, setTarget] = useState(() => Number(localStorage.getItem('pyforge.finderTarget') ?? 90));
  const [log, setLog] = useState<{ id: string; title: string; secs: number; right: boolean }[]>([]);
  const [summary, setSummary] = useState(false);
  const ex = queue[idx % Math.max(queue.length, 1)];
  const [pick, setPick] = useState<string | null>(null);
  const [secs, setSecs] = useState(0);
  const [score, setScore] = useState({ right: 0, total: 0 });
  const start = useRef(0);
  const done = pick !== null;

  const options = useMemo(() => {
    if (!ex) return [];
    const conf = ex.confusers.filter((c) => c !== ex.answer && FINDER_BY_ID[c]).slice(0, 3);
    const fill = shuffle(FINDER_PATTERNS.map((p) => p.id).filter((id) => id !== ex.answer && !conf.includes(id))).slice(0, 3 - conf.length);
    return shuffle([ex.answer, ...conf, ...fill]);
  }, [ex, idx]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { setPick(null); setSecs(0); start.current = Date.now(); }, [idx, running]);

  // A stopwatch, not a countdown: you are never cut off, but the session report tells you if you were on pace.
  useEffect(() => {
    if (!running || done || summary) return;
    const t = setInterval(() => setSecs((Date.now() - start.current) / 1000), 250);
    return () => clearInterval(t);
  }, [running, done, summary, idx]);

  const finish = (p: string | null) => {
    if (done || !ex) return;
    setPick(p);
    const right = p === ex.answer;
    const took = (Date.now() - start.current) / 1000;
    setSecs(took);
    onResult(ex.id, right ? (target && took <= target / 2 ? 3 : 2) : 0, right ? [] : ['pattern-miss']);
    setScore((s) => ({ right: s.right + (right ? 1 : 0), total: s.total + 1 }));
    setLog((l) => [...l, { id: ex.id, title: ex.title, secs: took, right }]);
  };

  const sessionLen = Math.max(1, Math.min(SESSION, queue.length));
  const next = () => {
    if (log.length && log.length % sessionLen === 0 && !summary) { setSummary(true); return; }
    setIdx((i) => i + 1);
  };
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
      if (summary) { if (e.key === 'Enter') { e.preventDefault(); setSummary(false); setIdx((i) => i + 1); } return; }
      if (!running) { if (e.key === 'Enter') { e.preventDefault(); setRunning(true); } return; }
      if (done) { if (e.key === 'Enter') { e.preventDefault(); next(); } return; }
      const n = Number(e.key);
      if (n >= 1 && n <= options.length) finish(options[n - 1]);
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  });

  if (!ex) return null;

  if (summary) {
    const batch = log.slice(-sessionLen);
    const right = batch.filter((x) => x.right).length;
    const avg = batch.reduce((a, x) => a + x.secs, 0) / batch.length;
    const onPace = target ? batch.filter((x) => x.secs <= target).length : batch.length;
    const slow = [...batch].sort((a, b) => b.secs - a.secs).filter((x) => target && x.secs > target);
    const verdict = right / batch.length >= 0.8 && (!target || onPace / batch.length >= 0.8)
      ? 'Interview ready on these. Try a tighter target next.'
      : right / batch.length < 0.6 ? 'Accuracy first: reread the lessons for the ones you missed before worrying about speed.'
      : 'Getting there. Speed comes from spotting the clue words, so reread the clue for your slowest ones.';
    return (
      <Card className="mx-auto max-w-2xl p-7">
        <h2 className="text-2xl font-bold text-zinc-100">Session report</h2>
        <p className="mt-1 text-zinc-400">{verdict}</p>
        <div className="mt-5 grid grid-cols-3 gap-3 text-center">
          <div className="rounded-lg bg-zinc-950 p-3"><div className="tnum text-2xl font-bold text-zinc-100">{right}/{batch.length}</div><div className="text-sm text-zinc-500">right</div></div>
          <div className="rounded-lg bg-zinc-950 p-3"><div className="tnum text-2xl font-bold text-zinc-100">{fmtS(avg)}</div><div className="text-sm text-zinc-500">average time</div></div>
          <div className="rounded-lg bg-zinc-950 p-3"><div className={`tnum text-2xl font-bold ${!target || onPace === batch.length ? 'text-emerald-300' : 'text-amber-300'}`}>{target ? `${onPace}/${batch.length}` : 'Off'}</div><div className="text-sm text-zinc-500">{target ? `within ${fmtS(target)}` : 'no target set'}</div></div>
        </div>
        <h3 className="mb-2 mt-6 font-semibold text-zinc-100">Every question</h3>
        <ul className="divide-y divide-zinc-800 rounded-md border border-zinc-800">
          {batch.map((x, i) => (
            <li key={i} className="flex items-center gap-3 px-3 py-2 text-[15px]">
              {x.right ? <CheckCircle2 size={16} className="text-emerald-400" /> : <XCircle size={16} className="text-rose-400" />}
              <span className="flex-1 text-zinc-200">{x.title}</span>
              <span className={`tnum font-mono text-sm ${target && x.secs > target ? 'text-amber-300' : 'text-zinc-400'}`}>{fmtS(x.secs)}{target && x.secs > target ? ' over' : ''}</span>
            </li>
          ))}
        </ul>
        {slow.length > 0 && <p className="mt-3 text-sm text-zinc-400">Over target: {slow.map((x) => x.title).join(', ')}. In a real interview you have a minute or two to name the approach before you start coding.</p>}
        <div className="mt-6 flex gap-2">
          <Button onClick={() => { setSummary(false); setIdx((i) => i + 1); }}>Next {sessionLen} questions <Kbd>Enter</Kbd></Button>
        </div>
      </Card>
    );
  }

  if (!running) {
    return (
      <Card className="mx-auto max-w-xl p-8 text-center">
        <Timer className="mx-auto mb-3 text-violet-400" size={28} />
        <h2 className="text-lg font-semibold text-zinc-100">Pattern finder</h2>
        <p className="mt-2 text-zinc-400">
          You get a real interview problem with an example and constraints. Pick the pattern that gives the most
          efficient solution. A stopwatch tracks each answer but never cuts you off. After every {sessionLen} questions
          you get a report on accuracy and whether you were on pace.
        </p>
        <p className="mt-4 text-sm font-medium text-zinc-300">Target time per question</p>
        <div className="mt-2 flex flex-wrap justify-center gap-1.5">
          {TARGETS.map((t) => (
            <button key={t.s} onClick={() => { setTarget(t.s); localStorage.setItem('pyforge.finderTarget', String(t.s)); }}
              className={`rounded-full border px-3 py-1 text-sm ${target === t.s ? 'border-violet-500 bg-violet-500/10 text-zinc-100' : 'border-zinc-700 text-zinc-400 hover:text-zinc-200'}`}>{t.label}</button>
          ))}
        </div>
        <p className="mt-3 text-sm text-zinc-500">{queue.length} problems unlocked · keys <Kbd>1</Kbd>–<Kbd>4</Kbd></p>
        <Button className="mt-5" onClick={() => setRunning(true)}><Play size={15} />Start <Kbd>Enter</Kbd></Button>
      </Card>
    );
  }

  const right = pick === ex.answer;
  const ans = FINDER_BY_ID[ex.answer];
  const picked = pick ? FINDER_BY_ID[pick] : null;
  const lesson = ans.lesson ? LESSON_BY_ID[ans.lesson] : undefined;
  const optCls = (id: string) =>
    !done ? 'border-zinc-800 text-zinc-200 hover:border-violet-500'
      : id === ex.answer ? 'border-emerald-500/60 bg-emerald-500/10 text-emerald-200'
      : id === pick ? 'border-rose-500/60 bg-rose-500/10 text-rose-200' : 'border-zinc-800 text-zinc-500';

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-3 flex items-center justify-between text-sm text-zinc-500">
        <span className="tnum">Question {(log.length - (done ? 1 : 0)) % sessionLen + 1} of {sessionLen} this session</span>
        <span className="tnum">{score.right} of {score.total} right this session</span>
      </div>
      {target > 0 && !done && (
        <div className="mb-4 h-1.5 overflow-hidden rounded-full bg-zinc-800">
          <div className={`h-full transition-[width] duration-200 ${secs <= target * 0.75 ? 'bg-emerald-500' : secs <= target ? 'bg-amber-500' : 'bg-rose-500'}`} style={{ width: `${Math.min(1, secs / target) * 100}%` }} />
        </div>
      )}

      <Card className="p-6">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <DiffTag d={ex.difficulty} />
          <CompanyTags ids={ex.companies} />
          <span className={`tnum ml-auto font-mono text-sm ${target && secs > target ? 'text-rose-300' : 'text-zinc-300'}`}>{fmtS(secs)}{target ? ` / ${fmtS(target)}` : ''}</span>
        </div>
        <h3 className="text-xl font-semibold text-zinc-100">{ex.title}</h3>
        <p className="mt-2 text-[17px] leading-relaxed text-zinc-200">{ex.statement}</p>
        <div className="mt-3 rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 font-mono text-sm text-zinc-300"><span className="text-zinc-500">Example: </span>{ex.example}</div>
        <p className="mt-2 font-mono text-sm text-sky-300">Constraints: {ex.constraints}</p>
      </Card>

      <h4 className="mb-2 mt-5 text-lg font-semibold text-zinc-100">Which pattern gives the most efficient solution?</h4>
      <div className="grid gap-2 sm:grid-cols-2">
        {options.map((id, i) => (
          <button key={id} onClick={() => finish(id)} disabled={done}
            className={`flex items-center gap-3 rounded-lg border px-3 py-3 text-left text-[15px] transition-colors ${optCls(id)}`}>
            <Kbd>{i + 1}</Kbd>{FINDER_BY_ID[id].name}
          </button>
        ))}
      </div>

      {done && (
        <Card className="mt-5 p-5">
          <p className="mb-4 flex flex-wrap items-center gap-2 font-medium">
            {right ? <><CheckCircle2 size={18} className="text-emerald-400" /><span className="text-emerald-300">Right.</span></>
              : <><XCircle size={18} className="text-rose-400" /><span className="text-rose-300">Not this one.</span></>}
            <span className="text-zinc-300">The best fit is <span className="hl font-semibold text-zinc-100">{ans.name}</span>.</span>
          </p>
          <div className="space-y-4 text-[15px] leading-relaxed">
            <Sec t="The clue in the problem">{ex.clue}</Sec>
            <Sec t="The obvious approach">{ex.brute}</Sec>
            <Sec t={`How ${ans.name.toLowerCase()} solves it`}>{ex.insight} <span className="whitespace-nowrap font-mono text-sm text-sky-300">{ex.optimal}</span></Sec>
            {picked && !right && (
              <Sec t={`Why not ${picked.name.toLowerCase()}?`} warn>
                {ex.whyNot?.[picked.id] ?? `${picked.name} fits when ${picked.fitsWhen}. This problem doesn't have that shape, so it would be slower than needed or give wrong answers.`}
              </Sec>
            )}
            {ex.followUp && <Sec t="What interviewers ask next">{ex.followUp}</Sec>}
          </div>
          {lesson && !right && <Template code={lesson.template} name={lesson.name} />}
          <div className="mt-5 flex flex-wrap gap-2">
            <Button onClick={next}>Next<Kbd>Enter</Kbd></Button>
            {lesson && onLearn && <Button variant="subtle" onClick={() => onLearn(lesson.id)}><BookOpen size={15} />{right ? 'Review' : 'Learn'} {lesson.name}</Button>}
            {ex.nc && <a href={`https://neetcode.io/problems/${ex.nc}`} target="_blank" rel="noreferrer" className="inline-flex items-center rounded-md px-3 py-2 text-sm font-medium text-violet-300 hover:underline">Solve it on NeetCode</a>}
          </div>
        </Card>
      )}
    </div>
  );
}

function Sec({ t, children, warn }: { t: string; children: React.ReactNode; warn?: boolean }) {
  return (
    <div className={warn ? 'rounded-md border border-rose-500/30 bg-rose-500/5 px-4 py-3' : ''}>
      <h5 className="font-semibold text-zinc-100">{t}</h5>
      <p className="text-zinc-300">{children}</p>
    </div>
  );
}

function Template({ code, name }: { code: string; name: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-4">
      <button onClick={() => setOpen(!open)} className="text-sm font-medium text-violet-300 hover:underline">{open ? 'Hide' : 'Show'} the {name.toLowerCase()} template</button>
      {open && <pre className="mt-2 overflow-x-auto rounded-md border border-zinc-800 bg-zinc-950 p-3 font-mono text-[13px] leading-relaxed">{code.split('\n').map((line, i) => <div key={i}>{line ? highlight(line, `t${i}`) : ' '}</div>)}</pre>}
    </div>
  );
}
