"""Source of truth for Mock OA problems.

Run:  python3 scripts/oa_problems.py
It executes every reference solution against every test to fill in the
expected outputs, checks that each debugging snippet really fails before the
fix and passes after it, then writes src/data/oaProblems.ts.
"""
import copy, json, pathlib, textwrap

D = lambda s: textwrap.dedent(s).strip('\n') + '\n'
P = []

def debug(id, title, func, statement, buggy, fixed, tests, visible=2, cmp='exact', bug='', difficulty='easy', calls_share_state=False):
    P.append(dict(id=id, kind='debug', title=title, func=func, statement=statement, starter=D(buggy), solution=D(fixed),
                  tests=tests, visible=visible, cmp=cmp, explain=bug, difficulty=difficulty))

def code(id, title, func, statement, starter, solution, tests, visible=2, cmp='exact', explain='', difficulty='medium', tags=()):
    P.append(dict(id=id, kind='code', title=title, func=func, statement=statement, starter=D(starter), solution=D(solution),
                  tests=tests, visible=visible, cmp=cmp, explain=explain, difficulty=difficulty, tags=list(tags)))

# ───────────────────────── Debugging snippets ─────────────────────────
debug('dbg-sum-evens', 'Sum of even numbers', 'sum_evens',
  'Return the sum of all even numbers in nums.',
  '''
  def sum_evens(nums):
      total = 0
      for i in range(1, len(nums)):
          if nums[i] % 2 == 0:
              total += nums[i]
      return total
  ''', '''
  def sum_evens(nums):
      total = 0
      for i in range(len(nums)):
          if nums[i] % 2 == 0:
              total += nums[i]
      return total
  ''', [[[1, 2, 3, 4]], [[2, 3]], [[]], [[4, 4, 4]], [[-2, 5, 6]]],
  bug='Off by one: range(1, len(nums)) skips index 0, so an even first element is never counted.')

debug('dbg-find-max', 'Largest value', 'find_max',
  'Return the largest number in a non-empty list.',
  '''
  def find_max(nums):
      best = 0
      for x in nums:
          if x > best:
              best = x
      return best
  ''', '''
  def find_max(nums):
      best = nums[0]
      for x in nums:
          if x > best:
              best = x
      return best
  ''', [[[3, 9, 2]], [[5]], [[-4, -2, -9]], [[0, -1]], [[-7]]],
  bug='best starts at 0, so a list of only negative numbers returns 0. Start from nums[0].')

debug('dbg-binary-search', 'Binary search', 'binary_search',
  'Return the index of target in a sorted list, or -1 if it is not there.',
  '''
  def binary_search(nums, target):
      lo, hi = 0, len(nums) - 1
      while lo < hi:
          mid = (lo + hi) // 2
          if nums[mid] == target:
              return mid
          if nums[mid] < target:
              lo = mid + 1
          else:
              hi = mid - 1
      return -1
  ''', '''
  def binary_search(nums, target):
      lo, hi = 0, len(nums) - 1
      while lo <= hi:
          mid = (lo + hi) // 2
          if nums[mid] == target:
              return mid
          if nums[mid] < target:
              lo = mid + 1
          else:
              hi = mid - 1
      return -1
  ''', [[[1, 3, 5, 7], 5], [[1, 3, 5, 7], 4], [[1, 3, 5, 7], 7], [[2], 2], [[1, 3], 3], [[], 1]],
  bug='With hi = len - 1 (inclusive), the loop must be while lo <= hi. Using < never checks the last remaining element.')

debug('dbg-fizzbuzz', 'FizzBuzz', 'fizzbuzz',
  'Return a list of strings for 1..n: "FizzBuzz" for multiples of 15, "Fizz" for multiples of 3, "Buzz" for multiples of 5, otherwise the number.',
  '''
  def fizzbuzz(n):
      out = []
      for i in range(1, n + 1):
          if i % 3 == 0:
              out.append("Fizz")
          elif i % 5 == 0:
              out.append("Buzz")
          elif i % 15 == 0:
              out.append("FizzBuzz")
          else:
              out.append(str(i))
      return out
  ''', '''
  def fizzbuzz(n):
      out = []
      for i in range(1, n + 1):
          if i % 15 == 0:
              out.append("FizzBuzz")
          elif i % 3 == 0:
              out.append("Fizz")
          elif i % 5 == 0:
              out.append("Buzz")
          else:
              out.append(str(i))
      return out
  ''', [[5], [15], [1], [16]], visible=1,
  bug='The 15 check comes after the 3 check, so it can never run. The most specific condition must come first.')

debug('dbg-first-unique', 'First unique character', 'first_unique',
  'Return the index of the first character that appears exactly once in s, or -1.',
  '''
  def first_unique(s):
      counts = {}
      for ch in s:
          counts[ch] = counts.get(ch, 0) + 1
      for i, ch in enumerate(s):
          if counts[ch] == 1:
              return i
          return -1
  ''', '''
  def first_unique(s):
      counts = {}
      for ch in s:
          counts[ch] = counts.get(ch, 0) + 1
      for i, ch in enumerate(s):
          if counts[ch] == 1:
              return i
      return -1
  ''', [['leetcode'], ['loveleetcode'], ['aabb'], ['z'], ['aab']],
  bug='return -1 is indented inside the loop, so the function gives up after checking only the first character.')

debug('dbg-default-arg', 'Word counter called twice', 'count_words',
  'Return a dict counting each word in the list. The function is called many times, and each call must start fresh.',
  '''
  def count_words(words, counts={}):
      for w in words:
          counts[w] = counts.get(w, 0) + 1
      return counts
  ''', '''
  def count_words(words, counts=None):
      if counts is None:
          counts = {}
      for w in words:
          counts[w] = counts.get(w, 0) + 1
      return counts
  ''', [[['a', 'b', 'a']], [['b']], [['x', 'x']], [[]]], calls_share_state=True,
  bug='A mutable default ({}) is created once and shared by every call, so counts leak from one call into the next. Default to None and create the dict inside.')

debug('dbg-merge-sorted', 'Merge two sorted lists', 'merge_sorted',
  'Merge two sorted lists into one sorted list.',
  '''
  def merge_sorted(a, b):
      i = j = 0
      out = []
      while i < len(a) and j < len(b):
          if a[i] <= b[j]:
              out.append(a[i])
              i += 1
          else:
              out.append(b[j])
              j += 1
      out.extend(a[i:])
      return out
  ''', '''
  def merge_sorted(a, b):
      i = j = 0
      out = []
      while i < len(a) and j < len(b):
          if a[i] <= b[j]:
              out.append(a[i])
              i += 1
          else:
              out.append(b[j])
              j += 1
      out.extend(a[i:])
      out.extend(b[j:])
      return out
  ''', [[[1, 4], [2, 3, 9]], [[1, 2, 3], [4]], [[], [5, 6]], [[7], []], [[1, 1], [1]]],
  bug='Only the leftovers of a are copied. Whatever remains in b after the loop is dropped.')

debug('dbg-valid-brackets', 'Balanced brackets', 'is_balanced',
  'Return True if every (, [ and { is closed by the matching bracket in the right order.',
  '''
  def is_balanced(s):
      pairs = {")": "(", "]": "[", "}": "{"}
      stack = []
      for ch in s:
          if ch in "([{":
              stack.append(ch)
          elif ch in pairs:
              if not stack or stack.pop() != pairs[ch]:
                  return False
      return True
  ''', '''
  def is_balanced(s):
      pairs = {")": "(", "]": "[", "}": "{"}
      stack = []
      for ch in s:
          if ch in "([{":
              stack.append(ch)
          elif ch in pairs:
              if not stack or stack.pop() != pairs[ch]:
                  return False
      return not stack
  ''', [['()[]{}'], ['(]'], ['(('], ['{[()]}'], ['']],
  bug='Returning True at the end ignores brackets that were opened but never closed. Return not stack.')

debug('dbg-transpose', 'Transpose a matrix', 'transpose',
  'Return the transpose of an R x C matrix (rows become columns).',
  '''
  def transpose(m):
      rows, cols = len(m), len(m[0])
      out = [[0] * rows] * cols
      for r in range(rows):
          for c in range(cols):
              out[c][r] = m[r][c]
      return out
  ''', '''
  def transpose(m):
      rows, cols = len(m), len(m[0])
      out = [[0] * rows for _ in range(cols)]
      for r in range(rows):
          for c in range(cols):
              out[c][r] = m[r][c]
      return out
  ''', [[[[1, 2], [3, 4]]], [[[1, 2, 3]]], [[[1], [2], [3]]]], visible=1, difficulty='medium',
  bug='[[0] * rows] * cols makes cols references to the SAME inner list, so every row ends up identical. Build each row separately with a comprehension.')

debug('dbg-dedupe', 'Remove duplicates, keep order', 'dedupe',
  'Return the list with duplicates removed, keeping the first occurrence of each value in its original order.',
  '''
  def dedupe(items):
      return list(set(items))
  ''', '''
  def dedupe(items):
      seen = set()
      out = []
      for x in items:
          if x not in seen:
              seen.add(x)
              out.append(x)
      return out
  ''', [[[3, 1, 3, 2, 1]], [['b', 'a', 'b']], [[]], [[5, 5, 5]]],
  bug='A set has no order, so list(set(items)) can scramble the result. Track seen values and append in order.')

debug('dbg-is-prime', 'Prime check', 'is_prime',
  'Return True if n is a prime number.',
  '''
  def is_prime(n):
      for d in range(2, n // 2):
          if n % d == 0:
              return False
      return True
  ''', '''
  def is_prime(n):
      if n < 2:
          return False
      d = 2
      while d * d <= n:
          if n % d == 0:
              return False
          d += 1
      return True
  ''', [[7], [4], [1], [0], [2], [9], [97]],
  bug='Two bugs: n < 2 is never rejected, and range(2, n // 2) is empty for n = 4, so 4 is called prime. Check divisors up to the square root, inclusive.')

debug('dbg-second-largest', 'Second largest distinct value', 'second_largest',
  'Return the second largest DISTINCT value, or None if there is none.',
  '''
  def second_largest(nums):
      nums = sorted(nums, reverse=True)
      if len(nums) < 2:
          return None
      return nums[1]
  ''', '''
  def second_largest(nums):
      vals = sorted(set(nums), reverse=True)
      if len(vals) < 2:
          return None
      return vals[1]
  ''', [[[4, 1, 3]], [[5, 5, 2]], [[7]], [[2, 2]]],
  bug='Duplicates of the max are not removed, so [5, 5, 2] returns 5. Use set() before sorting.')

debug('dbg-balance', 'Account balance', 'final_balance',
  'Each transaction is ("deposit" or "withdraw", amount). Return the final balance starting from start. A withdrawal larger than the balance is skipped.',
  '''
  def final_balance(start, transactions):
      bal = start
      for kind, amt in transactions:
          if kind == "deposit":
              bal += amt
          elif kind == "withdraw" and amt < bal:
              bal -= amt
      return bal
  ''', '''
  def final_balance(start, transactions):
      bal = start
      for kind, amt in transactions:
          if kind == "deposit":
              bal += amt
          elif kind == "withdraw" and amt <= bal:
              bal -= amt
      return bal
  ''', [[100, [['withdraw', 30], ['deposit', 10]]], [50, [['withdraw', 50]]], [0, [['withdraw', 5]]], [20, [['deposit', 5], ['withdraw', 25]]]],
  bug='amt < bal skips a withdrawal of exactly the whole balance. It should be <=.')

debug('dbg-compound', 'Compound growth', 'grow',
  'Return the balance after investing amount at a yearly rate (0.05 = 5%) for years years, rounded to 2 decimals.',
  '''
  def grow(amount, rate, years):
      for _ in range(years - 1):
          amount = amount * (1 + rate)
      return round(amount, 2)
  ''', '''
  def grow(amount, rate, years):
      for _ in range(years):
          amount = amount * (1 + rate)
      return round(amount, 2)
  ''', [[1000, 0.05, 1], [1000, 0.05, 3], [500, 0.1, 0], [100, 0.07, 10]],
  bug='range(years - 1) applies growth one year too few.')

debug('dbg-flatten', 'Flatten nested lists', 'flatten',
  'Flatten an arbitrarily nested list of integers into a single list.',
  '''
  def flatten(x):
      out = []
      for item in x:
          if isinstance(item, list):
              out.append(flatten(item))
          else:
              out.append(item)
      return out
  ''', '''
  def flatten(x):
      out = []
      for item in x:
          if isinstance(item, list):
              out.extend(flatten(item))
          else:
              out.append(item)
      return out
  ''', [[[1, [2, 3], 4]], [[[1, [2]], 3]], [[]], [[[[]]]]], difficulty='medium',
  bug='append adds the flattened sublist as ONE element, keeping the nesting. extend adds its items one by one.')

debug('dbg-reverse-words', 'Reverse word order', 'reverse_words',
  'Return the words of s in reverse order joined by single spaces. s may have extra spaces anywhere.',
  '''
  def reverse_words(s):
      return " ".join(reversed(s.split(" ")))
  ''', '''
  def reverse_words(s):
      return " ".join(reversed(s.split()))
  ''', [['the sky is blue'], ['  hello world  '], ['a   b'], ['one']],
  bug='split(" ") keeps empty strings for repeated spaces. split() with no argument splits on any run of whitespace and drops empties.')

debug('dbg-running-sum', 'Running total', 'running_sum',
  'Return a list where out[i] is the sum of nums[0..i].',
  '''
  def running_sum(nums):
      out = nums[:]
      for i in range(1, len(nums)):
          out[i] = nums[i] + nums[i - 1]
      return out
  ''', '''
  def running_sum(nums):
      out = nums[:]
      for i in range(1, len(nums)):
          out[i] = out[i - 1] + nums[i]
      return out
  ''', [[[1, 2, 3, 4]], [[5]], [[]], [[3, -1, 2]]],
  bug='It adds the previous INPUT value, not the previous running total. Use out[i - 1].')

debug('dbg-count-vowels', 'Count vowels', 'count_vowels',
  'Return how many vowels (a, e, i, o, u, any case) are in s.',
  '''
  def count_vowels(s):
      return sum(1 for ch in s if ch in "aeiou")
  ''', '''
  def count_vowels(s):
      return sum(1 for ch in s.lower() if ch in "aeiou")
  ''', [['hello'], ['AEIOU'], ['xyz'], ['Programming']],
  bug='Uppercase vowels are not counted. Lowercase the string first.')

# ───────────────────────── Coding problems ─────────────────────────
code('oa-two-sum', 'Pair with target sum', 'pair_indices',
  'Given a list of integers nums and an integer target, return the indices [i, j] with i < j such that nums[i] + nums[j] == target. Exactly one answer exists.\n\nExample: nums = [2, 7, 11, 15], target = 9 returns [0, 1].',
  '''
  def pair_indices(nums, target):
      # your code here
      pass
  ''', '''
  def pair_indices(nums, target):
      seen = {}
      for i, x in enumerate(nums):
          if target - x in seen:
              return [seen[target - x], i]
          seen[x] = i
  ''', [[[2, 7, 11, 15], 9], [[3, 2, 4], 6], [[3, 3], 6], [[-1, -2, -3, -4, -5], -8], [[1, 5, 1, 5], 10], [list(range(1, 2001)), 3999]],
  difficulty='easy', tags=['hashing'], explain='One pass with a dict from value to index. For each x, check whether target - x was already seen. O(N).')

code('oa-big-spenders', 'Customers over a spending limit', 'big_spenders',
  'You get transaction records as strings "customer,amount" (amount is an integer number of dollars). Return the customers whose total spend is strictly greater than limit, sorted alphabetically.\n\nExample: records = ["ann,40", "bob,10", "ann,70"], limit = 100 returns ["ann"].',
  '''
  def big_spenders(records, limit):
      # your code here
      pass
  ''', '''
  def big_spenders(records, limit):
      totals = {}
      for r in records:
          name, amt = r.split(",")
          totals[name] = totals.get(name, 0) + int(amt)
      return sorted(n for n, t in totals.items() if t > limit)
  ''', [[['ann,40', 'bob,10', 'ann,70'], 100], [['a,1'], 0], [['x,50', 'y,50', 'x,1', 'y,0'], 50], [[], 10], [['zed,5', 'amy,5', 'bo,5'], 4]],
  difficulty='easy', tags=['hashing'], explain='Parse each record, accumulate totals in a dict, then filter and sort. O(N log N) for the final sort.')

code('oa-stock', 'Best single trade', 'max_profit',
  'prices[i] is a stock price on day i. Buy once and sell once on a later day. Return the maximum profit, or 0 if no profit is possible.\n\nExample: [7, 1, 5, 3, 6, 4] returns 5.',
  '''
  def max_profit(prices):
      # your code here
      pass
  ''', '''
  def max_profit(prices):
      lowest = float("inf")
      best = 0
      for p in prices:
          lowest = min(lowest, p)
          best = max(best, p - lowest)
      return best
  ''', [[[7, 1, 5, 3, 6, 4]], [[7, 6, 4, 3, 1]], [[1]], [[2, 4, 1, 7]], [[3, 3, 3]], [list(range(10000, 0, -1)) + [10001]]],
  difficulty='easy', tags=['sliding-window'], explain='Track the cheapest price so far and the best profit selling today. O(N), O(1) space.')

code('oa-merge-intervals', 'Merge booking intervals', 'merge_intervals',
  'Given a list of [start, end] bookings (not sorted), merge all overlapping or touching bookings and return them sorted by start. [1, 3] and [3, 5] count as overlapping.\n\nExample: [[1, 3], [2, 6], [8, 10]] returns [[1, 6], [8, 10]].',
  '''
  def merge_intervals(intervals):
      # your code here
      pass
  ''', '''
  def merge_intervals(intervals):
      out = []
      for s, e in sorted(intervals):
          if out and s <= out[-1][1]:
              out[-1][1] = max(out[-1][1], e)
          else:
              out.append([s, e])
      return out
  ''', [[[[1, 3], [2, 6], [8, 10]]], [[[1, 4], [4, 5]]], [[[5, 6], [1, 2]]], [[[1, 10], [2, 3], [4, 5]]], [[]], [[[1, 1]]]],
  tags=['intervals'], explain='Sort by start, then extend the last merged interval when the next one starts at or before its end. O(N log N).')

code('oa-top-words', 'Most frequent words', 'top_words',
  'Return the k most frequent words. Sort by count descending, and break ties alphabetically.\n\nExample: words = ["b", "a", "b", "c", "a", "b"], k = 2 returns ["b", "a"].',
  '''
  def top_words(words, k):
      # your code here
      pass
  ''', '''
  from collections import Counter
  def top_words(words, k):
      c = Counter(words)
      return sorted(c, key=lambda w: (-c[w], w))[:k]
  ''', [[['b', 'a', 'b', 'c', 'a', 'b'], 2], [['x', 'y', 'z'], 2], [['the', 'day', 'is', 'sunny', 'the', 'the', 'sunny', 'is', 'is'], 4], [['solo'], 1]],
  tags=['top-k'], explain='Count with Counter, then sort by (-count, word). A heap of size k also works in O(N log k).')

code('oa-longest-unique', 'Longest run without repeats', 'longest_unique',
  'Return the length of the longest substring of s with no repeated characters.\n\nExample: "abcabcbb" returns 3.',
  '''
  def longest_unique(s):
      # your code here
      pass
  ''', '''
  def longest_unique(s):
      last = {}
      left = best = 0
      for i, ch in enumerate(s):
          if ch in last and last[ch] >= left:
              left = last[ch] + 1
          last[ch] = i
          best = max(best, i - left + 1)
      return best
  ''', [['abcabcbb'], ['bbbbb'], ['pwwkew'], [''], ['abba'], ['a' * 5000 + 'bcdef']],
  tags=['sliding-window'], explain='Sliding window: when a character repeats inside the window, jump the left edge past its last position. O(N).')

code('oa-rooms', 'Meeting rooms needed', 'rooms_needed',
  'Each meeting is [start, end). Return the minimum number of rooms so that no two meetings in the same room overlap. A meeting ending at time t frees the room for one starting at t.\n\nExample: [[0, 30], [5, 10], [15, 20]] returns 2.',
  '''
  def rooms_needed(meetings):
      # your code here
      pass
  ''', '''
  import heapq
  def rooms_needed(meetings):
      ends = []
      for s, e in sorted(meetings):
          if ends and ends[0] <= s:
              heapq.heappop(ends)
          heapq.heappush(ends, e)
      return len(ends)
  ''', [[[[0, 30], [5, 10], [15, 20]]], [[[7, 10], [2, 4]]], [[]], [[[1, 5], [5, 10]]], [[[1, 10], [2, 9], [3, 8], [4, 7]]]],
  tags=['intervals', 'top-k'], explain='Sort by start, keep a min-heap of end times. Reuse a room when the earliest end is at or before the new start. O(N log N).')

code('oa-spread', 'Days until everyone is notified', 'days_to_notify',
  'A grid has 2 = already notified, 1 = not yet, 0 = empty desk. Each day, every notified person tells the people directly up, down, left and right. Return the number of days until everyone is notified, or -1 if someone never will be.\n\nExample: [[2, 1, 1], [1, 1, 0], [0, 1, 1]] returns 4.',
  '''
  def days_to_notify(grid):
      # your code here
      pass
  ''', '''
  from collections import deque
  def days_to_notify(grid):
      R, C = len(grid), len(grid[0])
      q = deque()
      waiting = 0
      for r in range(R):
          for c in range(C):
              if grid[r][c] == 2:
                  q.append((r, c))
              elif grid[r][c] == 1:
                  waiting += 1
      days = 0
      while q and waiting:
          for _ in range(len(q)):
              r, c = q.popleft()
              for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                  nr, nc = r + dr, c + dc
                  if 0 <= nr < R and 0 <= nc < C and grid[nr][nc] == 1:
                      grid[nr][nc] = 2
                      waiting -= 1
                      q.append((nr, nc))
          days += 1
      return days if waiting == 0 else -1
  ''', [[[[2, 1, 1], [1, 1, 0], [0, 1, 1]]], [[[2, 1, 1], [0, 1, 1], [1, 0, 1]]], [[[0, 2]]], [[[1]]], [[[2, 2], [1, 1]]]],
  tags=['bfs'], explain='Multi-source BFS: start with every notified person in the queue, process one level per day. O(R x C).')

code('oa-min-add', 'Fix the parentheses', 'min_add',
  'Given a string of ( and ), return the minimum number of parentheses you must insert to make it valid.\n\nExample: "())" returns 1, "(((" returns 3.',
  '''
  def min_add(s):
      # your code here
      pass
  ''', '''
  def min_add(s):
      open_ = need = 0
      for ch in s:
          if ch == "(":
              open_ += 1
          elif open_:
              open_ -= 1
          else:
              need += 1
      return open_ + need
  ''', [['())'], ['((('], ['()'], ['()))(('], [''], [')(']],
  difficulty='easy', tags=['monotonic-stack'], explain='Count unmatched opens. A ) with no open needs an insert. At the end every leftover ( needs a ). O(N).')

code('oa-rebalance', 'Portfolio rebalancing', 'rebalance',
  'holdings maps each fund to its current dollar value. targets maps each fund to its target weight (weights sum to 1). Return a dict of the dollar amount to buy (positive) or sell (negative) for each fund so the portfolio matches the targets, rounded to 2 decimals.\n\nExample: holdings = {"stock": 70, "bond": 30}, targets = {"stock": 0.6, "bond": 0.4} returns {"stock": -10.0, "bond": 10.0}.',
  '''
  def rebalance(holdings, targets):
      # your code here
      pass
  ''', '''
  def rebalance(holdings, targets):
      total = sum(holdings.values())
      return {f: round(total * w - holdings.get(f, 0), 2) for f, w in targets.items()}
  ''', [[{'stock': 70, 'bond': 30}, {'stock': 0.6, 'bond': 0.4}], [{'a': 100}, {'a': 0.5, 'b': 0.5}], [{'x': 33.33, 'y': 66.67}, {'x': 0.5, 'y': 0.5}], [{'a': 10, 'b': 20, 'c': 70}, {'a': 0.2, 'b': 0.3, 'c': 0.5}]],
  difficulty='easy', tags=['hashing'], explain='Target value = total x weight. Trade = target − current, and a fund you do not hold yet starts at 0.')

code('oa-least-loaded', 'Assign jobs to servers', 'assign_jobs',
  'There are k servers, all idle at load 0. Jobs arrive in order with a given cost. Each job goes to the server with the smallest current load (lowest server index on ties). Return the final load of every server, by index.\n\nExample: k = 2, jobs = [5, 3, 2] returns [5, 5].',
  '''
  def assign_jobs(k, jobs):
      # your code here
      pass
  ''', '''
  import heapq
  def assign_jobs(k, jobs):
      heap = [(0, i) for i in range(k)]
      loads = [0] * k
      for cost in jobs:
          load, i = heapq.heappop(heap)
          loads[i] = load + cost
          heapq.heappush(heap, (loads[i], i))
      return loads
  ''', [[2, [5, 3, 2]], [3, [4, 4, 4, 4]], [1, [1, 2, 3]], [3, []], [2, [1, 1, 1, 1, 10]]],
  tags=['top-k'], explain='Min-heap of (load, index). Pop the least loaded, add the job, push it back. O(N log k).')

code('oa-error-codes', 'Most common error code', 'top_error',
  'Each log line looks like "2026-11-18 12:00:01 ERROR 503 upstream timeout" or "... INFO ...". Return the most common error code among ERROR lines as a string, choosing the smallest code on ties. Return "" if there are no errors.',
  '''
  def top_error(logs):
      # your code here
      pass
  ''', '''
  from collections import Counter
  def top_error(logs):
      c = Counter()
      for line in logs:
          parts = line.split()
          if len(parts) >= 4 and parts[2] == "ERROR":
              c[parts[3]] += 1
      if not c:
          return ""
      return min(c, key=lambda code: (-c[code], code))
  ''', [[['2026-11-18 12:00:01 ERROR 503 timeout', '2026-11-18 12:00:02 INFO ok', '2026-11-18 12:00:03 ERROR 503 again', '2026-11-18 12:00:04 ERROR 404 missing']],
        [['d t INFO fine']], [['d t ERROR 500 x', 'd t ERROR 404 y']], [[]]],
  difficulty='easy', tags=['hashing'], explain='Split each line, count codes on ERROR lines with a Counter, and pick the max count with the smallest code as tiebreak.')

code('oa-islands', 'Count office clusters', 'count_clusters',
  'A grid has "1" for an occupied desk and "0" for empty. A cluster is a group of occupied desks connected up, down, left or right. Return the number of clusters.',
  '''
  def count_clusters(grid):
      # your code here
      pass
  ''', '''
  def count_clusters(grid):
      R, C = len(grid), len(grid[0]) if grid else 0
      seen = set()
      def fill(r, c):
          stack = [(r, c)]
          seen.add((r, c))
          while stack:
              r, c = stack.pop()
              for nr, nc in ((r+1, c), (r-1, c), (r, c+1), (r, c-1)):
                  if 0 <= nr < R and 0 <= nc < C and grid[nr][nc] == "1" and (nr, nc) not in seen:
                      seen.add((nr, nc))
                      stack.append((nr, nc))
      count = 0
      for r in range(R):
          for c in range(C):
              if grid[r][c] == "1" and (r, c) not in seen:
                  count += 1
                  fill(r, c)
      return count
  ''', [[[['1', '1', '0'], ['0', '1', '0'], ['0', '0', '1']]], [[['0']]], [[['1', '0', '1'], ['0', '1', '0'], ['1', '0', '1']]], [[['1'] * 60 for _ in range(60)]]],
  tags=['matrix'], explain='Scan cells. Each unvisited "1" starts a new cluster, and an iterative DFS marks its whole group. O(R x C).')

code('oa-coins', 'Fewest coins', 'fewest_coins',
  'Return the fewest coins needed to make amount using unlimited coins of the given values, or -1 if it is impossible.\n\nExample: coins = [1, 3, 4], amount = 6 returns 2.',
  '''
  def fewest_coins(coins, amount):
      # your code here
      pass
  ''', '''
  def fewest_coins(coins, amount):
      INF = float("inf")
      dp = [0] + [INF] * amount
      for a in range(1, amount + 1):
          for c in coins:
              if c <= a and dp[a - c] + 1 < dp[a]:
                  dp[a] = dp[a - c] + 1
      return dp[amount] if dp[amount] != INF else -1
  ''', [[[1, 3, 4], 6], [[2], 3], [[1], 0], [[1, 2, 5], 11], [[186, 419, 83, 408], 6249]],
  tags=['dp'], explain='dp[a] = fewest coins for amount a = min(dp[a - c] + 1). Greedy fails on [1, 3, 4] with 6. O(amount x coins).')

code('oa-product', 'Product of all others', 'product_others',
  'Return a list where out[i] is the product of every element except nums[i], without using division.',
  '''
  def product_others(nums):
      # your code here
      pass
  ''', '''
  def product_others(nums):
      n = len(nums)
      out = [1] * n
      left = 1
      for i in range(n):
          out[i] = left
          left *= nums[i]
      right = 1
      for i in range(n - 1, -1, -1):
          out[i] *= right
          right *= nums[i]
      return out
  ''', [[[1, 2, 3, 4]], [[0, 4, 5]], [[-1, 1, 0, -3, 3]], [[2, 3]]],
  tags=['prefix-sum'], explain='Left pass stores the product before i, right pass multiplies in the product after i. O(N), no division.')

code('oa-subarray-k', 'Count target-sum windows', 'count_k',
  'Return how many contiguous subarrays of nums sum to exactly k. Values can be negative.\n\nExample: nums = [1, 1, 1], k = 2 returns 2.',
  '''
  def count_k(nums, k):
      # your code here
      pass
  ''', '''
  def count_k(nums, k):
      seen = {0: 1}
      run = ans = 0
      for x in nums:
          run += x
          ans += seen.get(run - k, 0)
          seen[run] = seen.get(run, 0) + 1
      return ans
  ''', [[[1, 1, 1], 2], [[1, 2, 3], 3], [[1, -1, 0], 0], [[3, 4, 7, 2, -3, 1, 4, 2], 7], [[0] * 300, 0]],
  tags=['prefix-sum'], explain='Prefix sums with a Counter: subarrays ending here that sum to k = how many earlier prefixes equal running − k. O(N).')

code('oa-rate-limit', 'API rate limiter', 'allowed',
  'Requests arrive at the given timestamps (seconds, non-decreasing). A client may make at most limit requests in any window of window seconds: a request at time t is allowed only if fewer than limit ALLOWED requests happened in (t − window, t]. Return a list of True/False for each request.\n\nExample: times = [1, 1, 2, 11], limit = 2, window = 10 returns [True, True, False, True].',
  '''
  def allowed(times, limit, window):
      # your code here
      pass
  ''', '''
  from collections import deque
  def allowed(times, limit, window):
      q = deque()
      out = []
      for t in times:
          while q and q[0] <= t - window:
              q.popleft()
          if len(q) < limit:
              q.append(t)
              out.append(True)
          else:
              out.append(False)
      return out
  ''', [[[1, 1, 2, 11], 2, 10], [[1, 2, 3], 5, 1], [[5, 5, 5, 5], 1, 1], [[], 3, 10], [[0, 10, 20], 1, 10]],
  tags=['sliding-window'], explain='Keep a deque of allowed timestamps. Drop ones that fell out of the window, then allow if fewer than limit remain. O(N).')

code('oa-anagram-groups', 'Group anagrams', 'group_anagrams',
  'Group words that are anagrams of each other. Sort the words inside each group alphabetically, and sort the groups by their first word.\n\nExample: ["eat", "tea", "tan", "ate", "nat", "bat"] returns [["ate", "eat", "tea"], ["bat"], ["nat", "tan"]].',
  '''
  def group_anagrams(words):
      # your code here
      pass
  ''', '''
  from collections import defaultdict
  def group_anagrams(words):
      g = defaultdict(list)
      for w in words:
          g["".join(sorted(w))].append(w)
      return sorted(sorted(v) for v in g.values())
  ''', [[['eat', 'tea', 'tan', 'ate', 'nat', 'bat']], [['']], [['a']], [['ab', 'ba', 'abc', 'cab', 'bca', 'x']]],
  tags=['hashing'], explain='Key each word by its sorted letters in a defaultdict(list), then sort for a deterministic answer. O(N K log K).')


# ───────────────── Multi-part builds (OpenAI / Jane Street style) ─────────────────
def build(id, title, cls, statement, starter, solution, tests, visible=1, explain='', difficulty='medium', tags=()):
    """tests: each is a list of [method, args] calls; the first is ["__init__", args]."""
    P.append(dict(id=id, kind='build', title=title, func=cls, statement=statement, starter=D(starter), solution=D(solution),
                  tests=tests, visible=visible, cmp='exact', explain=explain, difficulty=difficulty, tags=list(tags)))

build('bd-kv-txn', 'Key-value store with transactions', 'KVStore',
  'Build class KVStore with:\n  set(key, value), get(key) returning the value or None, delete(key),\n  begin() to start a transaction, commit() to keep all changes since the matching begin, and rollback() to undo them. Transactions can be nested: rollback only undoes the innermost open transaction. commit() and rollback() with no open transaction return False, otherwise True.\n\nThis is the kind of multi-part practical problem OpenAI and Jane Street like: get part 1 working, then extend it.',
  """
  class KVStore:
      def __init__(self):
          pass

      def set(self, key, value):
          pass

      def get(self, key):
          pass

      def delete(self, key):
          pass

      def begin(self):
          pass

      def commit(self):
          pass

      def rollback(self):
          pass
  """, """
  _MISSING = object()

  class KVStore:
      def __init__(self):
          self.data = {}
          self.undo = []          # one dict per open transaction: key -> old value

      def _remember(self, key):
          if self.undo and key not in self.undo[-1]:
              self.undo[-1][key] = self.data.get(key, _MISSING)

      def set(self, key, value):
          self._remember(key)
          self.data[key] = value

      def get(self, key):
          return self.data.get(key)

      def delete(self, key):
          self._remember(key)
          self.data.pop(key, None)

      def begin(self):
          self.undo.append({})

      def commit(self):
          if not self.undo:
              return False
          top = self.undo.pop()
          if self.undo:
              for k, v in top.items():
                  self.undo[-1].setdefault(k, v)
          return True

      def rollback(self):
          if not self.undo:
              return False
          for k, v in self.undo.pop().items():
              if v is _MISSING:
                  self.data.pop(k, None)
              else:
                  self.data[k] = v
          return True
  """, [
    [['__init__', []], ['set', ['a', 1]], ['get', ['a']], ['delete', ['a']], ['get', ['a']]],
    [['__init__', []], ['set', ['a', 1]], ['begin', []], ['set', ['a', 2]], ['get', ['a']], ['rollback', []], ['get', ['a']], ['rollback', []]],
    [['__init__', []], ['begin', []], ['set', ['x', 5]], ['begin', []], ['set', ['x', 6]], ['commit', []], ['get', ['x']], ['rollback', []], ['get', ['x']]],
    [['__init__', []], ['set', ['k', 1]], ['begin', []], ['delete', ['k']], ['get', ['k']], ['rollback', []], ['get', ['k']], ['commit', []]],
    [['__init__', []], ['begin', []], ['set', ['n', 1]], ['set', ['n', 2]], ['begin', []], ['delete', ['n']], ['rollback', []], ['get', ['n']], ['commit', []], ['get', ['n']]],
  ], explain='Keep a stack of undo logs. The first time a key changes inside a transaction, save its old value (or a MISSING marker). Rollback restores the top log. Commit merges the top log into the one below so an outer rollback still works.', tags=['design'])

build('bd-lru', 'LRU cache from scratch', 'LRUCache',
  'Build class LRUCache(capacity) with get(key) returning the value or -1, and put(key, value). When a put would exceed capacity, evict the least recently used key first. Both get and put count as a use. Aim for O(1) per call.',
  """
  class LRUCache:
      def __init__(self, capacity):
          pass

      def get(self, key):
          pass

      def put(self, key, value):
          pass
  """, """
  from collections import OrderedDict

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
          if key in self.d:
              self.d.move_to_end(key)
          self.d[key] = value
          if len(self.d) > self.cap:
              self.d.popitem(last=False)
  """, [
    [['__init__', [2]], ['put', [1, 1]], ['put', [2, 2]], ['get', [1]], ['put', [3, 3]], ['get', [2]], ['put', [4, 4]], ['get', [1]], ['get', [3]], ['get', [4]]],
    [['__init__', [1]], ['put', [1, 1]], ['put', [1, 5]], ['get', [1]], ['put', [2, 2]], ['get', [1]], ['get', [2]]],
    [['__init__', [2]], ['get', [9]], ['put', [1, 1]], ['put', [2, 2]], ['put', [1, 10]], ['put', [3, 3]], ['get', [2]], ['get', [1]]],
  ], explain='A dict for O(1) lookup plus an ordering you can update in O(1): OrderedDict.move_to_end and popitem(last=False), or a hand-written doubly linked list with head and tail sentinels.', tags=['design'])

build('bd-ring', 'Ring buffer (circular queue)', 'RingBuffer',
  'Build class RingBuffer(capacity) backed by a fixed-size list. push(x) adds to the back and returns False if full, pop() removes and returns the front or None if empty, peek() returns the front without removing it (or None), and size() returns the count. Do not use deque.',
  """
  class RingBuffer:
      def __init__(self, capacity):
          pass

      def push(self, x):
          pass

      def pop(self):
          pass

      def peek(self):
          pass

      def size(self):
          pass
  """, """
  class RingBuffer:
      def __init__(self, capacity):
          self.buf = [None] * capacity
          self.head = 0
          self.count = 0

      def push(self, x):
          if self.count == len(self.buf):
              return False
          self.buf[(self.head + self.count) % len(self.buf)] = x
          self.count += 1
          return True

      def pop(self):
          if not self.count:
              return None
          x = self.buf[self.head]
          self.head = (self.head + 1) % len(self.buf)
          self.count -= 1
          return x

      def peek(self):
          return self.buf[self.head] if self.count else None

      def size(self):
          return self.count
  """, [
    [['__init__', [2]], ['push', [1]], ['push', [2]], ['push', [3]], ['pop', []], ['push', [3]], ['peek', []], ['size', []]],
    [['__init__', [3]], ['pop', []], ['peek', []], ['push', ['a']], ['pop', []], ['pop', []], ['size', []]],
    [['__init__', [2]], ['push', [1]], ['pop', []], ['push', [2]], ['push', [3]], ['pop', []], ['pop', []], ['push', [4]], ['push', [5]], ['size', []]],
  ], difficulty='easy', explain='Track head and count. The back slot is (head + count) % capacity. Wrapping with modulo means no shifting, so every operation is O(1).', tags=['design'])

build('bd-min-heap', 'Min-heap from scratch', 'MinHeap',
  'Build class MinHeap without heapq: push(x), pop() returning the smallest or None if empty, peek() returning the smallest without removing it (or None), and size().',
  """
  class MinHeap:
      def __init__(self):
          pass

      def push(self, x):
          pass

      def pop(self):
          pass

      def peek(self):
          pass

      def size(self):
          pass
  """, """
  class MinHeap:
      def __init__(self):
          self.a = []

      def push(self, x):
          a = self.a
          a.append(x)
          i = len(a) - 1
          while i and a[(i - 1) // 2] > a[i]:
              p = (i - 1) // 2
              a[i], a[p] = a[p], a[i]
              i = p

      def pop(self):
          a = self.a
          if not a:
              return None
          top = a[0]
          last = a.pop()
          if a:
              a[0] = last
              i = 0
              while True:
                  l, r, small = 2 * i + 1, 2 * i + 2, i
                  if l < len(a) and a[l] < a[small]:
                      small = l
                  if r < len(a) and a[r] < a[small]:
                      small = r
                  if small == i:
                      break
                  a[i], a[small] = a[small], a[i]
                  i = small
          return top

      def peek(self):
          return self.a[0] if self.a else None

      def size(self):
          return len(self.a)
  """, [
    [['__init__', []], ['push', [5]], ['push', [1]], ['push', [3]], ['peek', []], ['pop', []], ['pop', []], ['pop', []], ['pop', []]],
    [['__init__', []], ['push', [2]], ['push', [2]], ['push', [1]], ['size', []], ['pop', []], ['pop', []], ['size', []]],
    [['__init__', []]] + [['push', [x]] for x in [9, 4, 7, 1, 8, 2, 6, 3, 5, 0]] + [['pop', []] for _ in range(10)],
  ], explain='Store the heap in a list where node i has children 2i + 1 and 2i + 2. Push sifts up, pop moves the last item to the root and sifts down. O(log N) each.', tags=['top-k'])

build('bd-trie', 'Autocomplete trie', 'Autocomplete',
  'Build class Autocomplete with insert(word) and suggest(prefix) that returns up to 3 stored words starting with prefix, in alphabetical order. Inserting a word twice stores it once.',
  """
  class Autocomplete:
      def __init__(self):
          pass

      def insert(self, word):
          pass

      def suggest(self, prefix):
          pass
  """, """
  class Autocomplete:
      def __init__(self):
          self.root = {}

      def insert(self, word):
          node = self.root
          for ch in word:
              node = node.setdefault(ch, {})
          node["$"] = True

      def suggest(self, prefix):
          node = self.root
          for ch in prefix:
              if ch not in node:
                  return []
              node = node[ch]
          out = []
          def dfs(n, path):
              if len(out) == 3:
                  return
              if "$" in n:
                  out.append(prefix + path)
              for ch in sorted(k for k in n if k != "$"):
                  dfs(n[ch], path + ch)
          dfs(node, "")
          return out
  """, [
    [['__init__', []], ['insert', ['car']], ['insert', ['cart']], ['insert', ['care']], ['insert', ['cat']], ['suggest', ['ca']], ['suggest', ['car']], ['suggest', ['dog']]],
    [['__init__', []], ['insert', ['a']], ['insert', ['a']], ['suggest', ['a']], ['suggest', ['']], ['insert', ['ab']], ['suggest', ['']]],
  ], explain='A trie of nested dicts with an end marker. Walk to the prefix node, then DFS children in alphabetical order and stop after 3 words.', tags=['design'])

# ───────────────────────── Validate and emit ─────────────────────────
def run(src, func, tests, share=False, kind='code'):
    ns = {}
    exec(src, ns)
    out = []
    for args in tests:
        if kind == 'build':
            obj = None
            res = []
            for method, a in args:
                if method == '__init__':
                    obj = ns[func](*copy.deepcopy(a)); res.append(None)
                else:
                    res.append(getattr(obj, method)(*copy.deepcopy(a)))
            out.append(res)
        else:
            out.append(ns[func](*copy.deepcopy(args)))
    return out

def same(a, b, cmp):
    if cmp == 'unordered':
        return sorted(map(json.dumps, a)) == sorted(map(json.dumps, b))
    return json.loads(json.dumps(a)) == json.loads(json.dumps(b))

for p in P:
    expected = run(p['solution'], p['func'], p['tests'], kind=p['kind'])
    p['expected'] = json.loads(json.dumps(expected))
    if p['kind'] == 'debug':
        try:
            got = run(p['starter'], p['func'], p['tests'])
            bad = [i for i, (g, e) in enumerate(zip(got, expected)) if not same(g, e, p['cmp'])]
        except Exception:
            bad = ['crash']
        assert bad, f"{p['id']}: buggy version passes every test"
        assert len(p['starter'].splitlines()) <= len(p['solution'].splitlines()) + 6
    else:
        # starter must not accidentally pass
        try:
            assert run(p['starter'], p['func'], p['tests'][:1], kind=p['kind']) != expected[:1], p['id']
        except AttributeError:
            pass

print(len([p for p in P if p['kind'] == 'debug']), 'debug,', len([p for p in P if p['kind'] == 'code']), 'coding,', len([p for p in P if p['kind'] == 'build']), 'builds: all references verified')
root = pathlib.Path(__file__).resolve().parent.parent
(root / 'src/data/oaProblems.ts').write_text(
    '// Generated by scripts/oa_problems.py. Edit that file, then run: python3 scripts/oa_problems.py\n'
    'import type { OAProblem } from \'../types\';\n\n'
    'export const OA_PROBLEMS: OAProblem[] = ' + json.dumps(P, indent=1) + ';\n')
