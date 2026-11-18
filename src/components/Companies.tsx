import { ExternalLink } from 'lucide-react';
import { useMemo, useState } from 'react';
import { AREA_NAME, PLAYBOOKS, RESOURCES } from '../data/companies';
import { COMPANIES, COMPANY_NAME } from '../data/meta';
import { AREA_DECK, AREA_MODE, areaStats, readiness } from '../lib/coach';
import type { CompanyId, Mode, Progress } from '../types';
import { Bar, Button, Card, PageTitle, SectionTitle } from './ui';

interface Props {
  progress: Progress;
  initial?: CompanyId | 'all';
  open: (m: Mode, opts?: { deck?: string; company?: CompanyId | 'all' }) => void;
}

export default function Companies({ progress, initial, open }: Props) {
  const [id, setId] = useState<CompanyId>(initial && initial !== 'all' ? initial : 'citadel');
  const pb = PLAYBOOKS.find((p) => p.id === id)!;
  const stats = useMemo(() => areaStats(progress), [progress]);
  const r = readiness(id, stats);
  const tier = COMPANIES.find((c) => c.id === id)!.tier;

  return (
    <div>
      <PageTitle sub="What each loop usually looks like for new grads, what it rewards, and how ready you are. Loops change and differ by team, so confirm your format with your recruiter.">Company playbooks</PageTitle>

      <div className="mb-8 flex flex-wrap gap-x-1 gap-y-2 border-b border-zinc-800 pb-px">
        {COMPANIES.map((c) => (
          <button key={c.id} onClick={() => setId(c.id)}
            className={`-mb-px border-b-2 px-3 py-2 transition-colors ${id === c.id ? 'border-violet-500 font-semibold text-zinc-100' : 'border-transparent text-zinc-500 hover:text-zinc-200'}`}>
            {c.name}
          </button>
        ))}
      </div>

      <div className="grid gap-10 lg:grid-cols-[1.35fr_1fr]">
        <div className="space-y-8">
          <div>
            <p className="text-sm text-zinc-500">{tier === 'quant' ? 'Quant trading firm' : 'Big tech and frontier AI'}</p>
            <h2 className="mt-1 text-[32px] font-bold leading-tight tracking-[-0.02em] text-zinc-100">{COMPANY_NAME[id]}</h2>
            <p className="mt-2 max-w-[60ch] text-lg leading-relaxed text-zinc-300">{pb.tagline}</p>
          </div>

          <section>
            <SectionTitle>The usual loop</SectionTitle>
            <ol className="space-y-2">
              {pb.loop.map((s, i) => (
                <li key={i} className="flex gap-3">
                  <span className="tnum mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-zinc-700 text-sm text-zinc-400">{i + 1}</span>
                  <span className="leading-relaxed text-zinc-200">{s}</span>
                </li>
              ))}
            </ol>
          </section>

          <section>
            <SectionTitle>What they test</SectionTitle>
            <ul className="list-disc space-y-1 pl-5 text-zinc-200 marker:text-zinc-600">
              {pb.focus.map((f) => <li key={f}>{f}</li>)}
            </ul>
          </section>

          <section>
            <SectionTitle>What they value</SectionTitle>
            <p className="max-w-[65ch] leading-relaxed text-zinc-200">{pb.values}</p>
          </section>

          <section>
            <SectionTitle>Tips</SectionTitle>
            <ul className="space-y-2">
              {pb.tips.map((t) => <li key={t} className="border-l-2 border-amber-500 pl-3 leading-relaxed text-zinc-200">{t}</li>)}
            </ul>
          </section>

          <section>
            <SectionTitle>Read before your interview</SectionTitle>
            <ul className="space-y-1.5">
              {pb.links.map((l) => (
                <li key={l.url}><a href={l.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 text-violet-300 underline decoration-violet-500/40 underline-offset-4 hover:decoration-violet-500">{l.label}<ExternalLink size={13} /></a></li>
              ))}
            </ul>
          </section>
        </div>

        <div className="space-y-6 lg:sticky lg:top-24 lg:self-start">
          <Card className="p-5">
            <div className="flex items-baseline justify-between">
              <h3 className="text-lg font-semibold text-zinc-100">Your readiness</h3>
              <span className="tnum text-3xl font-bold text-zinc-100"><span className="hl">{Math.round(r.score * 100)}%</span></span>
            </div>
            <p className="mb-4 mt-1 text-sm text-zinc-500">Weighted by how much {COMPANY_NAME[id]} leans on each skill. Click a row to practice it.</p>
            <div className="space-y-3">
              {r.parts.map((p) => (
                <button key={p.area} onClick={() => open(AREA_MODE[p.area], { company: id, deck: AREA_DECK[p.area] })} className="block w-full text-left">
                  <div className="mb-1 flex justify-between text-sm">
                    <span className="text-zinc-200">{AREA_NAME[p.area]}</span>
                    <span className="tnum text-zinc-500">{Math.round(p.weight * 100)}% of loop</span>
                  </div>
                  <Bar value={p.mastery} color={p.mastery > 0.7 ? 'bg-emerald-500' : 'bg-violet-500'} />
                </button>
              ))}
            </div>
            <div className="mt-5 flex flex-wrap gap-2">
              <Button onClick={() => open('syntax', { company: id })}>Practice {COMPANY_NAME[id]} problems</Button>
              <Button variant="subtle" onClick={() => open('cards', { company: id })}>Flashcards</Button>
            </div>
          </Card>

          <Card className="p-5">
            <h3 className="mb-3 font-semibold text-zinc-100">Good free resources</h3>
            <ul className="space-y-3">
              {RESOURCES.map((x) => (
                <li key={x.url}>
                  <a href={x.url} target="_blank" rel="noreferrer" className="font-medium text-violet-300 hover:underline">{x.label}</a>
                  <p className="text-sm text-zinc-500">{x.note}</p>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </div>
    </div>
  );
}
