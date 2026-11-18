import { BookOpen, CheckCircle2, Play, Timer, XCircle } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { DS_CHOICES, PATTERNS, PATTERN_NAME } from '../data/meta';
import { DS_FITS, FITS_WHEN, LESSON_BY_ID, LESSON_FOR_PATTERN } from '../data/lessons';
import { highlight } from '../lib/highlight';
import { shuffle } from '../lib/check';
import type { PatternExercise, PatternId } from '../types';
import { Button, Card, CompanyTags, DiffTag, Kbd } from './ui';

interface Props {
  queue: PatternExercise[];
  onResult: (id: string, quality: 0 | 1 | 2 | 3, tags: string[]) => void;
  onLearn?: (lessonId: string) => void;
}

const LIMIT = 15;

export default function PatternDrill({ queue, onResult, onLearn }: Props) {
  const [idx, setIdx] = useState(0);
  const [running, setRunning] = useState(false);
  const [timed, setTimed] = useState(false);
  const [showCode, setShowCode] = useState(false);
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
    setPat(null); setDs(null); setDone(false); setTimedOut(false); setLeft(LIMIT); setShowCode(false);
    start.current = Date.now();
  }, [idx, running]);

  useEffect(() => {
    if (!running || done || !timed) return;
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
    const quality: 0 | 1 | 2 | 3 = pr && dr ? (timed && secs < 8 ? 3 : 2) : pr ? 1 : 0;
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
          Read the problem, name the pattern, then the main Python data structure. When you miss, you get a full
          explanation of the clue you should have spotted and why your pick doesn't fit.
        </p>
        <p className="mt-2 text-xs text-zinc-500">{queue.length} problems in this set · keys <Kbd>1</Kbd>–<Kbd>4</Kbd></p>
        <div className="mt-5 flex flex-wrap justify-center gap-2">
          <Button onClick={() => { setTimed(false); setRunning(true); }}><Play size={15} />Practice, no timer <Kbd>Enter</Kbd></Button>
          <Button variant="subtle" onClick={() => { setTimed(true); setRunning(true); }}><Timer size={15} />Speed round, {LIMIT}s each</Button>
        </div>
        <p className="mt-3 text-xs text-zinc-500">New to patterns? Start untimed. Switch to speed rounds once you get most right.</p>
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
        <div className={`h-full transition-[width] duration-100 ${!timed ? 'bg-transparent' : pct > 0.5 ? 'bg-emerald-500' : pct > 0.2 ? 'bg-amber-500' : 'bg-rose-500'}`} style={{ width: `${(done ? 0 : pct) * 100}%` }} />
      </div>

      <Card className="p-6">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <DiffTag d={ex.difficulty} />
          <CompanyTags ids={ex.companies} />
          {!done && timed && <span className="ml-auto font-mono text-sm text-zinc-300">{left.toFixed(1)}s</span>}
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

      {done && <Explain ex={ex} pat={pat} ds={ds} timedOut={timedOut} showCode={showCode} setShowCode={setShowCode} onLearn={onLearn} next={next} />}
    </div>
  );
}

function Explain({ ex, pat, ds, timedOut, showCode, setShowCode, onLearn, next }: {
  ex: PatternExercise; pat: PatternId | null; ds: string | null; timedOut: boolean;
  showCode: boolean; setShowCode: (b: boolean) => void; onLearn?: (id: string) => void; next: () => void;
}) {
  const pr = pat === ex.answerPattern, dr = ds === ex.answerDS;
  const lessonId = LESSON_FOR_PATTERN[ex.answerPattern];
  const lesson = lessonId ? LESSON_BY_ID[lessonId] : undefined;
  const both = pr && dr;
  return (
    <Card className="mt-4 p-5">
      <div className="mb-3 flex flex-wrap items-center gap-2 text-sm font-medium">
        {both
          ? <><CheckCircle2 size={16} className="text-emerald-400" /><span className="text-emerald-300">Both right</span></>
          : pr ? <><CheckCircle2 size={16} className="text-amber-400" /><span className="text-amber-300">Pattern right, data structure off</span></>
          : <><XCircle size={16} className="text-rose-400" /><span className="text-rose-300">{timedOut ? 'Time\u2019s up' : 'Not quite'}</span></>}
        <span className="text-zinc-400">Answer: <span className="hl text-zinc-100">{PATTERN_NAME[ex.answerPattern]}</span> with <span className="hl font-mono text-zinc-100">{ex.answerDS}</span></span>
      </div>
      <p className="leading-relaxed text-zinc-200">{ex.why}</p>

      {!both && (
        <div className="mt-4 space-y-3 border-t border-zinc-800 pt-4 text-[15px] leading-relaxed">
          <div>
            <h4 className="font-semibold text-zinc-100">The clue you should look for</h4>
            <p className="text-zinc-300">{PATTERN_NAME[ex.answerPattern]} fits when {FITS_WHEN[ex.answerPattern]}. Look at the constraint <span className="font-mono text-sky-300">{ex.constraints}</span>: the target complexity rules out the brute force and points here.</p>
            {lesson && <ul className="mt-2 list-disc space-y-0.5 pl-5 text-zinc-400 marker:text-zinc-600">{lesson.signals.slice(0, 3).map((x) => <li key={x}>{x}</li>)}</ul>}
          </div>
          {pat && !pr && (
            <div>
              <h4 className="font-semibold text-zinc-100">Why not {PATTERN_NAME[pat]}?</h4>
              <p className="text-zinc-300">{PATTERN_NAME[pat]} is for when {FITS_WHEN[pat]}. This problem doesn't have that shape, so it would either be slower than the target or give wrong answers.</p>
            </div>
          )}
          {!dr && (
            <div>
              <h4 className="font-semibold text-zinc-100">About the data structure</h4>
              <p className="text-zinc-300">{ds ? <>You picked <span className="font-mono">{ds}</span>, which is for {DS_FITS[ds] ?? 'a different job'}. </> : null}Here the work is done by <span className="font-mono">{ex.answerDS}</span>, used for {DS_FITS[ex.answerDS] ?? 'this job'}.</p>
            </div>
          )}
          {lesson && (
            <div>
              <button onClick={() => setShowCode(!showCode)} className="text-sm font-medium text-violet-300 hover:underline">{showCode ? 'Hide' : 'Show'} the {lesson.name.toLowerCase()} template</button>
              {showCode && <pre className="mt-2 overflow-x-auto rounded-md border border-zinc-800 bg-zinc-950 p-3 font-mono text-[13px] leading-relaxed">{lesson.template.split('\n').slice(0, 14).map((line, i) => <div key={i}>{line ? highlight(line, `x${i}`) : '\u00a0'}</div>)}</pre>}
            </div>
          )}
        </div>
      )}
      <div className="mt-4 flex flex-wrap gap-2">
        <Button onClick={next}>Next<Kbd>Enter</Kbd></Button>
        {!both && lesson && onLearn && <Button variant="subtle" onClick={() => onLearn(lesson.id)}><BookOpen size={15} />Learn {lesson.name}</Button>}
      </div>
    </Card>
  );
}
