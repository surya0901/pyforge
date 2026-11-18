import { useEffect, useRef, useState } from 'react';
import type { Progress } from '../types';
import { Button, Card, PageTitle } from './ui';

const SECONDS = 120;
type Q = { text: string; answer: number };

const r = (a: number, b: number) => a + Math.floor(Math.random() * (b - a + 1));

/** Zetamac-style mix, tuned toward quant first rounds. */
function makeQ(): Q {
  const kind = r(0, 5);
  if (kind === 0) { const a = r(12, 99), b = r(12, 99); return { text: `${a} + ${b}`, answer: a + b }; }
  if (kind === 1) { const a = r(100, 999), b = r(10, 99); return { text: `${a} − ${b}`, answer: a - b }; }
  if (kind === 2) { const a = r(2, 12), b = r(11, 99); return { text: `${a} × ${b}`, answer: a * b }; }
  if (kind === 3) { const b = r(3, 12), q = r(4, 40); return { text: `${b * q} ÷ ${b}`, answer: q }; }
  if (kind === 4) { const a = r(11, 29), b = r(11, 19); return { text: `${a} × ${b}`, answer: a * b }; }
  const pct = [10, 15, 20, 25, 40, 50, 75][r(0, 6)], base = r(1, 20) * 20; return { text: `${pct}% of ${base}`, answer: (pct * base) / 100 };
}

export default function MentalMath({ progress, onFinish }: { progress: Progress; onFinish: (score: number) => void }) {
  const [state, setState] = useState<'idle' | 'run' | 'done'>('idle');
  const [q, setQ] = useState<Q>(makeQ);
  const [val, setVal] = useState('');
  const [score, setScore] = useState(0);
  const [left, setLeft] = useState(SECONDS);
  const [flash, setFlash] = useState(false);
  const end = useRef(0);
  const input = useRef<HTMLInputElement>(null);
  const scoreRef = useRef(0);

  const start = () => {
    setScore(0); scoreRef.current = 0; setVal(''); setQ(makeQ()); setLeft(SECONDS);
    end.current = Date.now() + SECONDS * 1000;
    setState('run');
    setTimeout(() => input.current?.focus(), 0);
  };

  useEffect(() => {
    if (state !== 'run') return;
    const t = setInterval(() => {
      const l = Math.max(0, (end.current - Date.now()) / 1000);
      setLeft(l);
      if (l <= 0) { clearInterval(t); setState('done'); onFinish(scoreRef.current); }
    }, 200);
    return () => clearInterval(t);
  }, [state, onFinish]);

  useEffect(() => {
    const h = (e: KeyboardEvent) => { if (state !== 'run' && e.key === 'Enter') { e.preventDefault(); start(); } };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  });

  const onChange = (v: string) => {
    setVal(v);
    if (v.trim() !== '' && Number(v) === q.answer) {
      scoreRef.current += 1;
      setScore(scoreRef.current);
      setQ(makeQ());
      setVal('');
      setFlash(true);
      setTimeout(() => setFlash(false), 160);
    }
  };

  const history = progress.math.slice(-12);
  const best = progress.math.reduce((m, x) => Math.max(m, x.score), 0);
  const maxBar = Math.max(40, ...history.map((h) => h.score));

  return (
    <div>
      <PageTitle sub="Two minutes of arithmetic. Answers submit themselves when correct. Quant first rounds reward exactly this speed, and it makes a good break between longer sessions.">Mental math sprint</PageTitle>
      <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
        <Card className="flex min-h-[340px] flex-col items-center justify-center p-8">
          {state === 'idle' && (
            <>
              <p className="mb-5 text-zinc-400">Addition, subtraction, times tables to 12 × 99, teen products, division, percentages.</p>
              <Button onClick={start}>Start sprint</Button>
            </>
          )}
          {state === 'run' && (
            <>
              <div className="tnum mb-6 flex w-full justify-between text-zinc-500">
                <span>{Math.ceil(left)} s left</span>
                <span>{score} solved</span>
              </div>
              <div className={`tnum mb-6 text-6xl font-bold tracking-tight text-zinc-100 transition-colors ${flash ? 'text-emerald-400' : ''}`}>{q.text}</div>
              <input ref={input} value={val} onChange={(e) => onChange(e.target.value.replace(/[^\d.-]/g, ''))} inputMode="decimal" autoFocus
                aria-label="Your answer"
                className="tnum w-48 rounded-md border-2 border-zinc-700 bg-zinc-950 px-3 py-2 text-center text-3xl font-semibold text-zinc-100 outline-none focus:border-violet-500" />
              <div className="mt-8 h-1 w-full overflow-hidden rounded-full bg-zinc-800"><div className="h-full bg-amber-500" style={{ width: `${(left / SECONDS) * 100}%` }} /></div>
            </>
          )}
          {state === 'done' && (
            <>
              <p className="text-zinc-400">Time.</p>
              <p className="tnum my-2 text-7xl font-bold text-zinc-100"><span className="hl">{score}</span></p>
              <p className="mb-6 text-zinc-400">{score >= best && score > 0 ? 'A new personal best.' : `Personal best is ${best}.`} Many candidates aim for 40+ before quant first rounds.</p>
              <Button onClick={start}>Go again</Button>
            </>
          )}
        </Card>
        <Card className="p-5">
          <h3 className="font-semibold text-zinc-100">Recent sprints</h3>
          <p className="mb-4 text-sm text-zinc-500">Best: {best || 'none yet'}</p>
          {history.length === 0 ? <p className="text-sm text-zinc-500">Your scores will chart here.</p> : (
            <div className="flex h-40 items-end gap-1.5">
              {history.map((h, i) => (
                <div key={i} className="flex flex-1 flex-col items-center gap-1" title={new Date(h.at).toLocaleString()}>
                  <span className="tnum text-[11px] text-zinc-500">{h.score}</span>
                  <div className={`w-full rounded-t-sm ${h.score === best ? 'bg-amber-500' : 'bg-violet-500/70'}`} style={{ height: `${(h.score / maxBar) * 120}px` }} />
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
