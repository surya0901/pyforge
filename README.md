# pyforge: a new grad interview gym

A static, zero-backend trainer for the part of coding interviews that breaks under pressure: **exact Python syntax**, **pattern recognition speed**, and **reading code for subtle bugs**. Built for Citadel, HRT, Jane Street, Meta, Google, OpenAI, Nvidia, Amazon, Microsoft, Apple and Netflix prep.

React + Vite + TypeScript + Tailwind + Lucide. No API keys, no server. Progress, streaks, spaced-repetition schedules and mistake analytics live in `localStorage`.

## What's inside

A study app built for short sessions: open it on a break, do what the **Today** page suggests, close it.

**Today (the coach).** Pick your target companies. The coach looks at how much each company weighs each skill and how accurate you are in each area. From that it builds a 15–25 minute plan, highlights your strengths, marks real gaps (under 60% accuracy) and shows a readiness score per company. One click sends your stats to Claude for a written review, a two-week plan and live quizzing.

| Area | What's there |
|---|---|
| Syntax recall | 55 fill-in-the-blank solutions across all 18 patterns, with diagnostic feedback on classic slips (`.append` on a set, `true`, `heapq.push`, `{}` as a set, `/` vs `//`, `pop()` vs `popleft()`, `[[0]*n]*m`, ±1) |
| Bug hunter | 23 realistic buggy solutions. Flag the lines, pick or type the fix, and read why each bug breaks |
| Pattern speed | 32 timed drills: name the pattern and data structure in 15 seconds |
| Mental math | 2-minute arithmetic sprints with a score history (quant first rounds) |
| System design | 11 problems (URL shortener, rate limiter, news feed, chat, video streaming, KV store, **order matching engine**, **market data feed handler**, **LLM inference service**, crawler, autocomplete). Write each step yourself, then compare with a reference answer |
| Flashcards | 112 cards in 6 decks: behavioral, CS fundamentals, Python internals, system design, probability and markets, GPUs and AI systems. SM-2 spaced repetition with Again/Hard/Good/Easy grading |
| Story bank | Write your STAR stories once, tag them with themes, and see which themes you still need |
| Companies | Playbooks for all 11 companies: the usual loop, what they test, what they value, tips, official links, and your weighted readiness |
| Python reference | A searchable cheat sheet of method names with Big-O. Open it anywhere with `?` |

Paper and night themes. Everything is saved in your browser (`localStorage`). No accounts, no backend, no API keys.

### Keyboard

| Key | Action |
|---|---|
| `Tab` / `Enter` | next blank / check, then next |
| `1`–`4` | answer options; flashcard grades |
| `Space` | flip a flashcard |
| `?` or `Ctrl K` | Python reference drawer |
| `g` then `t s b p m d f c g r` | jump to Today, Syntax, Bugs, Patterns, Math, Design, Flashcards, Companies, Stats, Reference |

## Run locally

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # outputs dist/
npx vite build -c vite.single.config.ts   # optional: one self-contained HTML file in dist-single/
```

## Deploy to GitHub Pages (3 steps)

> This repo is private. On a free GitHub plan, Pages only works for public repos, so the workflow is manual for now. Make the repo public or upgrade, then follow the steps below and restore the `push` trigger in `deploy.yml`.

1. **Create a repo and push** this folder to the `main` branch:
   ```bash
   git init && git add . && git commit -m "PyForge"
   git branch -M main
   git remote add origin https://github.com/<you>/<repo>.git
   git push -u origin main
   ```
2. **Enable Pages:** repo → **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. **Done.** `.github/workflows/deploy.yml` builds and publishes on every push to `main` (re-run it from the Actions tab once if the first run happened before step 2). Your site is at `https://<you>.github.io/<repo>/`.

`vite.config.ts` uses `base: './'`, so assets resolve correctly under any repo name with no config changes.

## Adding exercises

Everything is plain typed data in `src/data/`. Add an object and it shows up in filters, queues and analytics automatically.

**Syntax drill** (`src/data/syntax.ts`). Mark blanks `__0__`, `__1__` … in `code`:

```ts
s({
  id: 'syn-my-problem', title: 'My Problem', pattern: 'heaps', difficulty: 'medium',
  companies: ['google', 'citadel'],
  prompt: 'One-line description.',
  code: `import heapq
heap = []
__0__`,
  blanks: [
    { answers: ['heapq.heappush(heap, x)'], intent: 'push x onto the min-heap' },
  ],
}),
```

Answers are compared with whitespace removed and `"`/`'` unified. List every acceptable form, or use a regex with the `re:` prefix (tested against the whitespace-stripped input), e.g. `'re:^lambda(\\w+):\\1\\[1\\]$'`.

**Bug hunt** (`src/data/bugs.ts`). `line` is 1-indexed, `options[0]` is the correct full replacement line (keep indentation), the rest are decoys.

**Pattern drill** (`src/data/patterns.ts`). `answerDS` must be one of `DS_CHOICES` in `src/data/meta.ts`.

**Flashcard** (`src/data/flashcards.ts`): `c('behavioral', 'my-id', 'Front', 'Back', ['amazon'])`.

**System design problem** (`src/data/design.ts`): a list of steps, each with a prompt and reference bullets.

**Company playbook** (`src/data/companies.ts`): loop, focus, values, tips, links and `weights`, which drive the coach and readiness scores.

Pattern IDs: `arrays, two-pointers, sliding-window, stack, binary-search, linked-list, trees, tries, heaps, backtracking, graphs, adv-graphs, dp-1d, dp-2d, greedy, bits, math, ds-scratch`.
Company IDs: `citadel, hrt, janestreet, meta, google, openai, nvidia, amazon, microsoft, apple, netflix`.

## Project layout

```
src/
  App.tsx                 shell, nav, filters, hotkeys
  components/
    Coach.tsx             today plan, skill map, company readiness, Claude export
    Companies.tsx         11 company playbooks
    DesignStudio.tsx      step-by-step system design practice
    Flashcards.tsx        decks, spaced repetition, story bank
    MentalMath.tsx        2-minute arithmetic sprints
    Dashboard.tsx         stats, weakest patterns, slips
    SyntaxDrill.tsx       active-recall blanks + diagnostics
    BugHunter.tsx         line flagging + fix selection
    PatternDrill.tsx      15s timed recognizer
    Reference.tsx         searchable cheat sheet + drawer
    ui.tsx                shared primitives
  data/                   syntax.ts, bugs.ts, patterns.ts, reference.ts, meta.ts
  lib/
    check.ts              answer matching + mistake diagnostics
    storage.ts            localStorage, SM-2 scheduling, mastery, streaks
    highlight.tsx         tiny Python syntax highlighter
.github/workflows/deploy.yml
```

Every filled-in syntax solution and every fixed bug hunt was executed against test cases before release.

Progress lives in your browser. Use **Export** on the dashboard to back it up.
