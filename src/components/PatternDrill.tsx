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

const LIMIT = 45;

export default function PatternDrill({ queue, onResult, onLearn }: Props) {
  const [idx, setIdx] = useState(0);
  const [running, setRunning] = useState(false);
  const [timed, setTimed] = useState(false);
  const ex = queue[idx % Math.max(queue.length, 1)];
  const [pick, setPick] = useState<string | null>(null);
  const [timedOut, setTimedOut] = useState(false);
  const [left, setLeft] = useState(LIMIT);
  const [score, setScore] = useState({ right: 0, total: 0 });
  const start = useRef(0);
  const done = pick !== null || timedOut;

  const options = useMemo(() => {
    if (!ex) return [];
    const conf = ex.confusers.filter((c) => c !== ex.answer && FINDER_BY_ID[c]).slice(0, 3);
    const fill = shuffle(FINDER_PATTERNS.map((p) => p.id).filter((id) => id !== ex.answer && !conf.includes(id))).slice(0, 3 - conf.length);
    return shuffle([ex.answer, ...conf, ...fill]);
  }, [ex, idx]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { setPick(null); setTimedOut(false); setLeft(LIMIT); start.current = Date.now(); }, [idx, running]);

  const finish = (p: string | null, timeout = false) => {
    if (done || !ex) return;
    if (timeout) setTimedOut(true); else setPick(p);
    const right = p === ex.answer;
    const secs = (Date.now() - start.current) / 1000;
    onResult(ex.id, right ? (timed && secs < 15 ? 3 : 2) : 0, right ? [] : [timeout ? 'timeout' : 'pattern-miss']);
    setScore((s) => ({ right: s.right + (right ? 1 : 0), total: s.total + 1 }));
  };

  useEffect(() => {
    if (!running || done || !timed) return;
    const t = setInterval(() => {
      const remain = LIMIT - (Date.now() - start.current) / 1000;
      setLeft(Math.max(0, remain));
      if (remain <= 0) finish(null, true);
    }, 100);
    return () => clearInterval(t);
  });

  const next = () => setIdx((i) => i + 1);
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
      if (!running) { if (e.key === 'Enter') { e.preventDefault(); setRunning(true); } return; }
      if (done) { if (e.key === 'Enter') { e.preventDefault(); next(); } return; }
      const n = Number(e.key);
      if (n >= 1 && n <= options.length) finish(options[n - 1]);
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  });

  if (!ex) return null;

  if (!running) {
    return (
      <Card className="mx-auto max-w-xl p-8 text-center">
        <Timer className="mx-auto mb-3 text-violet-400" size={28} />
        <h2 className="text-lg font-semibold text-zinc-100">Pattern finder</h2>
        <p className="mt-2 text-zinc-400">
          You get a real interview problem with an example and constraints. Pick the pattern that gives the most
          efficient solution. Every answer comes with the clue to spot, the brute force, the optimal idea, and why
          the tempting wrong choices fail.
        </p>
        <p className="mt-2 text-sm text-zinc-500">{queue.length} problems unlocked · keys <Kbd>1</Kbd>–<Kbd>4</Kbd></p>
        <div className="mt-5 flex flex-wrap justify-center gap-2">
          <Button onClick={() => { setTimed(false); setRunning(true); }}><Play size={15} />Practice, no timer <Kbd>Enter</Kbd></Button>
          <Button variant="subtle" onClick={() => { setTimed(true); setRunning(true); }}><Timer size={15} />Interview pace, {LIMIT}s each</Button>
        </div>
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
        <span className="tnum">Problem {(idx % queue.length) + 1} of {queue.length}</span>
        <span className="tnum">{score.right} of {score.total} right this session</span>
      </div>
      {timed && (
        <div className="mb-4 h-1.5 overflow-hidden rounded-full bg-zinc-800">
          <div className={`h-full transition-[width] duration-100 ${left / LIMIT > 0.5 ? 'bg-emerald-500' : left / LIMIT > 0.2 ? 'bg-amber-500' : 'bg-rose-500'}`} style={{ width: `${(done ? 0 : left / LIMIT) * 100}%` }} />
        </div>
      )}

      <Card className="p-6">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <DiffTag d={ex.difficulty} />
          <CompanyTags ids={ex.companies} />
          {!done && timed && <span className="ml-auto font-mono text-sm text-zinc-300">{left.toFixed(0)}s</span>}
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
              : <><XCircle size={18} className="text-rose-400" /><span className="text-rose-300">{timedOut ? 'Time’s up.' : 'Not this one.'}</span></>}
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
