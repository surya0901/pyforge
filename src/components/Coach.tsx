import { Clock, Copy, ExternalLink, Sparkles } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { PLAYBOOKS } from '../data/companies';
import { COMPANIES, COMPANY_NAME } from '../data/meta';
import { areaStats, buildPlan, claudePrompt, readiness } from '../lib/coach';
import { getLocal, setLocal, streak } from '../lib/storage';
import type { CompanyId, Mode, Progress } from '../types';
import { Bar, Button, Card, SectionTitle } from './ui';
import { CoachPanel } from './AI';
import { nextProblems } from './StudyPath';
import { LESSON_BY_ID, LESSONS } from '../data/lessons';
import { lessonForSlug, patternsSummary } from '../lib/coverage';

interface Props {
  progress: Progress;
  solved: Set<string>;
  open: (m: Mode, opts?: { deck?: string; company?: CompanyId | 'all' }) => void;
  onLearn: (lessonId?: string) => void;
}

const TARGET_KEY = 'pyforge.targets.v1';

function greeting() {
  const h = new Date().getHours();
  return h < 5 ? 'Late session' : h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening';
}

export default function Coach({ progress, open, solved, onLearn }: Props) {
  const nextNc = nextProblems(solved, 1)[0];
  const ncLessonId = nextNc ? lessonForSlug(nextNc.slug) : undefined;
  const ncLesson = ncLessonId ? LESSON_BY_ID[ncLessonId] : undefined;
  const readFirst = ncLesson && !progress.lessons?.[ncLesson.id]?.opened ? ncLesson : undefined;
  const pat = patternsSummary(progress, solved);
  const nextLesson = pat.rows.find((r) => !r.cov.learned)?.lesson ?? LESSONS[0];
  const [targets, setTargets] = useState<CompanyId[]>(() => getLocal(TARGET_KEY, [] as CompanyId[]));
  const [copied, setCopied] = useState(false);
  useEffect(() => setLocal(TARGET_KEY, targets), [targets]);

  const stats = useMemo(() => areaStats(progress), [progress]);
  const { plan, strengths, gaps, dueCards } = useMemo(() => buildPlan(progress, targets), [progress, targets]);
  const shown = targets.length ? targets : PLAYBOOKS.map((p) => p.id);
  const ranked = shown.map((id) => ({ id, ...readiness(id, stats) })).sort((a, b) => b.score - a.score);
  const totalMin = plan.reduce((s, p) => s + p.minutes, 0);
  const days = streak(progress.days);
  const anyPractice = Object.keys(progress.cards).length > 0 || progress.math.length > 0;

  const mistakes = Object.entries(progress.mistakes).sort((a, b) => b[1] - a[1]).slice(0, 8);
  const prompt = claudePrompt(progress, targets.map((t) => COMPANY_NAME[t]), mistakes);
  const copy = async () => {
    try { await navigator.clipboard.writeText(prompt); setCopied(true); setTimeout(() => setCopied(false), 2500); } catch { /* clipboard blocked */ }
  };

  const toggle = (id: CompanyId) => setTargets((t) => (t.includes(id) ? t.filter((x) => x !== id) : [...t, id]));

  return (
    <div className="space-y-10">
      {/* Hero: what to do right now */}
      <section>
        <p className="text-zinc-500">{greeting()}{days > 0 ? `. You are on a ${days}-day streak.` : '.'}</p>
        <h1 className="mt-1 max-w-[22ch] text-[42px] font-bold leading-[1.05] tracking-[-0.025em] text-zinc-100">
          <span className="hl">{totalMin} minutes</span> is enough to move the needle today.
        </h1>
        {readFirst && (
          <button onClick={() => onLearn(readFirst.id)} className="mt-6 flex w-full flex-wrap items-center gap-3 rounded-md border border-amber-500/70 bg-amber-500/5 p-4 text-left transition-colors hover:bg-amber-500/10">
            <div className="flex-1">
              <div className="text-sm text-zinc-500">Before {nextNc!.name}, learn the pattern it uses (about 8 min)</div>
              <div className="text-lg font-semibold text-zinc-100">{readFirst.name}</div>
            </div>
            <span className="font-medium text-amber-300">Read the lesson</span>
          </button>
        )}
        {nextNc && (
          <a href={nextNc.url} target="_blank" rel="noreferrer"
            className={`${readFirst ? 'mt-3' : 'mt-6'} flex flex-wrap items-center gap-3 rounded-md border border-violet-500 bg-zinc-900 p-4 transition-colors hover:bg-zinc-950`}>
            <div className="flex-1">
              <div className="text-sm text-zinc-500">First, solve on NeetCode · {nextNc.section} · {solved.size}/150 done</div>
              <div className="text-lg font-semibold text-zinc-100">{nextNc.name} <span className="text-sm font-normal text-zinc-500">{nextNc.difficulty}</span></div>
            </div>
            <span className="inline-flex items-center gap-1.5 font-medium text-violet-300">Open <ExternalLink size={14} /></span>
          </a>
        )}
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          {plan.map((p, i) => {
            const st = stats.find((x) => x.area === p.area);
            // Low accuracy on pattern drills usually means the patterns were never taught. Send them to the lessons first.
            const toLessons = p.area === 'patterns' && !!st && st.attempts >= 3 && st.accuracy < 0.5;
            return (
            <button key={i} onClick={() => (toLessons ? onLearn(nextLesson.id) : open(p.mode, { deck: p.deck }))}
              className="group rounded-md border border-zinc-800 bg-zinc-900 p-4 text-left transition-colors hover:border-violet-500">
              <div className="mb-2 flex items-center gap-1.5 text-sm text-zinc-500"><Clock size={14} />{p.minutes} min</div>
              <div className="text-lg font-semibold leading-snug text-zinc-100 group-hover:text-violet-300">{p.title}</div>
              <p className="mt-1.5 text-sm leading-relaxed text-zinc-400">{p.why}{toLessons ? ` Start with the ${nextLesson.name} lesson, then drill again.` : ''}</p>
            </button>
            );
          })}
        </div>
        <button onClick={() => onLearn()} className="mt-3 flex w-full items-center gap-4 rounded-md border border-zinc-800 bg-zinc-900 p-4 text-left transition-colors hover:border-violet-500">
          <div className="flex-1">
            <div className="text-sm text-zinc-500">Patterns learned</div>
            <div className="text-lg font-semibold text-zinc-100"><span className="tnum">{pat.learned}</span> of {LESSONS.length} <span className="text-sm font-normal text-zinc-500">· next up: {nextLesson.name}</span></div>
          </div>
          <div className="w-40"><Bar value={pat.avg} /></div>
        </button>
        {!anyPractice && <p className="mt-3 text-sm text-zinc-500">The plan sharpens after your first few sessions. It looks at what your target companies care about and where your accuracy is low.</p>}
      </section>

      {/* Targets */}
      <section>
        <SectionTitle aside={<span className="text-sm text-zinc-500">{targets.length ? `${targets.length} selected` : 'All companies'}</span>}>Which companies are you aiming for?</SectionTitle>
        <div className="flex flex-wrap gap-2">
          {COMPANIES.map((c) => {
            const on = targets.includes(c.id);
            return (
              <button key={c.id} onClick={() => toggle(c.id)} aria-pressed={on}
                className={`rounded-full border px-3 py-1 transition-colors ${on ? 'border-violet-500 bg-violet-600 text-white' : 'border-zinc-800 bg-zinc-900 text-zinc-300 hover:border-zinc-600'}`}>
                {c.name}
              </button>
            );
          })}
        </div>
      </section>

      <div className="grid gap-8 lg:grid-cols-[1.2fr_1fr]">
        {/* Skill map */}
        <section>
          <SectionTitle>Where you stand</SectionTitle>
          <Card className="divide-y divide-zinc-800">
            {stats.map((s) => {
              const isGap = gaps.some((g) => g.area === s.area);
              const isStrong = strengths.some((g) => g.area === s.area);
              return (
                <div key={s.area} className="grid grid-cols-[1fr_120px] items-center gap-4 px-4 py-2.5">
                  <div>
                    <div className="flex items-center gap-2 text-zinc-100">
                      {isStrong ? <span className="hl">{s.name}</span> : <span className={isGap ? 'pen' : ''}>{s.name}</span>}
                    </div>
                    <div className="text-xs text-zinc-500">
                      {s.attempts === 0 ? 'Not started' : s.area === 'math' ? `${s.attempts} sprints` : `${s.seen} of ${s.items} seen, ${Math.round(s.accuracy * 100)}% accurate`}
                    </div>
                  </div>
                  <Bar value={s.mastery} color={isGap ? 'bg-rose-500' : isStrong ? 'bg-amber-500' : 'bg-violet-500'} />
                </div>
              );
            })}
          </Card>
          <p className="mt-2 text-sm text-zinc-500"><span className="hl">Highlighted</span> areas are strengths (75%+ accuracy). <span className="pen">Underlined</span> areas are real gaps (under 60%).</p>
        </section>

        <div className="space-y-8">
          {/* Readiness */}
          <section>
            <SectionTitle>Company readiness</SectionTitle>
            <div className="space-y-3">
              {ranked.map((r) => {
                const weakest = [...r.parts].sort((a, b) => b.weight * (1 - b.mastery) - a.weight * (1 - a.mastery))[0];
                return (
                  <button key={r.id} onClick={() => open('companies', { company: r.id })} className="block w-full text-left">
                    <div className="mb-1 flex items-baseline justify-between">
                      <span className="font-medium text-zinc-100">{COMPANY_NAME[r.id]}</span>
                      <span className="tnum text-sm text-zinc-400">{Math.round(r.score * 100)}%</span>
                    </div>
                    <Bar value={r.score} />
                    <div className="mt-1 text-xs text-zinc-500">Biggest lever: {weakest && stats.find((s) => s.area === weakest.area)?.name.toLowerCase()}</div>
                  </button>
                );
              })}
            </div>
          </section>

          <section><CoachPanel progress={progress} solved={solved} targets={targets} /></section>

          {/* Deeper AI review */}
          <section>
            <Card className="p-5">
              <h3 className="flex items-center gap-2 text-lg font-semibold text-zinc-100"><Sparkles size={17} className="text-amber-400" />Get a deeper review from Claude</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-zinc-400">
                The plan above is computed on your device. For a written review, a two-week schedule and live quizzing on your weakest area, send your stats to Claude.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Button onClick={copy}><Copy size={15} />{copied ? 'Copied' : 'Copy my stats'}</Button>
                <a href={`https://claude.ai/new?q=${encodeURIComponent(prompt)}`} target="_blank" rel="noreferrer"
                  className="inline-flex items-center gap-2 rounded-md border border-zinc-800 bg-zinc-900 px-3.5 py-1.5 font-medium text-zinc-200 hover:border-zinc-600">Open in Claude</a>
              </div>
              {dueCards > 0 && <p className="mt-3 text-xs text-zinc-500">{dueCards} flashcards are waiting for review.</p>}
            </Card>
          </section>
        </div>
      </div>
    </div>
  );
}
