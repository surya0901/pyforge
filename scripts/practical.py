"""
Generates src/data/practical.ts: multi-part "practical" interview problems.

Each problem's reference solution lives here. Every expected value is produced by running
the reference, so the tests can never disagree with a correct answer. Tests of earlier parts
are re-run on later parts (the Jane Street rule: extending your code must not break part one).

Run: python3 scripts/practical.py
"""
import json, copy, textwrap, random, time

def norm(x):
    return json.loads(json.dumps(x, default=lambda o: list(o) if isinstance(o, (set, tuple)) else repr(o)))

def run_build(ns, cls, ops):
    obj, out = None, []
    for m, a in ops:
        if m == '__init__':
            obj = ns[cls](*copy.deepcopy(a)); out.append(None)
        else:
            out.append(getattr(obj, m)(*copy.deepcopy(a)))
    return norm(out)

def load(src):
    ns = {'__name__': 'ref'}
    exec(textwrap.dedent(src), ns)
    return ns

PROBLEMS = []

def problem(**kw):
    ns = load(kw['reference'])
    for part in kw['parts']:
        tests = []
        for t in part['tests']:
            if part['kind'] == 'build':
                exp = run_build(ns, part['func'], t['args'])
            else:
                exp = norm(ns[part['func']](*copy.deepcopy(t['args'])))
            if 'want' in t:
                assert exp == norm(t['want']), (kw['id'], t.get('label'), exp, t['want'])
            tests.append({'args': t['args'], 'expected': exp, 'label': t.get('label', ''), 'hidden': t.get('hidden', False)})
        part['tests'] = tests
    kw['reference'] = textwrap.dedent(kw['reference']).strip('\n')
    kw['starter'] = textwrap.dedent(kw['starter']).strip('\n')
    PROBLEMS.append(kw)

def ops(*xs):
    return [list(x) for x in xs]

# ---------------------------------------------------------------- order book
problem(
    id='order-book', title='Limit order book', minutes=45,
    companies=['citadel', 'hrt', 'janestreet'],
    source='Citadel and Citadel Securities candidates in 2026 report an order book coding round: store orders, answer best price queries, cancel without disturbing other orders.',
    starter='''
    class OrderBook:
        def __init__(self):
            pass

        def add(self, order_id, side, price, qty):
            pass

        def best_bid(self):
            pass

        def best_ask(self):
            pass
    ''',
    reference='''
    import heapq
    from collections import deque

    class OrderBook:
        def __init__(self):
            self.levels = {'buy': {}, 'sell': {}}   # side -> price -> deque of [id, qty]
            self.heaps = {'buy': [], 'sell': []}    # buy stores -price so both are min heaps
            self.where = {}                          # id -> (side, price)

        def _key(self, side, price):
            return -price if side == 'buy' else price

        def add(self, order_id, side, price, qty):
            lvl = self.levels[side]
            if price not in lvl:
                lvl[price] = deque()
                heapq.heappush(self.heaps[side], self._key(side, price))
            lvl[price].append([order_id, qty])
            self.where[order_id] = (side, price)

        def _best(self, side):
            h, lvl = self.heaps[side], self.levels[side]
            while h:
                price = -h[0] if side == 'buy' else h[0]
                if price in lvl and lvl[price]:
                    return price
                heapq.heappop(h)                      # lazy delete of an empty level
                lvl.pop(price, None)
            return None

        def _level(self, side):
            p = self._best(side)
            return None if p is None else [p, sum(q for _, q in self.levels[side][p])]

        def best_bid(self):
            return self._level('buy')

        def best_ask(self):
            return self._level('sell')

        def cancel(self, order_id):
            if order_id not in self.where:
                return False
            side, price = self.where.pop(order_id)
            q = self.levels[side][price]
            for i, (oid, _) in enumerate(q):
                if oid == order_id:
                    del q[i]
                    break
            return True

        def volume_at(self, side, price):
            return sum(q for _, q in self.levels[side].get(price, ()))

        def submit(self, order_id, side, price, qty):
            other = 'sell' if side == 'buy' else 'buy'
            fills = []
            while qty > 0:
                best = self._best(other)
                if best is None or (side == 'buy' and best > price) or (side == 'sell' and best < price):
                    break
                q = self.levels[other][best]
                maker = q[0]
                take = min(qty, maker[1])
                fills.append([maker[0], best, take])
                maker[1] -= take
                qty -= take
                if maker[1] == 0:
                    q.popleft()
                    self.where.pop(maker[0], None)
            if qty > 0:
                self.add(order_id, side, price, qty)
            return fills
    ''',
    parts=[
        dict(title='Store orders and answer best prices', func='OrderBook', kind='build',
             prompt='Build OrderBook with add(order_id, side, price, qty) where side is "buy" or "sell". best_bid() returns [price, total quantity resting at that price] for the highest buy price, best_ask() the same for the lowest sell price. Return None when that side is empty. Both queries should be fast even with many price levels.',
             tests=[
                 dict(label='basic bids and asks', args=ops(('__init__', []), ('add', [1, 'buy', 100, 5]), ('add', [2, 'buy', 101, 3]), ('add', [3, 'sell', 103, 4]), ('best_bid', []), ('best_ask', [])), want=[None, None, None, None, [101, 3], [103, 4]]),
                 dict(label='same price adds up', args=ops(('__init__', []), ('add', [1, 'sell', 50, 2]), ('add', [2, 'sell', 50, 7]), ('best_ask', []))),
                 dict(label='hidden: empty book', hidden=True, args=ops(('__init__', []), ('best_bid', []), ('best_ask', []))),
                 dict(label='hidden: one side only', hidden=True, args=ops(('__init__', []), ('add', [9, 'buy', 10, 1]), ('best_ask', []), ('best_bid', []))),
             ],
             edges=['empty book returns None', 'one side empty', 'several orders at the same price add up', 'many price levels (use a heap or sorted structure)']),
        dict(title='Cancel orders', func='OrderBook', kind='build',
             prompt='Add cancel(order_id) which removes that order and returns True, or returns False if the id is unknown or already cancelled. Other orders at the same price keep their place in line. Add volume_at(side, price) returning the total quantity resting there (0 if none). After cancels, best_bid and best_ask must skip emptied price levels.',
             tests=[
                 dict(label='cancel the only order at the best price', args=ops(('__init__', []), ('add', [1, 'buy', 100, 5]), ('add', [2, 'buy', 99, 1]), ('cancel', [1]), ('best_bid', []), ('volume_at', ['buy', 100]))),
                 dict(label='cancel one of several at a price', args=ops(('__init__', []), ('add', [1, 'sell', 20, 5]), ('add', [2, 'sell', 20, 6]), ('cancel', [1]), ('best_ask', []))),
                 dict(label='hidden: cancel twice', hidden=True, args=ops(('__init__', []), ('add', [1, 'buy', 5, 5]), ('cancel', [1]), ('cancel', [1]), ('cancel', [42]), ('best_bid', []))),
                 dict(label='hidden: book empties then refills', hidden=True, args=ops(('__init__', []), ('add', [1, 'sell', 7, 1]), ('cancel', [1]), ('best_ask', []), ('add', [2, 'sell', 8, 2]), ('best_ask', []))),
             ],
             edges=['cancel an unknown id', 'cancel the same id twice', 'cancel empties the best level so the next level becomes best', 'cancel keeps the time order of the others']),
        dict(title='Match incoming orders', func='OrderBook', kind='build',
             prompt='Add submit(order_id, side, price, qty). A buy matches resting sells priced at or below its price, best price first, and oldest first within a price (price-time priority). Sells match the mirror way. Return the fills as [maker_id, price, qty] in the order they happen, trading at the resting order\'s price. Any unfilled quantity rests on the book like add().',
             tests=[
                 dict(label='buy sweeps two levels', args=ops(('__init__', []), ('add', [1, 'sell', 101, 2]), ('add', [2, 'sell', 102, 5]), ('submit', [3, 'buy', 102, 4]), ('best_ask', []), ('best_bid', [])), want=[None, None, None, [[1, 101, 2], [2, 102, 2]], [102, 3], None]),
                 dict(label='time priority inside a price', args=ops(('__init__', []), ('add', [1, 'buy', 50, 1]), ('add', [2, 'buy', 50, 1]), ('submit', [3, 'sell', 50, 1]), ('volume_at', ['buy', 50]), ('cancel', [2]))),
                 dict(label='hidden: no cross rests the order', hidden=True, args=ops(('__init__', []), ('add', [1, 'sell', 10, 1]), ('submit', [2, 'buy', 9, 3]), ('best_bid', []), ('best_ask', []))),
                 dict(label='hidden: leftover rests at its own price', hidden=True, args=ops(('__init__', []), ('add', [1, 'buy', 30, 2]), ('submit', [2, 'sell', 29, 5]), ('best_ask', []), ('best_bid', []))),
                 dict(label='hidden: filled order can no longer be cancelled', hidden=True, args=ops(('__init__', []), ('add', [1, 'sell', 5, 1]), ('submit', [2, 'buy', 5, 1]), ('cancel', [1]))),
             ],
             edges=['no crossing price: the order just rests', 'partial fill leaves a remainder that rests', 'a fully filled maker disappears (cancel returns False)', 'fills trade at the maker\'s price, not the taker\'s']),
    ],
    followups=['How would you make cancel O(1) instead of scanning the queue at a price?', 'What changes if two threads submit orders at once? Where do you lock?', 'Prices as floats: what can go wrong, and what do real exchanges do instead?', 'Which operation is your bottleneck at a million orders a second?'],
)

# ---------------------------------------------------------------- LRU then LFU
problem(
    id='lru-lfu', title='LRU cache, then LFU with custom eviction', minutes=40,
    companies=['citadel', 'meta', 'google', 'hrt', 'amazon'],
    source='"Implement LRU/LFU cache with custom eviction" appears in Citadel interview reports, and LRU cache shows up in 2026 Meta reports.',
    starter='''
    class LRUCache:
        def __init__(self, capacity):
            pass

        def get(self, key):
            pass

        def put(self, key, value):
            pass
    ''',
    reference='''
    from collections import OrderedDict, defaultdict

    class LRUCache:
        def __init__(self, capacity):
            self.cap = capacity
            self.d = OrderedDict()

        def get(self, key):
            if key not in self.d:
                return -1
            self.d.move_to_end(key)
            return self.d[key]

        def put(self, key, value):
            if self.cap <= 0:
                return
            if key in self.d:
                self.d.move_to_end(key)
            self.d[key] = value
            if len(self.d) > self.cap:
                self.d.popitem(last=False)

    class LFUCache:
        def __init__(self, capacity):
            self.cap = capacity
            self.val = {}
            self.freq = {}
            self.buckets = defaultdict(OrderedDict)   # freq -> keys in LRU order
            self.minf = 0

        def _touch(self, key):
            f = self.freq[key]
            del self.buckets[f][key]
            if not self.buckets[f]:
                del self.buckets[f]
                if self.minf == f:
                    self.minf = f + 1
            self.freq[key] = f + 1
            self.buckets[f + 1][key] = None

        def get(self, key):
            if key not in self.val:
                return -1
            self._touch(key)
            return self.val[key]

        def put(self, key, value):
            if self.cap <= 0:
                return
            if key in self.val:
                self.val[key] = value
                self._touch(key)
                return
            if len(self.val) >= self.cap:
                old, _ = self.buckets[self.minf].popitem(last=False)
                if not self.buckets[self.minf]:
                    del self.buckets[self.minf]
                del self.val[old], self.freq[old]
            self.val[key] = value
            self.freq[key] = 1
            self.buckets[1][key] = None
            self.minf = 1
    ''',
    parts=[
        dict(title='LRU cache', func='LRUCache', kind='build',
             prompt='LRUCache(capacity) with get(key) returning the value or -1, and put(key, value). When full, putting a new key evicts the least recently used key. Both get and put count as a use. Both must be O(1).',
             tests=[
                 dict(label='classic sequence', args=ops(('__init__', [2]), ('put', [1, 1]), ('put', [2, 2]), ('get', [1]), ('put', [3, 3]), ('get', [2]), ('get', [3])), want=[None, None, None, 1, None, -1, 3]),
                 dict(label='update refreshes recency', args=ops(('__init__', [2]), ('put', [1, 1]), ('put', [2, 2]), ('put', [1, 10]), ('put', [3, 3]), ('get', [1]), ('get', [2]))),
                 dict(label='hidden: capacity 0', hidden=True, args=ops(('__init__', [0]), ('put', [1, 1]), ('get', [1]))),
                 dict(label='hidden: capacity 1', hidden=True, args=ops(('__init__', [1]), ('put', [1, 1]), ('put', [2, 2]), ('get', [1]), ('get', [2]))),
             ],
             edges=['capacity 0', 'capacity 1', 'put on an existing key updates and refreshes it', 'get of a missing key']),
        dict(title='LFU cache', func='LFUCache', kind='build',
             prompt='Now LFUCache(capacity) with the same API. When full, evict the key used the fewest times. If several keys tie on count, evict the least recently used of them. A put on an existing key counts as a use. Aim for O(1) per operation. Keep LRUCache working too.',
             tests=[
                 dict(label='frequency decides', args=ops(('__init__', [2]), ('put', [1, 1]), ('put', [2, 2]), ('get', [1]), ('put', [3, 3]), ('get', [2]), ('get', [3]), ('get', [1])), want=[None, None, None, 1, None, -1, 3, 1]),
                 dict(label='tie broken by recency', args=ops(('__init__', [2]), ('put', [1, 1]), ('put', [2, 2]), ('put', [3, 3]), ('get', [1]), ('get', [2]))),
                 dict(label='hidden: capacity 0', hidden=True, args=ops(('__init__', [0]), ('put', [0, 0]), ('get', [0]))),
                 dict(label='hidden: update counts as a use', hidden=True, args=ops(('__init__', [2]), ('put', [1, 1]), ('put', [2, 2]), ('put', [1, 5]), ('put', [3, 3]), ('get', [1]), ('get', [2]), ('get', [3]))),
                 dict(label='hidden: min frequency resets for a new key', hidden=True, args=ops(('__init__', [2]), ('put', [1, 1]), ('get', [1]), ('get', [1]), ('put', [2, 2]), ('put', [3, 3]), ('get', [2]), ('get', [1]), ('get', [3]))),
             ],
             edges=['ties on frequency go to the least recent key', 'an update counts as a use', 'a brand new key resets the minimum frequency to 1', 'capacity 0']),
    ],
    followups=['Why does a doubly linked list plus a hash map give O(1) LRU? What does OrderedDict do under the hood?', 'How would you make this cache safe to use from several threads?', 'When is LFU a worse policy than LRU in practice?'],
)

# ---------------------------------------------------------------- rate limiter
problem(
    id='rate-limiter', title='Hit counter, rate limiter, token bucket', minutes=40,
    companies=['meta', 'google', 'amazon', 'openai', 'citadel'],
    source='Rate limiters and hit counters are a standard practical prompt for backend teams, and the sliding window idea comes up again in trading risk checks.',
    starter='''
    class HitCounter:
        def __init__(self):
            pass

        def hit(self, timestamp):
            pass

        def get_hits(self, timestamp):
            pass
    ''',
    reference='''
    from collections import deque, defaultdict

    class HitCounter:
        def __init__(self):
            self.q = deque()

        def hit(self, timestamp):
            self.q.append(timestamp)

        def get_hits(self, timestamp):
            while self.q and self.q[0] <= timestamp - 300:
                self.q.popleft()
            return len(self.q)

    class RateLimiter:
        def __init__(self, limit, window):
            self.limit, self.window = limit, window
            self.log = defaultdict(deque)

        def allow(self, user, t):
            q = self.log[user]
            while q and q[0] <= t - self.window:
                q.popleft()
            if len(q) < self.limit:
                q.append(t)
                return True
            return False

    class TokenBucket:
        def __init__(self, capacity, rate):
            self.cap, self.rate = capacity, rate
            self.tokens = float(capacity)
            self.last = None

        def allow(self, t, cost=1):
            if self.last is not None:
                self.tokens = min(self.cap, self.tokens + (t - self.last) * self.rate)
            self.last = t
            if self.tokens >= cost:
                self.tokens -= cost
                return True
            return False
    ''',
    parts=[
        dict(title='Hit counter', func='HitCounter', kind='build',
             prompt='HitCounter with hit(timestamp) and get_hits(timestamp), which returns how many hits happened in the past 300 seconds, meaning timestamps in (timestamp - 300, timestamp]. Timestamps are in seconds and never go backwards. Several hits can share a timestamp.',
             tests=[
                 dict(label='window edge', args=ops(('__init__', []), ('hit', [1]), ('hit', [2]), ('hit', [3]), ('get_hits', [4]), ('hit', [300]), ('get_hits', [300]), ('get_hits', [301])), want=[None, None, None, None, 3, None, 4, 3]),
                 dict(label='hidden: no hits yet', hidden=True, args=ops(('__init__', []), ('get_hits', [100]))),
                 dict(label='hidden: many hits at one second', hidden=True, args=ops(('__init__', []), ('hit', [5]), ('hit', [5]), ('hit', [5]), ('get_hits', [304]), ('get_hits', [305]))),
             ],
             edges=['exactly 300 seconds later the old hit drops out', 'several hits at the same timestamp', 'no hits at all']),
        dict(title='Per user rate limiter', func='RateLimiter', kind='build',
             prompt='RateLimiter(limit, window) with allow(user, t). Return True and record the request if that user has fewer than limit allowed requests in (t - window, t]. Otherwise return False. Rejected requests do not count. Users are independent.',
             tests=[
                 dict(label='limit 2 per 10 seconds', args=ops(('__init__', [2, 10]), ('allow', ['a', 1]), ('allow', ['a', 2]), ('allow', ['a', 3]), ('allow', ['b', 3]), ('allow', ['a', 11]), ('allow', ['a', 12])), want=[None, True, True, False, True, True, True]),
                 dict(label='hidden: rejected requests do not count', hidden=True, args=ops(('__init__', [1, 5]), ('allow', ['u', 0]), ('allow', ['u', 4]), ('allow', ['u', 4]), ('allow', ['u', 5]))),
                 dict(label='hidden: limit 0', hidden=True, args=ops(('__init__', [0, 5]), ('allow', ['u', 1]))),
             ],
             edges=['rejected requests must not be logged', 'separate users do not share a limit', 'limit 0 rejects everything', 'a request exactly window seconds old has expired']),
        dict(title='Token bucket', func='TokenBucket', kind='build',
             prompt='TokenBucket(capacity, rate): starts full with capacity tokens and refills continuously at rate tokens per second, never above capacity. allow(t, cost=1) refills for the time since the last call, then spends cost tokens and returns True if it has enough, else returns False and spends nothing. Times never go backwards.',
             tests=[
                 dict(label='burst then refill', args=ops(('__init__', [2, 1]), ('allow', [0]), ('allow', [0]), ('allow', [0]), ('allow', [1]), ('allow', [1.5])), want=[None, True, True, False, True, False]),
                 dict(label='hidden: never above capacity', hidden=True, args=ops(('__init__', [3, 10]), ('allow', [0, 3]), ('allow', [100, 3]), ('allow', [100, 1]))),
                 dict(label='hidden: a failed big request spends nothing', hidden=True, args=ops(('__init__', [5, 1]), ('allow', [0, 6]), ('allow', [0, 5]))),
             ],
             edges=['refill caps at capacity after a long idle time', 'a failed request spends no tokens', 'fractional time between calls']),
    ],
    followups=['Sliding log uses memory per request. How would a sliding window counter cut that?', 'How do you rate limit across 50 servers? What breaks if each one keeps its own counts?', 'Token bucket vs leaky bucket: what does each allow?'],
)

# ---------------------------------------------------------------- KV store with transactions
problem(
    id='kv-transactions', title='Key-value store with transactions', minutes=40,
    companies=['meta', 'google', 'openai', 'citadel', 'janestreet', 'amazon'],
    source='An in-memory store with nested BEGIN, ROLLBACK and COMMIT is a long running practical round. It tests state design more than tricks.',
    starter='''
    class KVStore:
        def __init__(self):
            pass

        def set(self, key, value):
            pass

        def get(self, key):
            pass

        def delete(self, key):
            pass

        def count(self, value):
            pass
    ''',
    reference='''
    from collections import Counter

    _MISSING = object()

    class KVStore:
        def __init__(self):
            self.data = {}
            self.counts = Counter()
            self.undo = []          # one list of (key, old value) per open transaction

        def _write(self, key, value):
            old = self.data.get(key, _MISSING)
            if self.undo:
                self.undo[-1].append((key, old))
            if old is not _MISSING:
                self.counts[old] -= 1
            if value is _MISSING:
                self.data.pop(key, None)
            else:
                self.data[key] = value
                self.counts[value] += 1

        def set(self, key, value):
            self._write(key, value)

        def get(self, key):
            return self.data.get(key)

        def delete(self, key):
            if key not in self.data:
                return False
            self._write(key, _MISSING)
            return True

        def count(self, value):
            return self.counts[value]

        def begin(self):
            self.undo.append([])

        def rollback(self):
            if not self.undo:
                return False
            log = self.undo.pop()
            for key, old in reversed(log):
                cur = self.data.get(key, _MISSING)
                if cur is not _MISSING:
                    self.counts[cur] -= 1
                if old is _MISSING:
                    self.data.pop(key, None)
                else:
                    self.data[key] = old
                    self.counts[old] += 1
            return True

        def commit(self):
            if not self.undo:
                return False
            self.undo = []
            return True
    ''',
    parts=[
        dict(title='Store with value counts', func='KVStore', kind='build',
             prompt='KVStore with set(key, value), get(key) returning the value or None, delete(key) returning True if the key existed, and count(value) returning how many keys currently hold that value. count must be O(1), not a scan.',
             tests=[
                 dict(label='basic', args=ops(('__init__', []), ('set', ['a', 10]), ('set', ['b', 10]), ('count', [10]), ('set', ['a', 20]), ('count', [10]), ('get', ['a']), ('delete', ['b']), ('count', [10])), want=[None, None, None, 2, None, 1, 20, True, 0]),
                 dict(label='hidden: missing keys', hidden=True, args=ops(('__init__', []), ('get', ['x']), ('delete', ['x']), ('count', [5]))),
                 dict(label='hidden: set the same value twice', hidden=True, args=ops(('__init__', []), ('set', ['k', 1]), ('set', ['k', 1]), ('count', [1]))),
             ],
             edges=['delete a missing key', 'set a key to the value it already has (count must not double)', 'count of a value nobody holds']),
        dict(title='Nested transactions', func='KVStore', kind='build',
             prompt='Add begin(), rollback() and commit(). Transactions nest. rollback() undoes every change since the most recent begin() and returns True, or returns False if no transaction is open. commit() makes every open transaction permanent and returns True, or False if none is open. get and count must reflect the current view at all times.',
             tests=[
                 dict(label='nested rollback', args=ops(('__init__', []), ('set', ['a', 10]), ('begin', []), ('set', ['a', 20]), ('begin', []), ('set', ['a', 30]), ('get', ['a']), ('rollback', []), ('get', ['a']), ('rollback', []), ('get', ['a']), ('rollback', [])), want=[None, None, None, None, None, None, 30, True, 20, True, 10, False]),
                 dict(label='commit closes everything', args=ops(('__init__', []), ('begin', []), ('set', ['a', 1]), ('begin', []), ('set', ['b', 1]), ('commit', []), ('rollback', []), ('count', [1]))),
                 dict(label='hidden: rollback restores a delete and counts', hidden=True, args=ops(('__init__', []), ('set', ['a', 5]), ('begin', []), ('delete', ['a']), ('count', [5]), ('rollback', []), ('get', ['a']), ('count', [5]))),
                 dict(label='hidden: rollback removes a key created inside', hidden=True, args=ops(('__init__', []), ('begin', []), ('set', ['n', 1]), ('set', ['n', 2]), ('rollback', []), ('get', ['n']), ('count', [1]), ('count', [2]))),
                 dict(label='hidden: commit with nothing open', hidden=True, args=ops(('__init__', []), ('commit', []))),
             ],
             edges=['rollback with no transaction', 'commit with no transaction', 'rollback must restore a deleted key', 'rollback must delete a key created inside the transaction', 'the same key changed twice in one transaction', 'counts stay right after rollback']),
    ],
    followups=['Undo log vs copying the whole dict on begin: what are the costs of each?', 'How would you make this durable so a crash does not lose committed data?', 'Two clients use the store at once. What isolation do they get from your design?'],
)

# ---------------------------------------------------------------- brackets
problem(
    id='brackets', title='Bracket checker that grows', minutes=30,
    companies=['janestreet', 'google', 'meta', 'jpmorgan'],
    source='Jane Street reports describe bracket validation that later has to return exact positions. The point is extending part one cleanly.',
    starter='''
    def is_balanced(s):
        pass
    ''',
    reference='''
    PAIRS = {')': '(', ']': '[', '}': '{'}

    def _scan(s):
        stack = []
        for i, ch in enumerate(s):
            if ch in '([{':
                stack.append(i)
            elif ch in PAIRS:
                if not stack or s[stack[-1]] != PAIRS[ch]:
                    return i, stack, []
                stack.pop()
        return -1, stack, None

    def is_balanced(s):
        bad, stack, _ = _scan(s)
        return bad == -1 and not stack

    def first_error(s):
        bad, stack, _ = _scan(s)
        if bad != -1:
            return bad
        return stack[0] if stack else -1

    def match_pairs(s):
        if not is_balanced(s):
            return []
        stack, out = [], []
        for i, ch in enumerate(s):
            if ch in '([{':
                stack.append(i)
            elif ch in PAIRS:
                out.append([stack.pop(), i])
        return sorted(out)
    ''',
    parts=[
        dict(title='Is it balanced?', func='is_balanced', kind='call',
             prompt='is_balanced(s) returns True if every (, [ and { is closed by the matching bracket in the right order. Any other characters are ignored.',
             tests=[
                 dict(label='nested', args=['a(b[c]{d})'], want=True),
                 dict(label='crossed', args=['([)]'], want=False),
                 dict(label='hidden: empty string', hidden=True, args=['']),
                 dict(label='hidden: only a closer', hidden=True, args=[')']),
                 dict(label='hidden: unclosed opener', hidden=True, args=['((']),
             ],
             edges=['empty string', 'a closer with nothing open', 'openers left at the end', 'crossed pairs like ([)]']),
        dict(title='Where is the first error?', func='first_error', kind='call',
             prompt='first_error(s) returns the index of the bracket that makes s invalid, or -1 if it is balanced. If a closer has no matching opener, return the closer\'s index. If the string ends with brackets still open, return the index of the earliest one still open.',
             tests=[
                 dict(label='bad closer', args=['(a]'], want=2),
                 dict(label='unclosed at end', args=['x(y[z]'], want=1),
                 dict(label='hidden: balanced', hidden=True, args=['{}[]()']),
                 dict(label='hidden: closer first', hidden=True, args=['}{']),
                 dict(label='hidden: several unclosed', hidden=True, args=['a(b(c[d]']),
             ],
             edges=['report the closer when it does not match', 'report the earliest unclosed opener at the end', 'balanced returns -1']),
        dict(title='Return the matching pairs', func='match_pairs', kind='call',
             prompt='match_pairs(s) returns every [open_index, close_index] pair, sorted by open index. If s is not balanced, return [].',
             tests=[
                 dict(label='nested pairs', args=['(a[b])'], want=[[0, 5], [2, 4]]),
                 dict(label='hidden: unbalanced', hidden=True, args=['(]']),
                 dict(label='hidden: siblings', hidden=True, args=['()[]{}']),
             ],
             edges=['unbalanced returns an empty list', 'output sorted by opening index, not closing order']),
    ],
    followups=['Your first part probably threw away indices. How did you change it so later parts were cheap?', 'How would you handle a stream too large for memory?', 'What if quotes can contain brackets that should be ignored?'],
)

# ---------------------------------------------------------------- RLE stream
problem(
    id='rle-stream', title='Run-length encoder for a stream', minutes=35,
    companies=['janestreet', 'hrt', 'google'],
    source='Jane Street reports include a run-length encoding utility that later has to handle partial streams, where state must carry across chunks.',
    starter='''
    def encode(s):
        pass
    ''',
    reference='''
    def encode(s):
        out = []
        for ch in s:
            if out and out[-1][0] == ch:
                out[-1][1] += 1
            else:
                out.append([ch, 1])
        return out

    def decode(runs):
        return ''.join(ch * n for ch, n in runs)

    class StreamEncoder:
        def __init__(self):
            self.cur = None     # the run that might still grow

        def feed(self, chunk):
            done = []
            for ch in chunk:
                if self.cur and self.cur[0] == ch:
                    self.cur[1] += 1
                else:
                    if self.cur:
                        done.append(self.cur)
                    self.cur = [ch, 1]
            return done

        def flush(self):
            out = [self.cur] if self.cur else []
            self.cur = None
            return out
    ''',
    parts=[
        dict(title='Encode', func='encode', kind='call',
             prompt='encode(s) returns a list of [character, count] runs. "aaabcc" becomes [["a", 3], ["b", 1], ["c", 2]].',
             tests=[
                 dict(label='example', args=['aaabcc'], want=[['a', 3], ['b', 1], ['c', 2]]),
                 dict(label='hidden: empty', hidden=True, args=['']),
                 dict(label='hidden: same letter later', hidden=True, args=['abba']),
             ],
             edges=['empty string', 'one character', 'the same letter in two separate runs']),
        dict(title='Decode', func='decode', kind='call',
             prompt='decode(runs) turns the list back into the string. decode(encode(s)) must equal s.',
             tests=[
                 dict(label='example', args=[[['x', 2], ['y', 1]]], want='xxy'),
                 dict(label='hidden: empty list', hidden=True, args=[[]]),
             ],
             edges=['empty list']),
        dict(title='Encode a stream in chunks', func='StreamEncoder', kind='build',
             prompt='StreamEncoder receives the text in chunks. feed(chunk) returns the runs that are now finished, meaning a different character has arrived after them. A run can continue into the next chunk, so the last run is held back. flush() returns whatever run is still held and resets. Concatenating every output must equal encode() of the whole text.',
             tests=[
                 dict(label='run crosses a chunk boundary', args=ops(('__init__', []), ('feed', ['aab']), ('feed', ['bbc']), ('flush', [])), want=[None, [['a', 2]], [['b', 3]], [['c', 1]]]),
                 dict(label='hidden: empty chunks', hidden=True, args=ops(('__init__', []), ('feed', ['']), ('feed', ['zz']), ('feed', ['']), ('flush', []), ('flush', []))),
                 dict(label='hidden: flush then keep going', hidden=True, args=ops(('__init__', []), ('feed', ['aa']), ('flush', []), ('feed', ['a']), ('flush', []))),
             ],
             edges=['a run that spans two chunks', 'empty chunks', 'flush twice', 'flush then feed again starts fresh']),
    ],
    followups=['What state does the stream version need, and why is holding back one run enough?', 'How would you encode counts in bytes for a compact binary format?', 'When does run-length encoding make data bigger?'],
)

# ---------------------------------------------------------------- trades
problem(
    id='trade-book', title='Trade aggregation and P&L', minutes=35,
    companies=['janestreet', 'citadel', 'hrt', 'goldman', 'jpmorgan'],
    source='Jane Street reports include trade processing: aggregate volume and top trades, then extend to short sales. Signed quantities from the start make the extension cheap.',
    starter='''
    class TradeBook:
        def __init__(self):
            pass

        def record(self, trader, symbol, qty, price):
            pass

        def position(self, trader, symbol):
            pass

        def top_traders(self, k):
            pass
    ''',
    reference='''
    from collections import defaultdict

    class TradeBook:
        def __init__(self):
            self.pos = defaultdict(int)       # (trader, symbol) -> signed qty
            self.cash = defaultdict(float)    # (trader, symbol) -> cash from trades
            self.notional = defaultdict(float)

        def record(self, trader, symbol, qty, price):
            self.pos[trader, symbol] += qty
            self.cash[trader, symbol] -= qty * price
            self.notional[trader] += abs(qty) * price

        def position(self, trader, symbol):
            return self.pos[trader, symbol]

        def top_traders(self, k):
            return sorted(self.notional, key=lambda t: (-self.notional[t], t))[:k]

        def pnl(self, trader, symbol, mark):
            return round(self.cash[trader, symbol] + self.pos[trader, symbol] * mark, 2)
    ''',
    parts=[
        dict(title='Positions and top traders', func='TradeBook', kind='build',
             prompt='record(trader, symbol, qty, price) logs a trade. qty is positive for a buy and negative for a sell. position(trader, symbol) returns the net quantity (0 if none). top_traders(k) returns up to k trader names with the largest total traded notional, the sum of abs(qty) * price over all their trades, highest first, ties by name A to Z.',
             tests=[
                 dict(label='buys and sells', args=ops(('__init__', []), ('record', ['ann', 'AAPL', 10, 5.0]), ('record', ['bob', 'AAPL', -4, 6.0]), ('record', ['ann', 'AAPL', -3, 5.5]), ('position', ['ann', 'AAPL']), ('top_traders', [2])), want=[None, None, None, None, 7, ['ann', 'bob']]),
                 dict(label='hidden: unknown trader', hidden=True, args=ops(('__init__', []), ('position', ['zed', 'X']), ('top_traders', [3]))),
                 dict(label='hidden: tie broken by name', hidden=True, args=ops(('__init__', []), ('record', ['cy', 'X', 1, 10.0]), ('record', ['al', 'X', -1, 10.0]), ('top_traders', [5]))),
             ],
             edges=['unknown trader has position 0', 'k larger than the number of traders', 'sells add to notional too (absolute value)', 'ties sorted by name']),
        dict(title='Profit and loss, including shorts', func='TradeBook', kind='build',
             prompt='Add pnl(trader, symbol, mark): the cash from all their trades in that symbol (selling brings cash in, buying spends it) plus their current position valued at mark. Round to 2 decimals. Short positions (negative) lose money when the mark goes up.',
             tests=[
                 dict(label='long position', args=ops(('__init__', []), ('record', ['ann', 'X', 10, 5.0]), ('pnl', ['ann', 'X', 6.0])), want=[None, None, 10.0]),
                 dict(label='short then cover', args=ops(('__init__', []), ('record', ['b', 'Y', -5, 20.0]), ('pnl', ['b', 'Y', 22.0]), ('record', ['b', 'Y', 5, 18.0]), ('pnl', ['b', 'Y', 100.0]), ('position', ['b', 'Y']))),
                 dict(label='hidden: no trades', hidden=True, args=ops(('__init__', []), ('pnl', ['q', 'Z', 50.0]))),
             ],
             edges=['short positions', 'a closed position (back to 0) keeps its realized P&L', 'no trades means 0']),
    ],
    followups=['Why do floats make money code risky? What would you store instead?', 'How would you make top_traders cheap if it is called after every trade?', 'Trades arrive out of order with timestamps. What changes?'],
)

# ---------------------------------------------------------------- file system
problem(
    id='file-system', title='In-memory file system', minutes=40,
    companies=['google', 'meta', 'amazon', 'microsoft', 'openai'],
    source='The in-memory file system is a standard stateful design round: a tree of dicts, path parsing and recursive size.',
    starter='''
    class FileSystem:
        def __init__(self):
            pass

        def mkdir(self, path):
            pass

        def add_file(self, path, content):
            pass

        def read(self, path):
            pass

        def ls(self, path):
            pass
    ''',
    reference='''
    class FileSystem:
        def __init__(self):
            self.root = {}          # dir: dict of name -> dict or str

        def _parts(self, path):
            return [p for p in path.split('/') if p]

        def _walk(self, parts, create=False):
            node = self.root
            for p in parts:
                if p not in node:
                    if not create:
                        return None
                    node[p] = {}
                node = node[p]
                if isinstance(node, str):
                    return None
            return node

        def mkdir(self, path):
            self._walk(self._parts(path), create=True)

        def add_file(self, path, content):
            parts = self._parts(path)
            d = self._walk(parts[:-1], create=True)
            d[parts[-1]] = d.get(parts[-1], '') + content

        def read(self, path):
            parts = self._parts(path)
            d = self._walk(parts[:-1])
            return d[parts[-1]] if d is not None and isinstance(d.get(parts[-1]), str) else ''

        def ls(self, path):
            parts = self._parts(path)
            if parts:
                d = self._walk(parts[:-1])
                if d is not None and isinstance(d.get(parts[-1]), str):
                    return [parts[-1]]
            d = self._walk(parts)
            return sorted(d) if isinstance(d, dict) else []

        def size(self, path):
            parts = self._parts(path)
            if parts:
                d = self._walk(parts[:-1])
                if d is None or parts[-1] not in d:
                    return 0
                node = d[parts[-1]]
            else:
                node = self.root
            def total(n):
                return len(n) if isinstance(n, str) else sum(total(c) for c in n.values())
            return total(node)

        def rm(self, path):
            parts = self._parts(path)
            if not parts:
                return False
            d = self._walk(parts[:-1])
            if d is None or parts[-1] not in d:
                return False
            del d[parts[-1]]
            return True
    ''',
    parts=[
        dict(title='Directories and files', func='FileSystem', kind='build',
             prompt='Paths look like "/a/b/c". mkdir(path) creates the directory and any missing parents. add_file(path, content) creates the file (and parent directories) or appends to it. read(path) returns the content ("" if missing). ls(path) returns sorted names inside a directory, or [name] if path is a file, or [] if it does not exist. ls("/") lists the root.',
             tests=[
                 dict(label='basic', args=ops(('__init__', []), ('ls', ['/']), ('mkdir', ['/a/b/c']), ('add_file', ['/a/b/c/d', 'hello']), ('ls', ['/']), ('read', ['/a/b/c/d']), ('ls', ['/a/b/c/d'])), want=[None, [], None, None, ['a'], 'hello', ['d']]),
                 dict(label='append', args=ops(('__init__', []), ('add_file', ['/f', 'ab']), ('add_file', ['/f', 'cd']), ('read', ['/f']))),
                 dict(label='hidden: missing path', hidden=True, args=ops(('__init__', []), ('ls', ['/nope']), ('read', ['/nope/x']))),
                 dict(label='hidden: sorted listing', hidden=True, args=ops(('__init__', []), ('mkdir', ['/z']), ('add_file', ['/b', 'x']), ('mkdir', ['/a']), ('ls', ['/']))),
             ],
             edges=['ls on a file returns just its name', 'ls of the root', 'missing paths', 'add_file creates parent directories']),
        dict(title='Directory size', func='FileSystem', kind='build',
             prompt='Add size(path): total characters in every file under path (or the file itself). 0 if missing. size("/") covers everything.',
             tests=[
                 dict(label='nested', args=ops(('__init__', []), ('add_file', ['/a/x', '123']), ('add_file', ['/a/b/y', '45']), ('size', ['/a']), ('size', ['/']), ('size', ['/a/x']))),
                 dict(label='hidden: missing and empty', hidden=True, args=ops(('__init__', []), ('mkdir', ['/e']), ('size', ['/e']), ('size', ['/missing']))),
             ],
             edges=['empty directory', 'missing path', 'size of a single file']),
        dict(title='Remove', func='FileSystem', kind='build',
             prompt='Add rm(path) which deletes a file or a whole directory tree and returns True, or False if the path does not exist. Removing "/" is not allowed and returns False.',
             tests=[
                 dict(label='remove a tree', args=ops(('__init__', []), ('add_file', ['/a/b/c', 'x']), ('rm', ['/a/b']), ('ls', ['/a']), ('size', ['/']), ('rm', ['/a/b']))),
                 dict(label='hidden: root', hidden=True, args=ops(('__init__', []), ('rm', ['/']))),
             ],
             edges=['removing a missing path', 'removing the root', 'removing a directory removes everything under it']),
    ],
    followups=['Where would you cache directory sizes, and what has to update on every write?', 'How do real file systems store a directory, and why are hard links possible?', 'Two processes append to the same file at once. What can go wrong?'],
)

# ---------------------------------------------------------------- arbitrage
problem(
    id='fx-arbitrage', title='Currency conversion and arbitrage', minutes=35,
    companies=['janestreet', 'citadel', 'hrt', 'goldman'],
    source='Exchange arbitrage shows up in 2026 Citadel Securities and Jane Street reports: a graph problem dressed up as markets.',
    starter='''
    def best_rate(rates, src, dst):
        pass
    ''',
    reference='''
    import math
    from collections import defaultdict

    def best_rate(rates, src, dst):
        g = defaultdict(list)
        for a, b, r in rates:
            g[a].append((b, r))
        if src == dst:
            return 1.0
        best = -1.0
        def dfs(u, prod, seen):
            nonlocal best
            if u == dst:
                best = max(best, prod)
                return
            for v, r in g[u]:
                if v not in seen:
                    seen.add(v)
                    dfs(v, prod * r, seen)
                    seen.remove(v)
        dfs(src, 1.0, {src})
        return round(best, 6)

    def has_arbitrage(rates):
        nodes = {x for a, b, _ in rates for x in (a, b)}
        dist = {n: 0.0 for n in nodes}
        edges = [(a, b, -math.log(r)) for a, b, r in rates]
        for _ in range(len(nodes)):
            changed = False
            for a, b, w in edges:
                if dist[a] + w < dist[b] - 1e-12:
                    dist[b] = dist[a] + w
                    changed = True
            if not changed:
                return False
        return True
    ''',
    parts=[
        dict(title='Best conversion rate', func='best_rate', kind='call',
             prompt='rates is a list of [from, to, rate]: 1 unit of from buys rate units of to (one direction only). best_rate(rates, src, dst) returns the best amount of dst you can get for 1 src by chaining conversions without repeating a currency, rounded to 6 decimals. Return 1.0 if src == dst and -1 if dst cannot be reached.',
             tests=[
                 dict(label='two routes', args=[[['USD', 'EUR', 0.9], ['EUR', 'GBP', 0.9], ['USD', 'GBP', 0.8]], 'USD', 'GBP'], want=0.81),
                 dict(label='hidden: unreachable', hidden=True, args=[[['A', 'B', 2.0]], 'B', 'A']),
                 dict(label='hidden: same currency', hidden=True, args=[[['A', 'B', 2.0]], 'A', 'A']),
                 dict(label='hidden: longer path wins', hidden=True, args=[[['A', 'B', 2.0], ['B', 'C', 2.0], ['A', 'C', 3.0]], 'A', 'C']),
             ],
             edges=['unreachable target', 'source equals target', 'a longer chain can beat a direct rate']),
        dict(title='Is there an arbitrage?', func='has_arbitrage', kind='call',
             prompt='has_arbitrage(rates) returns True if some cycle of conversions turns 1 unit into more than 1 unit. Think about logs: products become sums.',
             tests=[
                 dict(label='profitable cycle', args=[[['A', 'B', 2.0], ['B', 'C', 0.6], ['C', 'A', 0.9]]], want=True),
                 dict(label='no profit', args=[[['A', 'B', 2.0], ['B', 'A', 0.5]]], want=False),
                 dict(label='hidden: no cycles at all', hidden=True, args=[[['A', 'B', 3.0], ['B', 'C', 3.0]]]),
                 dict(label='hidden: empty', hidden=True, args=[[]]),
             ],
             edges=['no cycles', 'empty input', 'a cycle that returns exactly 1 is not arbitrage']),
    ],
    followups=['Why does -log(rate) turn this into negative cycle detection?', 'Bellman-Ford is O(V*E). When is that too slow, and what would a trading system do instead?', 'How would you return the actual cycle?'],
)

# ---------------------------------------------------------------- codebase rounds
CODEBASES = []

def codebase(**kw):
    """Multi-file project rounds, like Meta's AI-enabled round and Google's code comprehension round."""
    files = [(n, textwrap.dedent(c).strip('\n')) for n, c in kw['files']]
    fixed = [(n, textwrap.dedent(c).strip('\n')) for n, c in kw['solution']]
    harness = textwrap.dedent(kw['harness']).strip('\n')
    local = [n[:-3] for n, _ in files]
    def join(fs):
        out = []
        for _, c in fs:
            out += [l for l in c.split('\n') if not any(l.startswith(f'from {m} import') or l == f'import {m}' for m in local)]
        return '\n'.join(out) + '\n' + harness
    # every phase must fail on the starting code (except where noted) and pass on the solution
    for ph in kw['phases']:
        for t in ph['tests']:
            ns = {'__name__': 'solution'}; exec(join(fixed), ns)
            t['expected'] = norm(ns[t['name']]())
            if 'want' in t:
                assert t['expected'] == norm(t['want']), (kw['id'], t['name'], t['expected'])
            ns2 = {'__name__': 'solution'}
            try:
                exec(join(files), ns2); got = norm(ns2[t['name']]())
            except Exception as e:
                got = repr(e)
            t['startsFailing'] = got != t['expected']
            t.pop('want', None)
    kw['files'] = [{'name': n, 'code': c} for n, c in files]
    kw['solution'] = [{'name': n, 'code': c} for n, c in fixed]
    kw['harness'] = harness
    CODEBASES.append(kw)

codebase(
    id='cb-inventory', title='Inventory service', minutes=60, companies=['meta', 'google', 'amazon', 'openai'],
    source='Meta\'s AI-enabled round and Google\'s code comprehension pilot both hand you an unfamiliar multi-file codebase and move through fixing bugs, adding a feature, and optimizing.',
    files=[
        ('models.py', '''
        from dataclasses import dataclass

        @dataclass
        class Item:
            sku: str
            name: str
            price: float
            qty: int = 0

            def value(self):
                return self.price * self.qty
        '''),
        ('store.py', '''
        from models import Item

        class Inventory:
            """Stock for one warehouse.

            remove(sku, qty) must raise ValueError and change nothing if there is not enough stock.
            low_stock(threshold) returns skus whose qty is at or below threshold, in the order they were first added.
            """

            def __init__(self):
                self.items = {}
                self.order = []

            def add(self, sku, name, price, qty):
                if sku in self.items:
                    self.items[sku].qty += qty
                else:
                    self.items[sku] = Item(sku, name, price, qty)
                    self.order.append(sku)

            def remove(self, sku, qty):
                item = self.items[sku]
                item.qty -= qty
                return item.qty

            def low_stock(self, threshold):
                return [s for s in self.order if self.items[s].qty < threshold]

            def total_value(self):
                return round(sum(i.value() for i in self.items.values()), 2)
        '''),
        ('report.py', '''
        from store import Inventory

        def top_value(inv, k):
            """The k skus with the highest stock value (price * qty), highest first, ties by sku A to Z."""
            items = list(inv.items.values())
            result = []
            for _ in range(min(k, len(items))):
                best = items[0]
                for it in items:
                    if (-it.value(), it.sku) < (-best.value(), best.sku):
                        best = it
                result.append(best.sku)
                items.remove(best)
            return result
        '''),
    ],
    solution=[
        ('models.py', '''
        from dataclasses import dataclass

        @dataclass
        class Item:
            sku: str
            name: str
            price: float
            qty: int = 0

            def value(self):
                return self.price * self.qty
        '''),
        ('store.py', '''
        from models import Item

        class Inventory:
            def __init__(self):
                self.items = {}
                self.order = []
                self.changes = []          # (sku, delta), newest last

            def add(self, sku, name, price, qty):
                if sku in self.items:
                    self.items[sku].qty += qty
                else:
                    self.items[sku] = Item(sku, name, price, qty)
                    self.order.append(sku)
                self.changes.append((sku, qty))

            def remove(self, sku, qty):
                item = self.items.get(sku)
                if item is None or item.qty < qty:
                    raise ValueError('not enough stock')
                item.qty -= qty
                self.changes.append((sku, -qty))
                return item.qty

            def low_stock(self, threshold):
                return [s for s in self.order if self.items[s].qty <= threshold]

            def total_value(self):
                return round(sum(i.value() for i in self.items.values()), 2)

            def history(self, sku):
                return [d for s, d in self.changes if s == sku]

            def undo_last(self):
                if not self.changes:
                    return None
                sku, d = self.changes.pop()
                self.items[sku].qty -= d
                return sku
        '''),
        ('report.py', '''
        import heapq
        from store import Inventory

        def top_value(inv, k):
            return [it.sku for it in heapq.nsmallest(k, inv.items.values(), key=lambda it: (-it.value(), it.sku))]
        '''),
    ],
    harness='''
    import time

    def _inv():
        inv = Inventory()
        inv.add('A1', 'bolt', 0.5, 100)
        inv.add('B2', 'nut', 0.25, 10)
        inv.add('C3', 'gear', 12.0, 3)
        return inv

    def t_remove_too_much():
        inv = _inv()
        try:
            inv.remove('C3', 5)
            return 'no error raised'
        except ValueError:
            return inv.items['C3'].qty

    def t_low_stock_inclusive():
        return _inv().low_stock(10)

    def t_total_value():
        return _inv().total_value()

    def t_history():
        inv = _inv()
        inv.add('B2', 'nut', 0.25, 5)
        inv.remove('B2', 7)
        return inv.history('B2')

    def t_undo():
        inv = _inv()
        inv.remove('A1', 40)
        first = inv.undo_last()
        return [first, inv.items['A1'].qty, inv.history('A1')]

    def t_undo_empty():
        return Inventory().undo_last()

    def t_top_small():
        inv = _inv()
        inv.add('D4', 'pin', 1.0, 3)
        return top_value(inv, 3)

    def t_top_fast():
        inv = Inventory()
        for i in range(20000):
            inv.add(f'S{i:05d}', 'x', (i * 37) % 101 + 0.5, (i * 11) % 13)
        t = time.perf_counter()
        out = top_value(inv, 400)
        dt = time.perf_counter() - t
        return 'fast enough' if dt < 0.3 and out[:3] == ['S01242', 'S02555', 'S03868'] else f'too slow ({dt:.2f}s) or wrong'
    ''',
    phases=[
        dict(title='Fix the failing behavior', task='Two tests fail on the code you were given. The docstring in store.py is the spec. Find both bugs and fix them without breaking anything else.',
             tests=[dict(name='t_remove_too_much', label='removing more than you have raises ValueError and changes nothing', want=3), dict(name='t_low_stock_inclusive', label='low_stock includes items exactly at the threshold', want=['B2', 'C3']), dict(name='t_total_value', label='total value still right')]),
        dict(title='Add a feature', task='Add history(sku): every change to that sku in order, positive for add and negative for remove. Add undo_last(): revert the most recent change across all skus and return its sku, or None if there is nothing to undo. An undone change disappears from history.',
             tests=[dict(name='t_history', label='history records adds and removes', want=[10, 5, -7]), dict(name='t_undo', label='undo_last reverts the latest change'), dict(name='t_undo_empty', label='undo_last on a fresh inventory')]),
        dict(title='Make it fast', task='top_value in report.py is correct but times out on a big warehouse. Make it fast without changing its results (same order, same tie rule).',
             tests=[dict(name='t_top_small', label='same results on a small inventory'), dict(name='t_top_fast', label='20,000 items, top 400 in under 0.3 s', want='fast enough')]),
    ],
    followups=['How did you find each bug: by reading, by the failing test, or by asking the AI? How did you check its answer?', 'What is the complexity of top_value before and after?', 'undo_last and remove can interleave. Is there a case where undo makes qty negative?'],
)

codebase(
    id='cb-logs', title='Request log analyzer', minutes=60, companies=['meta', 'google', 'openai', 'amazon', 'microsoft'],
    source='Same format as the AI-enabled and code comprehension rounds: read code you did not write, fix it against a spec, extend it, then speed it up.',
    files=[
        ('parser.py', '''
        def parse_line(line):
            """'1700000000 GET /api/users?id=3 200 35' -> dict.

            path drops any query string (everything from '?').
            Blank or malformed lines return None.
            """
            ts, method, path, status, ms = line.split()
            return {'ts': int(ts), 'method': method, 'path': path, 'status': int(status), 'ms': int(ms)}

        def parse_all(lines):
            return [r for r in (parse_line(l) for l in lines) if r]
        '''),
        ('stats.py', '''
        from parser import parse_all

        def p95(records):
            """95th percentile latency by nearest rank: the value at rank ceil(0.95 * n) in sorted order (1 based)."""
            ms = sorted(r['ms'] for r in records)
            return ms[int(0.95 * len(ms))]

        def error_rate(records):
            """Share of responses with status 500 or above, per path, rounded to 3 decimals."""
            total, bad = {}, {}
            for r in records:
                total[r['path']] = total.get(r['path'], 0) + 1
                if r['status'] >= 500:
                    bad[r['path']] = bad.get(r['path'], 0) + 1
            return {p: round(bad.get(p, 0) / total[p], 3) for p in total}

        def rolling_errors(records, window):
            """For each record (sorted by ts), how many 5xx responses happened in (ts - window, ts]."""
            out = []
            for r in records:
                out.append(sum(1 for x in records if r['ts'] - window < x['ts'] <= r['ts'] and x['status'] >= 500))
            return out
        '''),
    ],
    solution=[
        ('parser.py', '''
        def parse_line(line):
            parts = line.split()
            if len(parts) != 5:
                return None
            ts, method, path, status, ms = parts
            try:
                return {'ts': int(ts), 'method': method, 'path': path.split('?')[0], 'status': int(status), 'ms': int(ms)}
            except ValueError:
                return None

        def parse_all(lines):
            return [r for r in (parse_line(l) for l in lines) if r]
        '''),
        ('stats.py', '''
        import math
        from collections import Counter
        from parser import parse_all

        def p95(records):
            ms = sorted(r['ms'] for r in records)
            return ms[math.ceil(0.95 * len(ms)) - 1]

        def error_rate(records):
            total, bad = {}, {}
            for r in records:
                total[r['path']] = total.get(r['path'], 0) + 1
                if r['status'] >= 500:
                    bad[r['path']] = bad.get(r['path'], 0) + 1
            return {p: round(bad.get(p, 0) / total[p], 3) for p in total}

        def top_paths(records, start, end, k):
            c = Counter(r['path'] for r in records if start <= r['ts'] < end)
            return [p for p, _ in sorted(c.items(), key=lambda x: (-x[1], x[0]))[:k]]

        def rolling_errors(records, window):
            out, lo, hi, bad = [], 0, 0, 0
            for r in records:
                while hi < len(records) and records[hi]['ts'] <= r['ts']:
                    bad += records[hi]['status'] >= 500
                    hi += 1
                while records[lo]['ts'] <= r['ts'] - window:
                    bad -= records[lo]['status'] >= 500
                    lo += 1
                out.append(bad)
            return out
        '''),
    ],
    harness='''
    import time

    LINES = [
        '100 GET /api/users?id=3 200 35',
        '101 GET /api/users 500 80',
        '',
        '102 POST /api/orders 201 120',
        'garbage line',
        '103 GET /api/orders?x=1 503 300',
        '104 GET /api/users 200 20',
    ]

    def t_parse():
        return [r['path'] for r in parse_all(LINES)]

    def t_p95():
        recs = [{'ts': i, 'path': '/x', 'status': 200, 'ms': i + 1} for i in range(20)]
        return p95(recs)

    def t_error_rate():
        return error_rate(parse_all(LINES))

    def t_top_paths():
        return top_paths(parse_all(LINES), 100, 104, 2)

    def t_top_paths_empty():
        return top_paths(parse_all(LINES), 200, 300, 3)

    def t_rolling_small():
        return rolling_errors(parse_all(LINES), 3)

    def t_rolling_fast():
        recs = [{'ts': i // 3, 'path': '/x', 'status': 500 if i % 7 == 0 else 200, 'ms': 1} for i in range(8000)]
        t = time.perf_counter()
        out = rolling_errors(recs, 50)
        dt = time.perf_counter() - t
        return 'fast enough' if dt < 0.5 and out[-1] == 21 and out[0] == 1 else f'too slow ({dt:.2f}s) or wrong'
    ''',
    phases=[
        dict(title='Fix the failing behavior', task='Read the docstrings: they are the spec. parse_all crashes on real logs and drops the wrong part of the path, and p95 returns the wrong rank. Fix both files.',
             tests=[dict(name='t_parse', label='skips blank and malformed lines, strips query strings', want=['/api/users', '/api/users', '/api/orders', '/api/orders', '/api/users']), dict(name='t_p95', label='p95 uses nearest rank', want=19), dict(name='t_error_rate', label='error rate per path')]),
        dict(title='Add a feature', task='Add top_paths(records, start, end, k) to stats.py: the k most requested paths with start <= ts < end, most requests first, ties by path A to Z. Return [] if nothing is in range.',
             tests=[dict(name='t_top_paths', label='top paths in a time range', want=['/api/orders', '/api/users']), dict(name='t_top_paths_empty', label='nothing in range', want=[])]),
        dict(title='Make it fast', task='rolling_errors is O(n squared) and times out on a day of logs. Records are sorted by ts. Make it linear without changing results (records sharing a timestamp all count each other).',
             tests=[dict(name='t_rolling_small', label='same results on the sample'), dict(name='t_rolling_fast', label='8,000 records in under 0.5 s', want='fast enough')]),
    ],
    followups=['Which bug did the docstring reveal that the tests alone would not?', 'Your rolling window uses two pointers. What invariant does each pointer keep?', 'Logs arrive as a live stream instead of a list. What would you keep in memory?'],
)

# ---------------------------------------------------------------- write
def ts_json(x):
    return json.dumps(x, ensure_ascii=False, indent=1)

out = ['// Generated by scripts/practical.py. Edit the script, not this file.',
       'export interface PracticalTest { args: unknown[]; expected: unknown; label: string; hidden: boolean }',
       'export interface PracticalPart { title: string; func: string; kind: "build" | "call"; prompt: string; tests: PracticalTest[]; edges: string[] }',
       'export interface PracticalProblem { id: string; title: string; minutes: number; companies: string[]; source: string; starter: string; reference: string; parts: PracticalPart[]; followups: string[] }',
       'export interface CodeFile { name: string; code: string }',
       'export interface CodebaseTest { name: string; label: string; expected: unknown; startsFailing: boolean }',
       'export interface CodebasePhase { title: string; task: string; tests: CodebaseTest[] }',
       'export interface CodebaseRound { id: string; title: string; minutes: number; companies: string[]; source: string; files: CodeFile[]; solution: CodeFile[]; harness: string; phases: CodebasePhase[]; followups: string[] }',
       f'export const PRACTICAL: PracticalProblem[] = {ts_json(PROBLEMS)};',
       f'export const CODEBASES: CodebaseRound[] = {ts_json(CODEBASES)};',
       ]
open('src/data/practical.ts', 'w').write('\n'.join(out) + '\n')
for p in PROBLEMS:
    print(p['id'], [len(x['tests']) for x in p['parts']])
for c in CODEBASES:
    print(c['id'], [[(t['name'], t['startsFailing']) for t in ph['tests']] for ph in c['phases']])

if __name__ == '__main__':
    import os
    if os.environ.get('DUMP'):
        json.dump({'p': PROBLEMS, 'c': CODEBASES}, open(os.environ['DUMP'], 'w'))
