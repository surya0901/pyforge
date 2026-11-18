import { CheckCircle2, Play, Timer, XCircle } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { DS_CHOICES, PATTERNS, PATTERN_NAME } from '../data/meta';
import { shuffle } from '../lib/check';
import type { PatternExercise, PatternId } from '../types';
import { Button, Card, CompanyTags, DiffTag, Kbd } from './ui';

interface Props {
  queue: PatternExercise[];
  onResult: (id: string, quality: 0 | 1 | 2 | 3, tags: string[]) => void;
}

const LIMIT = 15;

export default function PatternDrill({ queue, onResult }: Props) {
  const [idx, setIdx] = useState(0);
  const [running, setRunning] = useState(false);
  const ex = queue[idx % Math.max(queue.length, 1)];
  const [pat, setPat] = useState<PatternId | null>(null);
  const [ds, setDs] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [timedOut, setTimedOut] = useState(false);
  const [left, setLeft] = useState(LIMIT);
  const [score, setScore] = useState({ right: 0, total: 0 });
  const start = useRef(0);

  const patOpts = useMemo(() => {
    if (!ex) return [];
    const others = shuffle(PATTERNS.filter((p) => p.id !== ex.answerPattern)).slice(0, 3).map((p) => p.id);
    return shuffle([ex.answerPattern, ...others]);
  }, [ex, idx]); // eslint-disable-line react-hooks/exhaustive-deps
  const dsOpts = useMemo(() => {
    if (!ex) return [];
    const others = shuffle(DS_CHOICES.filter((d) => d !== ex.answerDS)).slice(0, 3);
    return shuffle([ex.answerDS, ...others]);
  }, [ex, idx]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    setPat(null); setDs(null); setDone(false); setTimedOut(false); setLeft(LIMIT);
    start.current = Date.now();
  }, [idx, running]);

  useEffect(() => {
    if (!running || done) return;
    const t = setInterval(() => {
      const remain = LIMIT - (Date.now() - start.current) / 1000;
      setLeft(Math.max(0, remain));
      if (remain <= 0) { setTimedOut(true); finish(pat, ds, true); }
    }, 100);
    return () => clearInterval(t);
  }); // re-bound each render so finish sees fresh state

  const finish = (p: PatternId | null, d: string | null, timeout = false) => {
    if (done || !ex) return;
    setDone(true);
    const pr = p === ex.answerPattern, dr = d === ex.answerDS;
    const secs = (Date.now() - start.current) / 1000;
    const quality: 0 | 1 | 2 | 3 = pr && dr ? (secs < 8 ? 3 : 2) : pr ? 1 : 0;
    const tags = [...(timeout ? ['timeout'] : []), ...(!pr ? ['pattern-miss'] : []), ...(!dr ? ['ds-miss'] : [])];
    onResult(ex.id, quality, tags);
    setScore((s) => ({ right: s.right + (pr && dr ? 1 : 0), total: s.total + 1 }));
  };

  const choosePat = (p: PatternId) => { if (done) return; setPat(p); if (ds) finish(p, ds); };
  const chooseDs = (d: string) => { if (done) return; setDs(d); if (pat) finish(pat, d); };
  const next = () => setIdx((i) => i + 1);

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (!running) { if (e.key === 'Enter') { e.preventDefault(); setRunning(true); } return; }
      if (done) { if (e.key === 'Enter') { e.preventDefault(); next(); } return; }
      const n = Number(e.key);
      if (n >= 1 && n <= 4) {
        if (!pat) choosePat(patOpts[n - 1]);
        else chooseDs(dsOpts[n - 1]);
      }
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  });

  if (!ex) return null;

  if (!running) {
    return (
      <Card className="mx-auto max-w-xl p-8 text-center">
        <Timer className="mx-auto mb-3 text-violet-400" size={28} />
        <h2 className="text-lg font-semibold text-zinc-100">Pattern Recognizer</h2>
        <p className="mt-2 text-sm text-zinc-400">
          {LIMIT} seconds per problem. Name the optimal pattern, then the primary Python data structure.
          Under 8 s with both right counts as an easy recall.
        </p>
        <p className="mt-2 text-xs text-zinc-500">{queue.length} problems in this set · keys <Kbd>1</Kbd>–<Kbd>4</Kbd></p>
        <Button className="mt-5" onClick={() => setRunning(true)}><Play size={15} />Start <Kbd>Enter</Kbd></Button>
      </Card>
    );
  }

  const optCls = (isPicked: boolean, isAns: boolean) =>
    done
      ? isAns ? 'border-emerald-500/60 bg-emerald-500/10 text-emerald-200' : isPicked ? 'border-rose-500/60 bg-rose-500/10 text-rose-200' : 'border-zinc-800 text-zinc-500'
      : isPicked ? 'border-violet-500 bg-violet-500/10 text-zinc-100' : 'border-zinc-800 text-zinc-300 hover:border-zinc-600';

  const pct = left / LIMIT;
  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-3 flex items-center justify-between text-xs text-zinc-500">
        <span className="tnum">Problem {(idx % queue.length) + 1} of {queue.length}</span>
        <span className="tnum">{score.right} of {score.total} right this session</span>
      </div>
      <div className="mb-4 h-1.5 overflow-hidden rounded-full bg-zinc-800">
        <div className={`h-full transition-[width] duration-100 ${pct > 0.5 ? 'bg-emerald-500' : pct > 0.2 ? 'bg-amber-500' : 'bg-rose-500'}`} style={{ width: `${(done ? 0 : pct) * 100}%` }} />
      </div>

      <Card className="p-6">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <DiffTag d={ex.difficulty} />
          <CompanyTags ids={ex.companies} />
          {!done && <span className="ml-auto font-mono text-sm text-zinc-300">{left.toFixed(1)}s</span>}
        </div>
        <p className="text-xl leading-snug text-zinc-100">{ex.statement}</p>
        <p className="mt-2 font-mono text-xs text-sky-300">{ex.constraints}</p>
      </Card>

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <div>
          <h4 className={`mb-2 font-semibold ${!pat && !done ? 'text-violet-300' : 'text-zinc-500'}`}>First, the pattern</h4>
          <div className="space-y-2">
            {patOpts.map((p, i) => (
              <button key={p} onClick={() => choosePat(p)} className={`flex w-full items-center gap-3 rounded-lg border px-3 py-2 text-left text-sm transition-colors ${optCls(pat === p, done && p === ex.answerPattern)}`}>
                <Kbd>{i + 1}</Kbd>{PATTERN_NAME[p]}
              </button>
            ))}
          </div>
        </div>
        <div>
          <h4 className={`mb-2 font-semibold ${pat && !done ? 'text-violet-300' : 'text-zinc-500'}`}>Then, the main data structure</h4>
          <div className="space-y-2">
            {dsOpts.map((d, i) => (
              <button key={d} onClick={() => chooseDs(d)} className={`flex w-full items-center gap-3 rounded-lg border px-3 py-2 text-left font-mono text-sm transition-colors ${optCls(ds === d, done && d === ex.answerDS)}`}>
                <Kbd>{i + 1}</Kbd>{d}
              </button>
            ))}
          </div>
        </div>
      </div>

      {done && (
        <Card className="mt-4 p-4">
          <div className="mb-2 flex items-center gap-2 text-sm font-medium">
            {pat === ex.answerPattern && ds === ex.answerDS
              ? <><CheckCircle2 size={16} className="text-emerald-400" /><span className="text-emerald-300">Both right</span></>
              : <><XCircle size={16} className="text-rose-400" /><span className="text-rose-300">{timedOut ? 'Time’s up' : 'Not quite'}</span></>}
            <span className="ml-2 text-zinc-400">Answer: <span className="hl text-zinc-100">{PATTERN_NAME[ex.answerPattern]}</span> with <span className="hl font-mono text-zinc-100">{ex.answerDS}</span></span>
          </div>
          <p className="text-sm text-zinc-400">{ex.why}</p>
          <Button className="mt-3" onClick={next}>Next<Kbd>Enter</Kbd></Button>
        </Card>
      )}
    </div>
  );
}
