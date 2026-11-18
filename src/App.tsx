import { BarChart3, BookOpen, Briefcase, Bug, Calculator, Compass, Keyboard, Layers, Map as MapIcon, Moon, Network, Sun, Target } from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import BugHunter from './components/BugHunter';
import Coach from './components/Coach';
import Companies from './components/Companies';
import Dashboard from './components/Dashboard';
import DesignStudio from './components/DesignStudio';
import Flashcards from './components/Flashcards';
import MentalMath from './components/MentalMath';
import PatternDrill from './components/PatternDrill';
import { ReferenceContent, ReferenceDrawer } from './components/Reference';
import StudyPath from './components/StudyPath';
import SyntaxDrill from './components/SyntaxDrill';
import { getDB, pullProgress, pushProgress, watchNeetcode, type NeetcodeStatus } from './lib/cloud';
import { Empty, Kbd, PageTitle } from './components/ui';
import { BUGS, PATTERN_DRILLS, SYNTAX } from './data';
import { COMPANIES, PATTERNS } from './data/meta';
import { buildQueue, emptyProgress, filterItems, getLocal, loadProgress, logMath, review, saveProgress, setLocal, streak } from './lib/storage';
import type { CompanyId, Mode, PatternId, Progress } from './types';

type NavItem = { id: Mode; label: string; icon: typeof Keyboard; key: string };
const GROUPS: { name: string; items: NavItem[] }[] = [
  { name: '', items: [{ id: 'coach', label: 'Today', icon: Compass, key: 't' }, { id: 'path', label: 'Study path', icon: MapIcon, key: 'n' }] },
  { name: 'Coding drills', items: [
    { id: 'syntax', label: 'Syntax recall', icon: Keyboard, key: 's' },
    { id: 'bug', label: 'Bug hunter', icon: Bug, key: 'b' },
    { id: 'pattern', label: 'Pattern speed', icon: Target, key: 'p' },
    { id: 'math', label: 'Mental math', icon: Calculator, key: 'm' },
  ] },
  { name: 'Interview prep', items: [
    { id: 'design', label: 'System design', icon: Network, key: 'd' },
    { id: 'cards', label: 'Flashcards', icon: Layers, key: 'f' },
    { id: 'companies', label: 'Companies', icon: Briefcase, key: 'c' },
  ] },
  { name: 'You', items: [
    { id: 'dashboard', label: 'Stats', icon: BarChart3, key: 'g' },
    { id: 'reference', label: 'Python reference', icon: BookOpen, key: 'r' },
  ] },
];
const ALL_NAV = GROUPS.flatMap((g) => g.items);

const DRILL_INTRO: Partial<Record<Mode, { title: string; sub: string }>> = {
  syntax: { title: 'Syntax recall', sub: 'You know the algorithm. Type the exact Python. Each blank says what it should do, and wrong answers tell you why.' },
  bug: { title: 'Bug hunter', sub: 'Read code like a reviewer. Flag every broken line, then pick the fix. This is the skill AI-assisted and code-comprehension rounds test.' },
  pattern: { title: 'Pattern speed', sub: 'Fifteen seconds to name the approach and the data structure from the constraints alone.' },
};

const THEME_KEY = 'pyforge.theme';
const readTheme = () => { try { return localStorage.getItem(THEME_KEY) === 'dark'; } catch { return false; } };

export default function App() {
  const [progress, setProgress] = useState<Progress>(loadProgress);
  const [mode, setMode] = useState<Mode>('coach');
  const [pattern, setPattern] = useState<PatternId | 'all'>('all');
  const [company, setCompany] = useState<CompanyId | 'all'>('all');
  const [deck, setDeck] = useState<string | undefined>();
  const [drawer, setDrawer] = useState(false);
  const [session, setSession] = useState(0);
  const [dark, setDark] = useState(readTheme);
  const [focus, setFocus] = useState<string | undefined>();
  const [ncCloud, setNcCloud] = useState<NeetcodeStatus | null>(null);
  const [cloud, setCloud] = useState(false);
  const [ncLocal, setNcLocal] = useState<string[]>(() => getLocal('pyforge.neetcode.local', ['duplicate-integer', 'is-anagram', 'two-integer-sum']));
  const [pace, setPaceState] = useState<number>(() => getLocal('pyforge.pace', 2));
  const setPace = (n: number) => { setPaceState(n); setLocal('pyforge.pace', n); };
  const solved = useMemo(() => new Set(ncCloud ? ncCloud.solved : ncLocal), [ncCloud, ncLocal]);
  const toggleLocal = (slug: string) => setNcLocal((xs) => {
    const next = xs.includes(slug) ? xs.filter((x) => x !== slug) : [...xs, slug];
    setLocal('pyforge.neetcode.local', next);
    return next;
  });

  // Cloud (claude.ai artifact only): pull newer progress once, then follow the NeetCode feed live.
  useEffect(() => {
    let unsub = () => {};
    (async () => {
      const db = await getDB();
      if (!db) return;
      setCloud(true);
      const newer = await pullProgress(loadProgress());
      if (newer) setProgress(newer);
      unsub = await watchNeetcode(setNcCloud);
    })();
    return () => unsub();
  }, []);

  useEffect(() => { saveProgress(progress); if (cloud) pushProgress(progress); }, [progress, cloud]);
  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark);
    try { localStorage.setItem(THEME_KEY, dark ? 'dark' : 'light'); } catch { /* ignore */ }
  }, [dark]);
  useEffect(() => { window.scrollTo({ top: 0 }); }, [mode]);

  const onResult = useCallback((id: string, q: 0 | 1 | 2 | 3, tags: string[]) => setProgress((p) => review(p, id, q, tags)), []);
  const onMath = useCallback((score: number) => setProgress((p) => logMath(p, score)), []);

  const queues = useMemo(() => {
    const front = <T extends { id: string }>(q: T[]) => (focus ? [...q.filter((e) => e.id === focus), ...q.filter((e) => e.id !== focus)] : q);
    return {
      syntax: front(buildQueue(filterItems(SYNTAX, pattern, company), progress)),
      bug: front(buildQueue(filterItems(BUGS, pattern, company), progress)),
      pattern: front(buildQueue(filterItems(PATTERN_DRILLS, pattern, company), progress)),
    };
  }, [pattern, company, session, mode, focus]); // eslint-disable-line react-hooks/exhaustive-deps

  const open = (m: Mode, opts: { deck?: string; company?: CompanyId | 'all'; pattern?: PatternId | 'all'; focus?: string } = {}) => {
    setFocus(opts.focus);
    if (opts.focus && opts.company === undefined) setCompany('all');
    if (opts.company !== undefined) setCompany(opts.company);
    if (opts.pattern !== undefined) setPattern(opts.pattern);
    setDeck(opts.deck);
    setMode(m);
    setSession((s) => s + 1);
  };
  const go = (m: Mode, pat: PatternId | 'all' = pattern, comp: CompanyId | 'all' = company) => open(m, { pattern: pat, company: comp });
  const nav = (m: Mode) => { setDeck(undefined); setFocus(undefined); setMode(m); };

  useEffect(() => {
    let g = false;
    const h = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') {
        if (e.key === 'Escape') (e.target as HTMLElement).blur();
        return;
      }
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); setDrawer((d) => !d); return; }
      if (e.key === '?') { setDrawer((d) => !d); return; }
      if (e.key === 'Escape') { setDrawer(false); return; }
      if (g) {
        const item = ALL_NAV.find((n) => n.key === e.key);
        if (item) { setDeck(undefined); setMode(item.id); }
        g = false;
        return;
      }
      if (e.key === 'g') { g = true; setTimeout(() => (g = false), 800); }
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, []);

  const showFilters = mode === 'syntax' || mode === 'bug' || mode === 'pattern' || mode === 'cards' || mode === 'design';
  const showPattern = mode === 'syntax' || mode === 'bug' || mode === 'pattern';
  const filterKey = `${pattern}|${company}|${session}`;
  const days = streak(progress.days);

  const body = () => {
    switch (mode) {
      case 'coach': return <Coach progress={progress} open={open} solved={solved} />;
      case 'path': return <StudyPath progress={progress} solved={solved} syncedAt={ncCloud?.updatedAt ?? null} cloud={cloud && !!ncCloud} pace={pace} setPace={setPace} toggleLocal={toggleLocal} open={open} />;
      case 'dashboard': return <><PageTitle sub="Every attempt and every slip, across all modes.">Stats</PageTitle><Dashboard progress={progress} go={go} reset={() => setProgress(emptyProgress())} /></>;
      case 'companies': return <Companies key={company} progress={progress} solved={solved} initial={company} open={open} />;
      case 'design': return <DesignStudio key={company} progress={progress} company={company} onResult={onResult} />;
      case 'cards': return <Flashcards key={`${company}-${deck}-${session}`} progress={progress} company={company} initialDeck={deck} onResult={onResult} />;
      case 'math': return <MentalMath progress={progress} onFinish={onMath} />;
      case 'reference': return <><PageTitle sub="Exact method names and their costs. Open it from anywhere with ? or Ctrl K.">Python reference</PageTitle><div className="max-w-4xl"><ReferenceContent autoFocus /></div></>;
      default: {
        const intro = DRILL_INTRO[mode]!;
        const q = queues[mode as 'syntax' | 'bug' | 'pattern'];
        return (
          <>
            <PageTitle sub={intro.sub}>{intro.title}</PageTitle>
            {!q.length ? <Empty text="Nothing matches these filters. Try all companies or all patterns." />
              : mode === 'syntax' ? <SyntaxDrill key={filterKey} queue={queues.syntax} onResult={onResult} />
              : mode === 'bug' ? <BugHunter key={filterKey} queue={queues.bug} onResult={onResult} />
              : <PatternDrill key={filterKey} queue={queues.pattern} onResult={onResult} />}
          </>
        );
      }
    }
  };

  const selectCls = 'rounded-md border border-zinc-800 bg-zinc-900 px-2.5 py-1.5 text-[15px] text-zinc-200 outline-none focus:border-violet-500';

  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-[232px] shrink-0 flex-col border-r border-zinc-800 bg-zinc-900/85 px-3 py-5 backdrop-blur md:flex">
        <button onClick={() => nav('coach')} className="mb-7 px-2 text-left">
          <div className="text-[26px] font-extrabold leading-none tracking-[-0.04em] text-zinc-100">py<span className="text-violet-400">forge</span></div>
          <div className="mt-1 text-sm text-zinc-500">new grad interview gym</div>
        </button>
        <nav className="space-y-5">
          {GROUPS.map((g) => (
            <div key={g.name || 'home'}>
              {g.name && <div className="mb-1 px-2 text-[13px] font-medium text-zinc-500">{g.name}</div>}
              {g.items.map((n) => (
                <button key={n.id} onClick={() => nav(n.id)}
                  className={`flex w-full items-center gap-2.5 rounded-md px-2 py-1.5 text-[15px] transition-colors ${mode === n.id ? 'bg-zinc-950 font-semibold text-zinc-100 shadow-[inset_3px_0_0_rgb(var(--hl-500))]' : 'text-zinc-400 hover:text-zinc-100'}`}>
                  <n.icon size={16} strokeWidth={mode === n.id ? 2.3 : 1.8} />
                  <span>{n.label}</span>
                </button>
              ))}
            </div>
          ))}
        </nav>
        <div className="mt-auto space-y-3 px-2">
          {days > 0 && <p className="text-sm text-zinc-400"><span className="hl font-semibold text-zinc-100">{days}-day streak</span></p>}
          <button onClick={() => setDrawer(true)} className="flex w-full items-center justify-between text-sm text-zinc-400 hover:text-zinc-100">Python cheat sheet <Kbd>?</Kbd></button>
          <button onClick={() => setDark((d) => !d)} className="flex w-full items-center gap-2 text-sm text-zinc-400 hover:text-zinc-100">
            {dark ? <Sun size={15} /> : <Moon size={15} />}{dark ? 'Paper mode' : 'Night mode'}
          </button>
        </div>
      </aside>

      <main className="min-w-0 flex-1">
        <header className={`sticky top-0 z-30 bg-zinc-950/90 backdrop-blur ${showFilters ? 'border-b border-zinc-800' : 'md:hidden'}`}>
          <div className="flex items-center gap-1 overflow-x-auto px-3 py-2 md:hidden">
            {ALL_NAV.map((n) => (
              <button key={n.id} onClick={() => nav(n.id)} className={`flex shrink-0 items-center gap-1.5 rounded-md px-2.5 py-1 text-sm ${mode === n.id ? 'bg-zinc-900 font-semibold text-zinc-100' : 'text-zinc-400'}`}>
                <n.icon size={14} />{n.label}
              </button>
            ))}
            <button onClick={() => setDark((d) => !d)} aria-label="Toggle theme" className="ml-1 shrink-0 p-1 text-zinc-400">{dark ? <Sun size={16} /> : <Moon size={16} />}</button>
          </div>
          {showFilters && (
            <div className="flex flex-wrap items-center gap-2 px-6 py-2.5">
              <span className="text-sm text-zinc-500">Focus</span>
              <select value={company} onChange={(e) => go(mode, pattern, e.target.value as CompanyId | 'all')} className={selectCls} aria-label="Company">
                <option value="all">All companies</option>
                <optgroup label="Quant">{COMPANIES.filter((c) => c.tier === 'quant').map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</optgroup>
                <optgroup label="Big tech and AI">{COMPANIES.filter((c) => c.tier === 'bigtech').map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</optgroup>
              </select>
              {showPattern && (
                <select value={pattern} onChange={(e) => go(mode, e.target.value as PatternId | 'all', company)} className={selectCls} aria-label="Pattern">
                  <option value="all">All 18 patterns</option>
                  {PATTERNS.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              )}
            </div>
          )}
        </header>
        <div className="mx-auto max-w-[1180px] px-6 py-8">{body()}</div>
      </main>

      <ReferenceDrawer open={drawer} onClose={() => setDrawer(false)} />
    </div>
  );
}
