import type { CompanyId } from '../types';

/** Skill areas the coach tracks. Each exercise or card maps to one. */
export type Area = 'syntax' | 'bugs' | 'patterns' | 'math' | 'design' | 'behavioral' | 'fundamentals' | 'python' | 'quant' | 'gpu-ai';

export const AREA_NAME: Record<Area, string> = {
  syntax: 'Python syntax recall',
  bugs: 'Reading and debugging code',
  patterns: 'Pattern recognition',
  math: 'Mental math speed',
  design: 'System design',
  behavioral: 'Behavioral stories',
  fundamentals: 'CS fundamentals',
  python: 'Python internals',
  quant: 'Probability and markets',
  'gpu-ai': 'GPUs and AI systems',
};

export interface Playbook {
  id: CompanyId;
  tagline: string;
  loop: string[];
  focus: string[];
  values: string;
  tips: string[];
  weights: Partial<Record<Area, number>>;
  links: { label: string; url: string }[];
}

export const PLAYBOOKS: Playbook[] = [
  {
    id: 'citadel', tagline: 'Fast, correct algorithms and clean code, often in C++ or Python depending on the team.',
    loop: ['Online assessment (timed algorithm problems)', 'One or two technical phone screens', 'Final round: several back-to-back coding interviews, sometimes design or a resume deep dive'],
    focus: ['Medium to hard LeetCode-style problems, done quickly and bug-free', 'Hash maps, heaps, graphs, DP', 'Language depth for the team\'s stack', 'Some teams ask probability or systems questions'],
    values: 'Speed with precision. Edge cases are part of correctness.',
    tips: ['Practice finishing a medium in 20 minutes with tests walked through.', 'Know whether you are interviewing for Citadel (the fund) or Citadel Securities (market making); teams differ.'],
    weights: { syntax: 0.2, bugs: 0.15, patterns: 0.25, math: 0.1, fundamentals: 0.1, quant: 0.1, behavioral: 0.05, python: 0.05 },
    links: [{ label: 'Citadel Securities: new grad engineering interview process', url: 'https://www.citadelsecurities.com/?p=44130' }],
  },
  {
    id: 'hrt', tagline: 'Engineering-led trading. Expect algorithms plus real systems depth.',
    loop: ['Online assessment', 'Technical phone interviews (algorithms, sometimes systems)', 'Onsite with several technical rounds, often including OS, networking or C++ for core developer roles'],
    focus: ['Algorithms and data structures', 'Operating systems, memory, caches, networking', 'Low-latency thinking: allocation, locality, lock-free queues', 'Some probability'],
    values: 'Technical depth and curiosity about how things really work.',
    tips: ['Be able to explain what your code does to the hardware.', 'Build a ring buffer and an LRU cache from scratch until it is automatic.'],
    weights: { syntax: 0.15, bugs: 0.1, patterns: 0.2, fundamentals: 0.25, math: 0.05, quant: 0.1, python: 0.05, behavioral: 0.05, design: 0.05 },
    links: [{ label: 'HRT blog: how to prepare for the SWE interview', url: 'https://www.hudsonrivertrading.com/?p=10041' }],
  },
  {
    id: 'janestreet', tagline: 'Collaborative problem solving. How you think matters more than speed.',
    loop: ['Technical interview over video, coding together with an engineer', 'In-person final round, often one problem extended with new requirements across rounds'],
    focus: ['Clear reasoning out loud', 'Clean, correct, well-structured code', 'Graphs and algorithmic thinking', 'Handling changing requirements gracefully'],
    values: 'Intellectual honesty, collaboration, and taking feedback well. Jane Street states its SWE interviews do not test math or probability.',
    tips: ['Ask clarifying questions before coding.', 'Narrate trade-offs; welcome hints.', 'Write code that is easy to extend, since the next round may build on it.'],
    weights: { patterns: 0.2, syntax: 0.15, bugs: 0.2, design: 0.05, behavioral: 0.15, python: 0.1, fundamentals: 0.05, quant: 0.1 },
    links: [{ label: 'Jane Street: preparing for a SWE interview', url: 'https://www.janestreet.com/preparing-for-a-software-engineering-interview/' }],
  },
  {
    id: 'meta', tagline: 'High-signal coding speed, plus a newer AI-enabled coding round.',
    loop: ['Recruiter call and technical screen (coding)', 'Onsite: a standard coding round (often two problems in 45 minutes), an AI-enabled coding round in many loops, and a behavioral round. Design rounds are more common above new grad.'],
    focus: ['Arrays, strings, trees, graphs, intervals, heaps', 'Finishing two problems with clean code', 'Working with AI tools on a production-like task', 'Behavioral signals: conflict, ambiguity, impact'],
    values: 'Move fast, focus on impact, be direct.',
    tips: ['Drill speed: 15–20 minutes per medium.', 'For the AI round, practice reading and verifying generated code (the Bug Hunter mode trains this).', 'Ask your recruiter which loop you have.'],
    weights: { patterns: 0.25, syntax: 0.2, bugs: 0.2, behavioral: 0.15, design: 0.1, python: 0.05, 'gpu-ai': 0.05 },
    links: [{ label: 'interviewing.io: Meta process and AI-assisted round', url: 'https://interviewing.io/meta-interview-questions' }],
  },
  {
    id: 'google', tagline: 'Algorithm depth, clear communication, and newer code-comprehension and AI-assisted formats.',
    loop: ['Online assessment or phone screen', 'Several onsite coding rounds plus a Googleyness and leadership round', 'Google has been introducing code comprehension and AI-assisted rounds, so confirm your format'],
    focus: ['Graphs, trees, DP, binary search on answers', 'Explaining complexity and trade-offs', 'Reading unfamiliar code', 'Open-ended problems'],
    values: 'Googleyness: humility, collaboration, user focus, comfort with ambiguity.',
    tips: ['Talk while you think and state complexity unprompted.', 'Practice reading code you did not write.'],
    weights: { patterns: 0.25, syntax: 0.15, bugs: 0.2, behavioral: 0.1, design: 0.1, fundamentals: 0.1, python: 0.05, 'gpu-ai': 0.05 },
    links: [{ label: 'Google: how we hire', url: 'https://www.google.com/about/careers/applications/how-we-hire/' }, { label: 'Exponent: Google AI-assisted coding interview', url: 'https://www.tryexponent.com/blog/google-ai-coding-interview' }],
  },
  {
    id: 'openai', tagline: 'Practical coding: build working, extensible code under follow-ups.',
    loop: ['Recruiter screen', 'Online assessment (timed coding)', 'Live coding rounds with practical, object-oriented problems', 'Behavioral round about the mission; team matching often after the offer'],
    focus: ['Writing real, runnable code with classes and state', 'Extending a solution as requirements change', 'Concurrency and API design basics', 'Genuine interest in AI and safety'],
    values: 'Mission alignment, ownership, and shipping correct code fast.',
    tips: ['Practice "build an in-memory X" problems (key-value store with TTL, rate limiter, LRU).', 'Have a real opinion on AI safety and a project that uses models.'],
    weights: { syntax: 0.2, bugs: 0.15, patterns: 0.15, design: 0.15, behavioral: 0.15, python: 0.1, 'gpu-ai': 0.1 },
    links: [{ label: 'Exponent: OpenAI new grad SWE guide', url: 'https://www.tryexponent.com/guides/openai-software-engineer-new-grad-interview' }, { label: 'OpenAI Charter', url: 'https://openai.com/charter/' }],
  },
  {
    id: 'nvidia', tagline: 'Team-driven loops. Strong fundamentals, often C/C++, plus your team\'s domain.',
    loop: ['Recruiter screen', 'Technical screens with the hiring team', 'Several technical interviews: coding, systems, domain (GPU, CUDA, drivers, ML infra)', 'Optional Insider Chat, which does not affect the decision'],
    focus: ['Arrays, bit manipulation, linked lists, trees', 'C/C++, memory, concurrency', 'Computer architecture and GPU basics', 'Projects that match the team'],
    values: 'Technical excellence and intellectual honesty.',
    tips: ['Read the team\'s job post closely and prep that domain.', 'Know warps, memory coalescing and the CUDA thread hierarchy at a whiteboard level.'],
    weights: { patterns: 0.15, syntax: 0.1, bugs: 0.15, fundamentals: 0.25, 'gpu-ai': 0.2, behavioral: 0.1, design: 0.05 },
    links: [{ label: 'CUDA C++ Programming Guide', url: 'https://docs.nvidia.com/cuda/cuda-c-programming-guide/' }],
  },
  {
    id: 'amazon', tagline: 'Coding plus Leadership Principles in every single round.',
    loop: ['Online assessment (coding plus a work-style survey)', 'Final loop of about three rounds; each mixes coding with Leadership Principle questions'],
    focus: ['Arrays, hash maps, trees, graphs, heaps', 'Object-oriented design for some rounds', 'STAR stories mapped to Leadership Principles'],
    values: 'The 16 Leadership Principles, especially Customer Obsession, Ownership, Dive Deep, Deliver Results.',
    tips: ['Prepare 6–8 stories that each cover several principles.', 'Say "I", give numbers, and include what you learned.'],
    weights: { patterns: 0.2, syntax: 0.15, bugs: 0.1, behavioral: 0.3, design: 0.15, python: 0.05, fundamentals: 0.05 },
    links: [{ label: 'Amazon Leadership Principles', url: 'https://www.amazon.jobs/content/en/our-workplace/leadership-principles' }],
  },
  {
    id: 'microsoft', tagline: 'Approachable coding rounds, design basics, and growth mindset.',
    loop: ['Online assessment or phone screen', 'Final loop of 3–4 interviews mixing coding, light design and behavioral; often an "as appropriate" round with a senior interviewer'],
    focus: ['Trees, linked lists, strings, arrays', 'Clean code and testing', 'Object-oriented design', 'Learning from feedback'],
    values: 'Growth mindset, collaboration, customer focus.',
    tips: ['Test your code out loud with small cases.', 'Have a story about learning something hard quickly.'],
    weights: { patterns: 0.2, syntax: 0.2, bugs: 0.15, behavioral: 0.2, design: 0.15, fundamentals: 0.1 },
    links: [{ label: 'Microsoft careers', url: 'https://careers.microsoft.com/' }],
  },
  {
    id: 'apple', tagline: 'Team-specific loops with depth in that team\'s area.',
    loop: ['Recruiter and hiring manager screens', 'Technical phone interviews', 'Onsite (or virtual) with the team: coding, domain, behavioral'],
    focus: ['Solid algorithms', 'Domain depth (iOS, systems, ML, infrastructure, depending on team)', 'Attention to detail and quality'],
    values: 'Craft, ownership, collaboration with design, discretion.',
    tips: ['Learn the team\'s product deeply and use it.', 'Expect detailed questions about your past projects.'],
    weights: { patterns: 0.2, syntax: 0.15, bugs: 0.15, fundamentals: 0.2, behavioral: 0.15, design: 0.15 },
    links: [{ label: 'Apple careers', url: 'https://www.apple.com/careers/us/' }],
  },
  {
    id: 'netflix', tagline: 'Fewer new grad seats; culture fit and practical engineering weigh heavily.',
    loop: ['Recruiter screen', 'Coding assessment (reports mention a CodeSignal-style test and an AI-assisted follow-up)', 'Team interviews: coding, design discussion, culture'],
    focus: ['Practical coding', 'Distributed systems basics (streaming, caching, CDN)', 'Candid communication'],
    values: 'Freedom and responsibility, candor, high talent density.',
    tips: ['Read the culture memo and have opinions about it.', 'Prepare examples of giving and receiving direct feedback.'],
    weights: { patterns: 0.15, syntax: 0.15, bugs: 0.15, design: 0.2, behavioral: 0.25, fundamentals: 0.1 },
    links: [{ label: 'Netflix culture memo', url: 'https://jobs.netflix.com/culture' }],
  },
];

export const RESOURCES: { label: string; url: string; note: string }[] = [
  { label: 'NeetCode 150', url: 'https://neetcode.io/practice', note: 'The best ordered problem list for these 18 patterns.' },
  { label: 'Tech Interview Handbook', url: 'https://www.techinterviewhandbook.org/', note: 'Free study plans, behavioral prep, resume tips.' },
  { label: 'System Design Primer', url: 'https://github.com/donnemartin/system-design-primer', note: 'Free, thorough, and enough for new grad design rounds.' },
  { label: 'Zetamac arithmetic game', url: 'https://arithmetic.zetamac.com/', note: 'The classic quant mental math drill.' },
  { label: 'Jane Street puzzles', url: 'https://www.janestreet.com/puzzles/', note: 'Monthly puzzles for thinking practice.' },
];
