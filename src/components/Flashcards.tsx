import { Plus, RotateCw, Trash2 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { COMPANY_NAME } from '../data/meta';
import { DECKS, FLASHCARDS, type DeckId, type Flashcard } from '../data/flashcards';
import { getLocal, mastery, setLocal } from '../lib/storage';
import { shuffle } from '../lib/check';
import type { CompanyId, Progress } from '../types';
import { Bar, Button, Card, Kbd, PageTitle } from './ui';

interface Props {
  progress: Progress;
  company: CompanyId | 'all';
  initialDeck?: string;
  onResult: (id: string, quality: 0 | 1 | 2 | 3, tags: string[]) => void;
}

const GRADES: { q: 0 | 1 | 2 | 3; label: string; hint: string }[] = [
  { q: 0, label: 'Again', hint: 'Blanked' },
  { q: 1, label: 'Hard', hint: 'Got it slowly' },
  { q: 2, label: 'Good', hint: 'Got it' },
  { q: 3, label: 'Easy', hint: 'Instant' },
];

export default function Flashcards({ progress, company, initialDeck, onResult }: Props) {
  const [tab, setTab] = useState<'cards' | 'stories'>('cards');
  const [deck, setDeck] = useState<DeckId | 'due' | 'all' | null>((initialDeck as DeckId) ?? null);

  return (
    <div>
      <PageTitle sub="Flip, answer out loud, then grade yourself honestly. Cards you miss come back sooner.">Flashcards</PageTitle>
      <div className="mb-6 flex gap-1 border-b border-zinc-800">
        {(['cards', 'stories'] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`-mb-px border-b-2 px-3 py-2 font-medium transition-colors ${tab === t ? 'border-violet-500 text-zinc-100' : 'border-transparent text-zinc-500 hover:text-zinc-300'}`}>
            {t === 'cards' ? 'Decks' : 'My story bank'}
          </button>
        ))}
      </div>
      {tab === 'stories' ? <StoryBank /> : deck ? (
        <Session key={`${deck}-${company}`} deck={deck} company={company} progress={progress} onResult={onResult} onExit={() => setDeck(null)} />
      ) : (
        <DeckPicker progress={progress} company={company} onPick={setDeck} />
      )}
    </div>
  );
}

function cardsFor(deck: DeckId | 'due' | 'all', company: CompanyId | 'all', p: Progress): Flashcard[] {
  const now = Date.now();
  let list = FLASHCARDS.filter((c) => company === 'all' || !c.companies || c.companies.includes(company));
  if (deck === 'due') list = list.filter((c) => p.cards[c.id] && p.cards[c.id].due <= now);
  else if (deck !== 'all') list = list.filter((c) => c.deck === deck);
  const due = list.filter((c) => p.cards[c.id] && p.cards[c.id].due <= now);
  const fresh = shuffle(list.filter((c) => !p.cards[c.id]));
  const later = list.filter((c) => p.cards[c.id] && p.cards[c.id].due > now).sort((a, b) => mastery(p.cards[a.id]) - mastery(p.cards[b.id]));
  return [...due, ...fresh, ...later];
}

function DeckPicker({ progress, company, onPick }: { progress: Progress; company: CompanyId | 'all'; onPick: (d: DeckId | 'due' | 'all') => void }) {
  const now = Date.now();
  const due = FLASHCARDS.filter((c) => progress.cards[c.id] && progress.cards[c.id].due <= now).length;
  return (
    <div>
      <div className="mb-6 flex flex-wrap gap-3">
        <Button onClick={() => onPick('due')} disabled={!due}>Review {due} due {due === 1 ? 'card' : 'cards'}</Button>
        <Button variant="subtle" onClick={() => onPick('all')}>Shuffle everything</Button>
        {company !== 'all' && <span className="self-center text-sm text-zinc-500">Showing cards relevant to {COMPANY_NAME[company]}</span>}
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {DECKS.map((d) => {
          const cards = FLASHCARDS.filter((c) => c.deck === d.id && (company === 'all' || !c.companies || c.companies.includes(company)));
          const m = cards.reduce((s, c) => s + mastery(progress.cards[c.id]), 0) / Math.max(1, cards.length);
          const dueHere = cards.filter((c) => progress.cards[c.id] && progress.cards[c.id].due <= now).length;
          return (
            <button key={d.id} onClick={() => onPick(d.id)} disabled={!cards.length}
              className="index-card group relative rounded-sm px-5 pb-4 pl-[68px] pt-4 text-left transition-transform hover:-translate-y-0.5 disabled:opacity-40">
              <div className="text-xl font-semibold text-zinc-100">{d.name}</div>
              <p className="mt-1 min-h-[3em] text-sm leading-[2] text-zinc-400">{d.blurb}</p>
              <div className="mt-3 flex items-center justify-between text-sm text-zinc-500">
                <span className="tnum">{cards.length} cards{dueHere ? `, ${dueHere} due` : ''}</span>
                <span className="tnum">{Math.round(m * 100)}%</span>
              </div>
              <div className="mt-1.5"><Bar value={m} /></div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function Session({ deck, company, progress, onResult, onExit }: { deck: DeckId | 'due' | 'all'; company: CompanyId | 'all'; progress: Progress; onResult: Props['onResult']; onExit: () => void }) {
  const queue = useMemo(() => cardsFor(deck, company, progress), [deck, company]); // eslint-disable-line react-hooks/exhaustive-deps
  const [i, setI] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [graded, setGraded] = useState(0);
  const card = queue[i];

  const grade = (q: 0 | 1 | 2 | 3) => {
    if (!card || !flipped) return;
    onResult(card.id, q, q === 0 ? [`card-miss-${card.deck}`] : []);
    setGraded((g) => g + 1);
    setFlipped(false);
    setI((x) => x + 1);
  };

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement)?.tagName === 'INPUT' || (e.target as HTMLElement)?.tagName === 'TEXTAREA') return;
      if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); setFlipped((f) => !f); }
      const n = Number(e.key);
      if (flipped && n >= 1 && n <= 4) grade((n - 1) as 0 | 1 | 2 | 3);
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  });

  if (!card) {
    return (
      <Card className="mx-auto max-w-lg p-8 text-center">
        <p className="text-xl font-semibold text-zinc-100">{graded ? <span className="hl">Stack finished.</span> : 'Nothing here yet.'}</p>
        <p className="mt-2 text-zinc-400">{graded ? `You graded ${graded} cards. Come back later for the ones that are due again.` : 'No cards are due right now. Pick a deck to learn new ones.'}</p>
        <Button className="mt-5" variant="subtle" onClick={onExit}>Back to decks</Button>
      </Card>
    );
  }

  const deckName = DECKS.find((d) => d.id === card.deck)?.name;
  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-3 flex items-center justify-between text-sm text-zinc-500">
        <button onClick={onExit} className="hover:text-zinc-200">All decks</button>
        <span className="tnum">{i + 1} of {queue.length}</span>
      </div>
      <div className="[perspective:1600px]">
        <div className={`flip relative h-[330px] cursor-pointer ${flipped ? 'on' : ''}`} onClick={() => setFlipped((f) => !f)}>
          <div className="face index-card absolute inset-0 flex flex-col rounded-sm px-8 py-6 pl-[76px]">
            <div className="text-sm text-violet-300">{deckName}</div>
            <div className="flex flex-1 items-center">
              <p className="text-[26px] font-semibold leading-[1.25] text-zinc-100">{card.front}</p>
            </div>
            <div className="text-sm text-zinc-500">Say your answer, then flip <Kbd>Space</Kbd></div>
          </div>
          <div className="face back index-card absolute inset-0 flex flex-col overflow-y-auto rounded-sm px-8 py-6 pl-[76px]">
            <div className="text-sm text-zinc-500">{card.front}</div>
            <p className="mt-2 text-[17px] leading-[32px] text-zinc-100">{card.back}</p>
            {card.companies && <p className="mt-auto pt-3 text-sm text-zinc-500">Comes up at {card.companies.map((c) => COMPANY_NAME[c]).join(', ')}</p>}
          </div>
        </div>
      </div>
      <div className="mt-5 grid grid-cols-4 gap-2">
        {GRADES.map((g, k) => (
          <button key={g.q} disabled={!flipped} onClick={() => grade(g.q)}
            className={`rounded-md border px-2 py-2 text-left transition-colors disabled:opacity-35 ${g.q === 0 ? 'border-rose-500/40 hover:bg-rose-500/10' : g.q === 3 ? 'border-emerald-500/40 hover:bg-emerald-500/10' : 'border-zinc-800 hover:bg-zinc-800/50'} bg-zinc-900`}>
            <div className="flex items-center justify-between font-medium text-zinc-100">{g.label}<Kbd>{k + 1}</Kbd></div>
            <div className="text-xs text-zinc-500">{g.hint}</div>
          </button>
        ))}
      </div>
      {!flipped && <p className="mt-3 text-center text-sm text-zinc-500"><RotateCw size={13} className="mr-1 inline" />Tap the card to flip it</p>}
    </div>
  );
}

// ───────────── Story bank ─────────────

const THEMES = ['Conflict', 'Failure', 'Leadership', 'Ambiguity', 'Tight deadline', 'Customer impact', 'Feedback', 'Proudest project', 'Being wrong', 'Learning fast'] as const;
interface Story { id: string; title: string; situation: string; action: string; result: string; themes: string[] }
const KEY = 'pyforge.stories.v1';

function StoryBank() {
  const [stories, setStories] = useState<Story[]>(() => getLocal<Story[]>(KEY, []));
  const [open, setOpen] = useState<string | null>(null);
  const [armed, setArmed] = useState<string | null>(null);
  useEffect(() => setLocal(KEY, stories), [stories]);

  const add = () => {
    const s: Story = { id: crypto.randomUUID?.() ?? String(Date.now()), title: 'New story', situation: '', action: '', result: '', themes: [] };
    setStories((x) => [s, ...x]);
    setOpen(s.id);
  };
  const upd = (id: string, patch: Partial<Story>) => setStories((x) => x.map((s) => (s.id === id ? { ...s, ...patch } : s)));
  const covered = new Set(stories.flatMap((s) => s.themes));

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <p className="max-w-[60ch] text-zinc-400">Write 6–8 real stories once. Tag each with the themes it can answer, and one story covers several questions.</p>
          <Button onClick={add}><Plus size={16} />Add story</Button>
        </div>
        {stories.length === 0 && (
          <Card className="p-6 text-zinc-400">Start with your proudest project, a disagreement you resolved, and a time something failed. Situation in two sentences, what you did, and a result with a number.</Card>
        )}
        {stories.map((s) => (
          <Card key={s.id} className="overflow-hidden">
            <button onClick={() => setOpen(open === s.id ? null : s.id)} className="flex w-full items-center justify-between px-4 py-3 text-left">
              <span className="font-semibold text-zinc-100">{s.title || 'Untitled story'}</span>
              <span className="text-sm text-zinc-500">{s.themes.join(', ') || 'No themes yet'}</span>
            </button>
            {open === s.id && (
              <div className="space-y-3 border-t border-zinc-800 px-4 py-4">
                <input value={s.title} onChange={(e) => upd(s.id, { title: e.target.value })} placeholder="Short title"
                  className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 font-semibold text-zinc-100 outline-none focus:border-violet-500" />
                {(['situation', 'action', 'result'] as const).map((f) => (
                  <label key={f} className="block">
                    <span className="mb-1 block text-sm font-medium text-zinc-300">{f === 'situation' ? 'Situation and task' : f === 'action' ? 'What I did (use "I")' : 'Result, with a number, and what I learned'}</span>
                    <textarea value={s[f]} onChange={(e) => upd(s.id, { [f]: e.target.value })} rows={3}
                      className="w-full resize-y rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 text-zinc-100 outline-none focus:border-violet-500" />
                  </label>
                ))}
                <div className="flex flex-wrap gap-1.5">
                  {THEMES.map((t) => {
                    const on = s.themes.includes(t);
                    return (
                      <button key={t} onClick={() => upd(s.id, { themes: on ? s.themes.filter((x) => x !== t) : [...s.themes, t] })}
                        className={`rounded-full border px-2.5 py-0.5 text-sm transition-colors ${on ? 'border-amber-600 bg-amber-500/40 text-zinc-100' : 'border-zinc-800 text-zinc-400 hover:border-zinc-600'}`}>{t}</button>
                    );
                  })}
                </div>
                <div className="flex justify-end">
                  <Button variant="ghost" onClick={() => { if (armed === s.id) setStories((x) => x.filter((y) => y.id !== s.id)); else { setArmed(s.id); setTimeout(() => setArmed(null), 3000); } }}><Trash2 size={15} />{armed === s.id ? 'Click again to delete' : 'Delete'}</Button>
                </div>
              </div>
            )}
          </Card>
        ))}
      </div>
      <Card className="h-fit p-4">
        <h3 className="mb-1 font-semibold text-zinc-100">Theme coverage</h3>
        <p className="mb-3 text-sm text-zinc-500">{covered.size} of {THEMES.length} covered</p>
        <ul className="space-y-1.5">
          {THEMES.map((t) => (
            <li key={t} className={`text-sm ${covered.has(t) ? 'text-zinc-100' : 'text-zinc-500'}`}>
              {covered.has(t) ? <span className="hl">{t}</span> : t}
            </li>
          ))}
        </ul>
        <p className="mt-4 text-xs leading-relaxed text-zinc-500">Stories stay in this browser only.</p>
      </Card>
    </div>
  );
}
