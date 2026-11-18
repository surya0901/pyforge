import { Sparkles } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { COMPANY_NAME } from '../data/meta';
import { NC_SECTIONS, NEETCODE } from '../data/neetcode';
import { areaStats } from '../lib/coach';
import { getSample, type SampleFn } from '../lib/cloud';
import type { CompanyId, Progress } from '../types';
import { Button, Card } from './ui';

export function useSample() {
  const [sample, setSample] = useState<SampleFn | null | undefined>(undefined);
  useEffect(() => { getSample().then(setSample); }, []);
  return sample; // undefined = still checking, null = not available here
}

/** Renders plain text with blank-line paragraphs and "- " bullets, no markdown library. */
function Prose({ text }: { text: string }) {
  const blocks = text.split(/\n{2,}/);
  return (
    <div className="space-y-3 leading-relaxed text-zinc-200">
      {blocks.map((b, i) => {
        const lines = b.split('\n');
        if (lines.every((l) => /^\s*[-•*]\s/.test(l))) {
          return <ul key={i} className="list-disc space-y-1 pl-5">{lines.map((l, k) => <li key={k}>{l.replace(/^\s*[-•*]\s/, '').replace(/\*\*/g, '')}</li>)}</ul>;
        }
        const isHead = lines.length === 1 && b.length < 60 && !/[.!?]$/.test(b.trim());
        return isHead
          ? <h4 key={i} className="pt-1 font-semibold text-zinc-100">{b.replace(/^#+\s*/, '').replace(/\*\*/g, '')}</h4>
          : <p key={i} className="whitespace-pre-line">{b.replace(/\*\*/g, '')}</p>;
      })}
    </div>
  );
}

function useStream() {
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const ctrl = useRef<AbortController | null>(null);
  const run = async (sample: SampleFn, prompt: string) => {
    ctrl.current?.abort();
    ctrl.current = new AbortController();
    setBusy(true); setErr(''); setText('');
    try {
      const r = await sample(prompt, { onText: ({ text: t }: { text: string }) => setText(t), signal: ctrl.current.signal, cache: false });
      setText(r.text);
    } catch (e) {
      const code = (e as { code?: string }).code;
      setErr(code === 'rate_limited' ? 'Claude is busy right now. Try again in a minute.' : code === 'not_granted' ? 'Allow Claude access for this page to use the coach.' : 'Could not reach Claude. Try again.');
    } finally {
      setBusy(false);
    }
  };
  return { text, busy, err, run };
}

export function CoachPanel({ progress, solved, targets }: { progress: Progress; solved: Set<string>; targets: CompanyId[] }) {
  const sample = useSample();
  const { text, busy, err, run } = useStream();
  if (sample === null) return null;

  const ask = () => {
    if (!sample) return;
    const stats = areaStats(progress).map((s) => `- ${s.name}: ${s.attempts} attempts, ${Math.round(s.accuracy * 100)}% accurate, mastery ${Math.round(s.mastery * 100)}%`).join('\n');
    const nc = NC_SECTIONS.map((sec) => {
      const all = NEETCODE.filter((p) => p.section === sec);
      return `- ${sec}: ${all.filter((p) => solved.has(p.slug)).length}/${all.length}`;
    }).join('\n');
    const slips = Object.entries(progress.mistakes).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([k, v]) => `${k} ×${v}`).join(', ') || 'none yet';
    const companies = targets.length ? targets.map((t) => COMPANY_NAME[t]).join(', ') : 'Citadel, HRT, Jane Street, Meta, Microsoft, Amazon, Google, Netflix, Apple, Nvidia, OpenAI';
    run(sample, `You are a direct, encouraging interview coach for a new grad software engineer (Computer Engineering M.S., Python). Targets: ${companies}.

Practice app stats:
${stats}

NeetCode 150 progress by section (${solved.size}/150 total):
${nc}

Most frequent mistakes: ${slips}

Write, in plain text with short headings and "- " bullets, no markdown symbols:
Where you stand: 2 honest sentences.
Strengths: up to 3 bullets (say "not enough data yet" if attempts are low).
Biggest gaps for these companies: 3 bullets, most important first.
Today (about 45 minutes): 3 concrete steps naming specific NeetCode problems or app modes.
This week: 4 bullets.
Keep it under 250 words.`);
  };

  return (
    <Card className="p-5">
      <h3 className="flex items-center gap-2 text-lg font-semibold text-zinc-100"><Sparkles size={17} className="text-amber-400" />Ask your Claude coach</h3>
      <p className="mt-1 text-sm text-zinc-400">Claude reads your drill stats, NeetCode progress and recurring mistakes, then tells you where you are lacking and what to do today.</p>
      <Button className="mt-3" onClick={ask} disabled={!sample || busy}>{busy ? 'Thinking…' : text ? 'Ask again' : 'Analyze my progress'}</Button>
      {err && <p className="mt-3 text-sm text-rose-300">{err}</p>}
      {text && <div className="mt-4 border-t border-zinc-800 pt-4"><Prose text={text} /></div>}
    </Card>
  );
}

export function BehavioralPractice({ question, company }: { question: string; company?: CompanyId }) {
  const sample = useSample();
  const [answer, setAnswer] = useState('');
  const { text, busy, err, run } = useStream();
  if (sample === null) return <p className="text-sm text-zinc-500">Answer grading by Claude works in the hosted version of pyforge.</p>;

  const grade = () => {
    if (!sample || answer.trim().length < 40) return;
    const who = company ? COMPANY_NAME[company] : 'a top tech company';
    run(sample, `You are a strict but kind behavioral interviewer at ${who} hiring a new grad software engineer.
Question: "${question}"
Candidate's answer (spoken style, may be rough):
"""${answer.slice(0, 4000)}"""

Grade it. Plain text, short headings, "- " bullets, no markdown symbols:
Score: X/10, one sentence why.
STAR check: say which of Situation, Task, Action, Result are clear or missing.
What ${who} interviewers would like: 2 bullets tied to the company's known values.
Fix these: 3 specific bullets (use "I" not "we", add a number to the result, cut filler...).
Tighter version: rewrite the answer in about 120 words using ONLY facts the candidate gave; mark any missing detail as [add: ...] instead of inventing it.`);
  };

  return (
    <div className="space-y-3">
      <textarea value={answer} onChange={(e) => setAnswer(e.target.value)} rows={5}
        placeholder="Type your answer the way you would say it out loud…"
        className="w-full resize-y rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 text-zinc-100 outline-none placeholder:text-zinc-600 focus:border-violet-500" />
      <div className="flex items-center gap-3">
        <Button onClick={grade} disabled={!sample || busy || answer.trim().length < 40}>{busy ? 'Grading…' : 'Get feedback from Claude'}</Button>
        {answer.trim().length < 40 && <span className="text-sm text-zinc-500">Write at least a few sentences first.</span>}
      </div>
      {err && <p className="text-sm text-rose-300">{err}</p>}
      {text && <div className="rounded-md border border-zinc-800 bg-zinc-950 p-4"><Prose text={text} /></div>}
    </div>
  );
}
