"""Source of truth for Blueprint Builder.

Each problem is a function broken into numbered plain-English steps. Every step
has three hint levels: a syntax clue, a fill-in-the-blank template, and the
exact lines. Running this file stitches the steps into a full solution, runs it
against the tests to fill in expected outputs, and writes
src/data/blueprints.ts.

Run:  python3 scripts/blueprints.py
"""
import copy, json, pathlib, re, textwrap

# Idioms are the reusable Python phrases a step needs. When you open a hint for
# a step, the app counts its idioms so you can drill the ones you keep needing.
IDIOMS = {
    'set-add': ('Make a set and add to it', 'seen = set()\nseen.add(x)'),
    'in-check': ('Membership test with in', 'if x in seen:'),
    'dict-get': ('Count with dict.get', 'count[x] = count.get(x, 0) + 1'),
    'counter': ('Counter from collections', 'from collections import Counter\ncount = Counter(nums)'),
    'defaultdict': ('defaultdict(list) for grouping', 'from collections import defaultdict\ngroups = defaultdict(list)'),
    'tuple-key': ('Tuple as a dict key', 'key = tuple(sorted(word))'),
    'enumerate': ('Index and value with enumerate', 'for i, x in enumerate(nums):'),
    'items': ('Loop over key and value with .items()', 'for key, value in d.items():'),
    'list-of-lists': ('A list of separate empty lists', 'buckets = [[] for _ in range(n + 1)]'),
    'range-back': ('Count down with range', 'for i in range(len(a) - 1, -1, -1):'),
    'two-pointers': ('Two pointers from both ends', 'l, r = 0, len(a) - 1\nwhile l < r:'),
    'str-methods': ('Character checks', 'ch.isalnum()\nch.lower()'),
    'stack': ('List as a stack', 'stack.append(x)\nstack.pop()\nstack[-1]'),
    'heapq': ('heapq push and pop', 'import heapq\nheapq.heappush(h, x)\nheapq.heappop(h)'),
    'deque': ('deque for BFS', 'from collections import deque\nq = deque([start])\nq.popleft()'),
    'max-min': ('Track a running best with max or min', 'best = max(best, value)'),
    'infinity': ('Start from infinity', "lowest = float('inf')"),
    'multi-assign': ('Swap or update several names at once', 'a, b = b, a + b'),
    'recursion': ('Base case first in recursion', 'if not node:\n    return 0'),
    'slicing': ('Slices and copies', 'path[:]\nnums[1:]'),
    'sort': ('sorted() and .sort()', 'nums.sort()\nsorted(words)'),
    'grid-bounds': ('Grid bounds check', 'if 0 <= r < rows and 0 <= c < cols:'),
    'floor-div': ('Integer division and ceiling', 'mid = (lo + hi) // 2\nmath.ceil(p / k)'),
    'list-mult': ('A list of zeros or ones', 'dp = [0] * (n + 1)'),
}

P = []
def B(id, title, nc, difficulty, pattern, statement, example, signature, steps, tests, postlude='', check=None, want=None):
    """steps: list of (text, clue, template, code, idioms). code/template are function-body lines (no leading indent)."""
    P.append(dict(id=id, title=title, nc=nc, difficulty=difficulty, pattern=pattern, statement=statement, example=example,
                  signature=signature, steps=[dict(text=t, clue=c, template=tm.strip('\n'), code=cd.strip('\n'), idioms=i) for t, c, tm, cd, i in steps],
                  tests=tests, postlude=textwrap.dedent(postlude).strip('\n'), check=check, want=want))

# ───────────────────────── Arrays & Hashing ─────────────────────────
B('bp-contains-dup', 'Contains Duplicate', 'duplicate-integer', 'easy', 'hashing',
  'Return True if any value appears at least twice in nums.', '[1, 2, 3, 1] → True', 'def contains_duplicate(nums):', [
  ('Make an empty set to remember numbers you have seen', 'A set gives O(1) "have I seen this?" checks. Create it with set(), not {} (that is a dict).',
   'seen = ____()', 'seen = set()', ['set-add']),
  ('Walk through each number', 'A plain for loop over the list.', 'for ____ in ____:', 'for n in nums:', []),
  ('If it is already in the set, you found a duplicate', 'Use the in keyword, then return True. Indent this inside the loop.', '    if n ____ seen:\n        return ____', '    if n in seen:\n        return True', ['in-check']),
  ('Otherwise add it, and return False after the loop', 'Sets use .add(), not .append(). The final return goes after the loop, not inside it.', '    seen.____(n)\nreturn ____', '    seen.add(n)\nreturn False', ['set-add']),
], [[[1, 2, 3, 1]], [[1, 2, 3, 4]], [[]], [[5, 5]]])

B('bp-valid-anagram', 'Valid Anagram', 'is-anagram', 'easy', 'hashing',
  'Return True if t is a rearrangement of the letters in s.', 's = "anagram", t = "nagaram" → True', 'def is_anagram(s, t):', [
  ('Different lengths can never be anagrams', 'Compare len() of both strings and return early.', 'if ____(s) != ____(t):\n    return ____', 'if len(s) != len(t):\n    return False', []),
  ('Make one dict to count letters', 'An empty dict is {}.', 'count = ____', 'count = {}', []),
  ('Add 1 for each letter of s and subtract 1 for each letter of t', 'dict.get(key, 0) returns 0 when the key is missing, so you never get a KeyError.', 'for a, b in zip(s, t):\n    count[a] = count.____(a, 0) + 1\n    count[b] = count.get(b, ____) - 1', 'for a, b in zip(s, t):\n    count[a] = count.get(a, 0) + 1\n    count[b] = count.get(b, 0) - 1', ['dict-get']),
  ('They are anagrams only if every count is back to zero', 'all() is True when every item is truthy. Check each value with .values().', 'return all(v == 0 for v in count.____())', 'return all(v == 0 for v in count.values())', ['items']),
], [['anagram', 'nagaram'], ['rat', 'car'], ['a', 'ab'], ['', ''], ['aacc', 'ccac']])

B('bp-two-sum', 'Two Sum', 'two-integer-sum', 'easy', 'hashing',
  'Return the indices [i, j] of the two numbers that add up to target. Exactly one answer exists.', 'nums = [2, 7, 11, 15], target = 9 → [0, 1]', 'def two_sum(nums, target):', [
  ('Make a dict from number to its index', 'Keys are the numbers you have seen, values are their positions.', 'seen = ____', 'seen = {}', []),
  ('Loop with both the index and the number', 'enumerate gives you (index, value) pairs.', 'for i, n in ____(nums):', 'for i, n in enumerate(nums):', ['enumerate']),
  ('If the partner (target minus n) was seen, return both indices', 'The partner is target - n. Look it up with in, then return [its index, i].', '    if target - n ____ seen:\n        return [seen[____], i]', '    if target - n in seen:\n        return [seen[target - n], i]', ['in-check']),
  ('Otherwise remember this number and its index', 'Store it AFTER checking, so a number never pairs with itself.', '    seen[____] = ____', '    seen[n] = i', []),
], [[[2, 7, 11, 15], 9], [[3, 2, 4], 6], [[3, 3], 6], [[-1, -2, -3, -4, -5], -8]])

B('bp-group-anagrams', 'Group Anagrams', 'anagram-groups', 'medium', 'hashing',
  'Group words that are anagrams of each other. Return the groups in any order.', '["eat","tea","tan","ate","nat","bat"] → [["eat","tea","ate"],["tan","nat"],["bat"]]', 'def group_anagrams(strs):', [
  ('Make a dict where each new key starts as an empty list', 'defaultdict(list) creates the empty list for you the first time a key is used. Import it from collections.', 'from collections import ____\ngroups = defaultdict(____)', 'from collections import defaultdict\ngroups = defaultdict(list)', ['defaultdict']),
  ('Loop over every word', 'A plain for loop.', 'for word in ____:', 'for word in strs:', []),
  ('Build a key that all anagrams share and add the word to that group', 'Sorting the letters gives the same result for anagrams. Lists cannot be dict keys, so wrap it in tuple().', '    key = ____(sorted(word))\n    groups[key].____(word)', '    key = tuple(sorted(word))\n    groups[key].append(word)', ['tuple-key', 'sort']),
  ('Return just the groups', 'You want the dict values, as a list.', 'return list(groups.____())', 'return list(groups.values())', ['items']),
], [[['eat', 'tea', 'tan', 'ate', 'nat', 'bat']], [['']], [['a']], [['ab', 'ba', 'abc']]],
  postlude='''
  def _check(strs):
      return sorted(sorted(g) for g in group_anagrams(strs))
  ''', check='_check')

B('bp-top-k', 'Top K Frequent Elements', 'top-k-elements-in-list', 'medium', 'top-k',
  'Return the k most frequent numbers in any order, in O(N) time using bucket sort.', 'nums = [1,1,1,2,2,3], k = 2 → [1, 2]', 'def top_k_frequent(nums, k):', [
  ('Set up a count dict and empty frequency buckets, one per possible count from 0 to len(nums)', 'Each bucket must be its own list: use a list comprehension. [[]] * n would make every bucket the same list.', 'count = {}\nfreq = [[] for _ in ____(len(nums) + 1)]', 'count = {}\nfreq = [[] for _ in range(len(nums) + 1)]', ['list-of-lists']),
  ('Count how many times each number appears', 'count.get(n, 0) + 1 starts missing numbers at 0.', 'for n in nums:\n    count[n] = count.____(n, ____) + 1', 'for n in nums:\n    count[n] = count.get(n, 0) + 1', ['dict-get']),
  ('Drop each number into the bucket for its count', 'Loop over the dict with .items() to get number and count together, then append the number to freq[count].', 'for n, c in count.____():\n    freq[____].append(n)', 'for n, c in count.items():\n    freq[c].append(n)', ['items']),
  ('Walk the buckets backward from the highest count, collecting numbers until you have k', 'range(start, stop, -1) counts down. Stop is exclusive, so use 0 to stop after bucket 1.', 'res = []\nfor i in range(len(freq) - 1, ____, -1):\n    for n in freq[i]:\n        res.append(n)\n        if len(res) == ____:\n            return res', 'res = []\nfor i in range(len(freq) - 1, 0, -1):\n    for n in freq[i]:\n        res.append(n)\n        if len(res) == k:\n            return res', ['range-back']),
], [[[1, 1, 1, 2, 2, 3], 2], [[1], 1], [[4, 4, 5, 5, 5, 6], 1], [[1, 2, 2, 3, 3, 3], 3]],
  postlude='''
  def _check(nums, k):
      return sorted(top_k_frequent(nums, k))
  ''', check='_check')

B('bp-product-except', 'Product of Array Except Self', 'products-of-array-discluding-self', 'medium', 'prefix-sum',
  'Return a list where res[i] is the product of every number except nums[i], without division.', '[1, 2, 3, 4] → [24, 12, 8, 6]', 'def product_except_self(nums):', [
  ('Start the result as a list of ones, one per number', 'Multiplying a single-item list makes copies: [1] * n.', 'res = [____] * len(nums)', 'res = [1] * len(nums)', ['list-mult']),
  ('Left pass: store the product of everything before each index', 'Keep a running product. Write it into res[i] first, then multiply in nums[i].', 'prefix = 1\nfor i in range(len(nums)):\n    res[i] = ____\n    prefix *= nums[____]', 'prefix = 1\nfor i in range(len(nums)):\n    res[i] = prefix\n    prefix *= nums[i]', []),
  ('Right pass: multiply in the product of everything after each index', 'Walk backward with range(len(nums) - 1, -1, -1). The stop is -1 so index 0 is included.', 'suffix = 1\nfor i in range(len(nums) - 1, ____, -1):\n    res[i] *= ____\n    suffix *= nums[i]', 'suffix = 1\nfor i in range(len(nums) - 1, -1, -1):\n    res[i] *= suffix\n    suffix *= nums[i]', ['range-back']),
  ('Return the result', 'Just return the list.', 'return ____', 'return res', []),
], [[[1, 2, 3, 4]], [[-1, 0, 1, 2, 3]], [[2, 3]], [[0, 0]]])

B('bp-valid-sudoku', 'Valid Sudoku', 'valid-sudoku', 'medium', 'hashing',
  'A 9x9 board holds digits as strings and "." for empty. Return True if no row, column or 3x3 box repeats a digit.', 'a standard partly filled board → True', 'def is_valid_sudoku(board):', [
  ('Make a set of seen digits for every row, every column and every 3x3 box', 'Use defaultdict(set) so each new key starts as an empty set.', 'from collections import defaultdict\nrows, cols, boxes = defaultdict(____), defaultdict(set), defaultdict(set)', 'from collections import defaultdict\nrows, cols, boxes = defaultdict(set), defaultdict(set), defaultdict(set)', ['defaultdict']),
  ('Visit every cell and skip empty ones', 'Two nested range(9) loops. continue skips to the next cell.', 'for r in range(9):\n    for c in range(____):\n        v = board[r][c]\n        if v == ".":\n            ____', 'for r in range(9):\n    for c in range(9):\n        v = board[r][c]\n        if v == ".":\n            continue', []),
  ('If the digit is already in its row, column or box, the board is invalid', 'The box id is (r // 3, c // 3). Integer division groups 0 to 2 as box 0, and so on.', '        box = (r // ____, c // 3)\n        if v in rows[r] or v in cols[c] or v in boxes[____]:\n            return False', '        box = (r // 3, c // 3)\n        if v in rows[r] or v in cols[c] or v in boxes[box]:\n            return False', ['in-check', 'floor-div']),
  ('Record the digit in all three, and return True after the loops', 'Sets use .add().', '        rows[r].____(v)\n        cols[c].add(v)\n        boxes[box].add(v)\nreturn True', '        rows[r].add(v)\n        cols[c].add(v)\n        boxes[box].add(v)\nreturn True', ['set-add']),
], [[[list("53..7...."), list("6..195..."), list(".98....6."), list("8...6...3"), list("4..8.3..1"), list("7...2...6"), list(".6....28."), list("...419..5"), list("....8..79")]],
    [[list("83..7...."), list("6..195..."), list(".98....6."), list("8...6...3"), list("4..8.3..1"), list("7...2...6"), list(".6....28."), list("...419..5"), list("....8..79")]],
    [[list("........."), list("........."), list("........."), list("........."), list("........."), list("........."), list("........."), list("........."), list("......1.1")]]])

B('bp-longest-consecutive', 'Longest Consecutive Sequence', 'longest-consecutive-sequence', 'medium', 'hashing',
  'Return the length of the longest run of consecutive values (they can be anywhere in the array), in O(N).', '[100, 4, 200, 1, 3, 2] → 4', 'def longest_consecutive(nums):', [
  ('Put every number in a set and start the best length at 0', 'set(nums) builds it in one go.', 'num_set = ____(nums)\nbest = 0', 'num_set = set(nums)\nbest = 0', ['set-add']),
  ('Only start counting at numbers where n - 1 is NOT in the set (the start of a run)', 'not in is the opposite of in.', 'for n in num_set:\n    if n - 1 ____ ____ num_set:', 'for n in num_set:\n    if n - 1 not in num_set:', ['in-check']),
  ('From that start, count upward while the next number exists', 'A while loop that keeps checking n + length.', '        length = 1\n        while n + length ____ num_set:\n            length += ____', '        length = 1\n        while n + length in num_set:\n            length += 1', ['in-check']),
  ('Keep the longest run, and return it after the loop', 'max(a, b) keeps the bigger one.', '        best = ____(best, length)\nreturn best', '        best = max(best, length)\nreturn best', ['max-min']),
], [[[100, 4, 200, 1, 3, 2]], [[0, 3, 7, 2, 5, 8, 4, 6, 0, 1]], [[]], [[1, 2, 0, 1]]])

# ───────────────────────── Two pointers ─────────────────────────
B('bp-valid-palindrome', 'Valid Palindrome', 'is-palindrome', 'easy', 'two-pointers',
  'Ignoring case and anything that is not a letter or digit, return True if s reads the same both ways.', '"A man, a plan, a canal: Panama" → True', 'def is_palindrome(s):', [
  ('Put one pointer at the start and one at the end', 'Assign both on one line.', 'l, r = 0, ____(s) - 1', 'l, r = 0, len(s) - 1', ['two-pointers']),
  ('Loop while the pointers have not crossed, skipping characters that are not letters or digits', 'str.isalnum() is True for letters and digits. Also check l < r inside the inner loops.', 'while l < r:\n    while l < r and not s[l].____():\n        l += 1\n    while l < r and not s[r].isalnum():\n        r -= ____', 'while l < r:\n    while l < r and not s[l].isalnum():\n        l += 1\n    while l < r and not s[r].isalnum():\n        r -= 1', ['str-methods']),
  ('Compare the two characters ignoring case', '.lower() on both sides.', '    if s[l].____() != s[r].lower():\n        return False', '    if s[l].lower() != s[r].lower():\n        return False', ['str-methods']),
  ('Move both pointers inward, and return True after the loop', 'Update both on one line.', '    l, r = l + 1, r ____ 1\nreturn True', '    l, r = l + 1, r - 1\nreturn True', ['multi-assign']),
], [['A man, a plan, a canal: Panama'], ['race a car'], [' '], ['0P'], ['ab_a']])

B('bp-two-sum-sorted', 'Two Sum II (sorted input)', 'two-integer-sum-ii', 'medium', 'two-pointers',
  'numbers is sorted ascending. Return the 1-based positions of the two numbers that add to target, using O(1) extra space.', 'numbers = [2, 7, 11, 15], target = 9 → [1, 2]', 'def two_sum_sorted(numbers, target):', [
  ('Point at both ends', 'Left at 0, right at the last index.', 'l, r = 0, len(numbers) - ____', 'l, r = 0, len(numbers) - 1', ['two-pointers']),
  ('Loop while left is before right and add the two values', 'A while loop, not a for loop, because both ends move.', '____ l < r:\n    s = numbers[l] + numbers[____]', 'while l < r:\n    s = numbers[l] + numbers[r]', ['two-pointers']),
  ('If the sum matches, return 1-based positions', 'Add 1 to each index.', '    if s == target:\n        return [l + ____, r + 1]', '    if s == target:\n        return [l + 1, r + 1]', []),
  ('Too small means move left up, too big means move right down', 'elif and else, not else if.', '    ____ s < target:\n        l += 1\n    else:\n        r ____ 1', '    elif s < target:\n        l += 1\n    else:\n        r -= 1', []),
], [[[2, 7, 11, 15], 9], [[2, 3, 4], 6], [[-1, 0], -1], [[1, 2, 3, 4, 4, 9, 56, 90], 8]])

B('bp-3sum', '3Sum', 'three-integer-sum', 'medium', 'two-pointers',
  'Return all unique triplets that sum to 0.', '[-1, 0, 1, 2, -1, -4] → [[-1,-1,2],[-1,0,1]]', 'def three_sum(nums):', [
  ('Sort the numbers and make the result list', '.sort() sorts in place and returns None, so do not assign it.', 'nums.____()\nres = []', 'nums.sort()\nres = []', ['sort']),
  ('Fix each number as the first of the triplet, skipping repeats of the previous one', 'i > 0 and nums[i] == nums[i - 1] means a duplicate anchor.', 'for i in range(len(nums)):\n    if i > 0 and nums[i] == nums[i - ____]:\n        continue\n    l, r = i + 1, len(nums) - 1', 'for i in range(len(nums)):\n    if i > 0 and nums[i] == nums[i - 1]:\n        continue\n    l, r = i + 1, len(nums) - 1', ['two-pointers']),
  ('Run two pointers on the rest, moving toward a total of zero', 'Too small: l += 1. Too big: r -= 1.', '    while l < r:\n        total = nums[i] + nums[l] + nums[r]\n        if total < 0:\n            l += 1\n        elif total > ____:\n            r -= 1', '    while l < r:\n        total = nums[i] + nums[l] + nums[r]\n        if total < 0:\n            l += 1\n        elif total > 0:\n            r -= 1', ['two-pointers']),
  ('On a match, save it, move left past duplicates, and return the list at the end', 'Append a list of three values. Then step l forward while it equals the previous value.', '        else:\n            res.append([nums[i], nums[l], nums[____]])\n            l += 1\n            while l < r and nums[l] == nums[l - 1]:\n                l += 1\nreturn ____', '        else:\n            res.append([nums[i], nums[l], nums[r]])\n            l += 1\n            while l < r and nums[l] == nums[l - 1]:\n                l += 1\nreturn res', []),
], [[[-1, 0, 1, 2, -1, -4]], [[0, 1, 1]], [[0, 0, 0, 0]], [[-2, 0, 1, 1, 2]]],
  postlude='''
  def _check(nums):
      return sorted(three_sum(nums))
  ''', check='_check')

B('bp-container', 'Container With Most Water', 'max-water-container', 'medium', 'two-pointers',
  'Pick two lines that hold the most water: width times the shorter height.', '[1,8,6,2,5,4,8,3,7] → 49', 'def max_area(height):', [
  ('Point at both ends and start the best at 0', 'Three names on one line works too.', 'l, r = 0, len(height) - 1\nbest = ____', 'l, r = 0, len(height) - 1\nbest = 0', ['two-pointers']),
  ('While the pointers have not met, compute the water between them', 'Width is r - l. Height is the shorter of the two: min().', 'while l < r:\n    area = (r - l) * ____(height[l], height[r])', 'while l < r:\n    area = (r - l) * min(height[l], height[r])', ['max-min']),
  ('Keep the best area', 'max() keeps the bigger value.', '    best = ____(best, area)', '    best = max(best, area)', ['max-min']),
  ('Move the shorter side inward, and return the best after the loop', 'The shorter line limits the water, so it is the only one worth moving.', '    if height[l] < height[r]:\n        l += 1\n    else:\n        r ____ 1\nreturn best', '    if height[l] < height[r]:\n        l += 1\n    else:\n        r -= 1\nreturn best', []),
], [[[1, 8, 6, 2, 5, 4, 8, 3, 7]], [[1, 1]], [[4, 3, 2, 1, 4]], [[1, 2, 1]]])

# ───────────────────────── Sliding window ─────────────────────────
B('bp-buy-sell', 'Best Time to Buy and Sell Stock', 'buy-and-sell-crypto', 'easy', 'sliding-window',
  'Buy once and sell later. Return the maximum profit, or 0.', '[7, 1, 5, 3, 6, 4] → 5', 'def max_profit(prices):', [
  ('Start the lowest price at infinity and the best profit at 0', "float('inf') is bigger than any number, so the first price always replaces it.", "lowest = float('____')\nbest = 0", "lowest = float('inf')\nbest = 0", ['infinity']),
  ('Walk through each price', 'A plain for loop.', 'for p in ____:', 'for p in prices:', []),
  ('Update the lowest price seen so far', 'min() keeps the smaller value.', '    lowest = ____(lowest, p)', '    lowest = min(lowest, p)', ['max-min']),
  ('Update the best profit if you sold today, and return it after the loop', 'Profit today is p - lowest.', '    best = max(best, p - ____)\nreturn best', '    best = max(best, p - lowest)\nreturn best', ['max-min']),
], [[[7, 1, 5, 3, 6, 4]], [[7, 6, 4, 3, 1]], [[1]], [[2, 4, 1, 7]]])

B('bp-longest-substring', 'Longest Substring Without Repeating Characters', 'longest-substring-without-duplicates', 'medium', 'sliding-window',
  'Return the length of the longest substring with no repeated characters.', '"abcabcbb" → 3', 'def length_of_longest_substring(s):', [
  ('Make a set for the window, a left edge at 0, and best at 0', 'Three setup lines.', 'window = ____()\nl = 0\nbest = 0', 'window = set()\nl = 0\nbest = 0', ['set-add']),
  ('Move the right edge across the string', 'range(len(s)) gives each index.', 'for r in ____(len(s)):', 'for r in range(len(s)):', []),
  ('While the new character is already in the window, remove from the left and move left forward', 'set.remove(x) deletes x. This is a while, not an if, because you may need to remove several.', '    while s[r] in window:\n        window.____(s[l])\n        l += 1', '    while s[r] in window:\n        window.remove(s[l])\n        l += 1', ['in-check']),
  ('Add the new character, record the window size, and return the best', 'Window size is r - l + 1.', '    window.add(s[r])\n    best = max(best, r - l + ____)\nreturn best', '    window.add(s[r])\n    best = max(best, r - l + 1)\nreturn best', ['set-add', 'max-min']),
], [['abcabcbb'], ['bbbbb'], ['pwwkew'], [''], ['abba']])

# ───────────────────────── Stack ─────────────────────────
B('bp-valid-parens', 'Valid Parentheses', 'validate-parentheses', 'easy', 'monotonic-stack',
  'Return True if every bracket is closed by the matching type in the right order.', '"([]{})" → True, "(]" → False', 'def is_valid(s):', [
  ('Map each closing bracket to its opening bracket, and make an empty stack', 'A dict literal with three pairs, and an empty list for the stack.', 'pairs = {")": "(", "]": "____", "}": "{"}\nstack = ____', 'pairs = {")": "(", "]": "[", "}": "{"}\nstack = []', ['stack']),
  ('Loop over the characters, pushing opening brackets', 'Opening brackets are the dict values. Push with .append().', 'for ch in s:\n    if ch not in pairs:\n        stack.____(ch)', 'for ch in s:\n    if ch not in pairs:\n        stack.append(ch)', ['stack', 'in-check']),
  ('For a closing bracket, the top of the stack must be its partner', 'Check the stack is not empty first, then compare stack.pop() with pairs[ch].', '    elif not stack or stack.____() != pairs[ch]:\n        return False', '    elif not stack or stack.pop() != pairs[ch]:\n        return False', ['stack']),
  ('At the end it is valid only if nothing is left open', 'An empty list is falsy, so not stack is True when it is empty.', 'return ____ stack', 'return not stack', []),
], [['()[]{}'], ['(]'], ['(('], ['{[()]}'], [')']])

B('bp-daily-temps', 'Daily Temperatures', 'daily-temperatures', 'medium', 'monotonic-stack',
  'For each day, return how many days until a warmer one, or 0.', '[73,74,75,71,69,72,76,73] → [1,1,4,2,1,1,0,0]', 'def daily_temperatures(temps):', [
  ('Answer starts as zeros, and the stack will hold indices of days still waiting', '[0] * n makes n zeros.', 'res = [____] * len(temps)\nstack = []', 'res = [0] * len(temps)\nstack = []', ['list-mult', 'stack']),
  ('Loop with index and temperature', 'enumerate gives both.', 'for i, t in ____(temps):', 'for i, t in enumerate(temps):', ['enumerate']),
  ('While today is warmer than the day on top of the stack, that day found its answer', 'stack[-1] peeks at the top. Pop it, then store the distance i - j.', '    while stack and t > temps[stack[____]]:\n        j = stack.pop()\n        res[j] = i - ____', '    while stack and t > temps[stack[-1]]:\n        j = stack.pop()\n        res[j] = i - j', ['stack']),
  ('Push today, and return the answers after the loop', 'Push the index, not the temperature.', '    stack.append(____)\nreturn res', '    stack.append(i)\nreturn res', ['stack']),
], [[[73, 74, 75, 71, 69, 72, 76, 73]], [[30, 40, 50, 60]], [[30, 60, 90]], [[90, 80]]])

# ───────────────────────── Binary search ─────────────────────────
B('bp-binary-search', 'Binary Search', 'binary-search', 'easy', 'binary-search',
  'Return the index of target in sorted nums, or -1.', 'nums = [-1,0,3,5,9,12], target = 9 → 4', 'def search(nums, target):', [
  ('Set the search range to the whole list', 'hi is the last index, so the range is inclusive.', 'lo, hi = 0, len(nums) - ____', 'lo, hi = 0, len(nums) - 1', []),
  ('Loop while the range is not empty and look at the middle', 'With an inclusive hi, the condition is lo <= hi. Use // for integer division.', 'while lo <= hi:\n    mid = (lo + hi) ____ 2', 'while lo <= hi:\n    mid = (lo + hi) // 2', ['floor-div']),
  ('Return mid if it matches, otherwise throw away the half that cannot hold the target', 'If nums[mid] is too small, the target is to the right: lo = mid + 1.', '    if nums[mid] == target:\n        return mid\n    elif nums[mid] < target:\n        lo = mid + ____\n    else:\n        hi = mid - 1', '    if nums[mid] == target:\n        return mid\n    elif nums[mid] < target:\n        lo = mid + 1\n    else:\n        hi = mid - 1', []),
  ('If the loop ends, the target is not there', 'Return after the loop.', 'return ____', 'return -1', []),
], [[[-1, 0, 3, 5, 9, 12], 9], [[-1, 0, 3, 5, 9, 12], 2], [[5], 5], [[1, 3], 3], [[1, 3, 5, 7], 8], [[1, 3, 5, 7], 1], [[2], 1]])

B('bp-koko', 'Koko Eating Bananas', 'eating-bananas', 'medium', 'binary-search',
  'Return the slowest integer speed k (bananas per hour, one pile per hour) that finishes all piles within h hours.', 'piles = [3, 6, 7, 11], h = 8 → 4', 'def min_eating_speed(piles, h):', [
  ('Import math and set the speed range from 1 to the biggest pile', 'max(piles) is the fastest speed you would ever need.', 'import math\nlo, hi = 1, ____(piles)', 'import math\nlo, hi = 1, max(piles)', ['max-min']),
  ('Binary search while lo is below hi', 'This version searches for the first speed that works, so the condition is lo < hi.', 'while lo ____ hi:\n    k = (lo + hi) // 2', 'while lo < hi:\n    k = (lo + hi) // 2', ['floor-div']),
  ('Count the hours at speed k', 'Each pile takes ceil(p / k) hours. sum() over a generator adds them.', '    hours = sum(math.____(p / k) for p in piles)', '    hours = sum(math.ceil(p / k) for p in piles)', ['floor-div']),
  ('If it fits, try slower (hi = k), otherwise go faster, and return lo at the end', 'Fits means hours <= h. When it does not fit, lo = k + 1.', '    if hours <= h:\n        hi = ____\n    else:\n        lo = k + 1\nreturn lo', '    if hours <= h:\n        hi = k\n    else:\n        lo = k + 1\nreturn lo', []),
], [[[3, 6, 7, 11], 8], [[30, 11, 23, 4, 20], 5], [[30, 11, 23, 4, 20], 6], [[1], 1]])

# ───────────────────────── Linked list and trees (helpers are added for you) ─────────────────────────
LL = '''
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def _to_list(head):
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out

def _build(vals):
    dummy = ListNode()
    cur = dummy
    for v in vals:
        cur.next = ListNode(v)
        cur = cur.next
    return dummy.next
'''
TREE = '''
from collections import deque as _dq

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def _tree(vals):
    if not vals:
        return None
    root = TreeNode(vals[0])
    q = _dq([root])
    i = 1
    while q and i < len(vals):
        node = q.popleft()
        if i < len(vals) and vals[i] is not None:
            node.left = TreeNode(vals[i]); q.append(node.left)
        i += 1
        if i < len(vals) and vals[i] is not None:
            node.right = TreeNode(vals[i]); q.append(node.right)
        i += 1
    return root

def _level(root):
    out, q = [], _dq([root] if root else [])
    while q:
        n = q.popleft()
        out.append(n.val)
        if n.left: q.append(n.left)
        if n.right: q.append(n.right)
    return out
'''

B('bp-reverse-list', 'Reverse Linked List', 'reverse-a-linked-list', 'easy', 'reverse-ll',
  'Reverse a singly linked list and return the new head. ListNode has .val and .next.', '1 → 2 → 3 → None becomes 3 → 2 → 1 → None', 'def reverse_list(head):', [
  ('Start with prev as None and cur at the head', 'Two names on one line.', 'prev, cur = ____, head', 'prev, cur = None, head', ['multi-assign']),
  ('Loop while there is a current node and save the next node first', 'If you flip before saving, you lose the rest of the list.', 'while cur:\n    nxt = cur.____', 'while cur:\n    nxt = cur.next', []),
  ('Point the current node back at prev, then step both forward', 'Flip with cur.next = prev, then move prev and cur.', '    cur.next = ____\n    prev, cur = cur, nxt', '    cur.next = prev\n    prev, cur = cur, nxt', ['multi-assign']),
  ('prev is the new head', 'cur is None when the loop ends.', 'return ____', 'return prev', []),
], [[[1, 2, 3, 4, 5]], [[1, 2]], [[]]],
  postlude=LL + '''
def _check(vals):
    return _to_list(reverse_list(_build(vals)))
''', check='_check')

B('bp-invert-tree', 'Invert Binary Tree', 'invert-a-binary-tree', 'easy', 'tree-traversal',
  'Mirror a binary tree (swap every left and right child) and return its root. TreeNode has .val, .left and .right.', '[4,2,7,1,3,6,9] → [4,7,2,9,6,3,1] (level order)', 'def invert_tree(root):', [
  ('Base case: an empty tree stays empty', 'Check for None with not root.', 'if ____ root:\n    return None', 'if not root:\n    return None', ['recursion']),
  ('Swap the left and right children', 'Tuple assignment swaps without a temp variable.', 'root.left, root.right = root.____, root.left', 'root.left, root.right = root.right, root.left', ['multi-assign']),
  ('Invert both subtrees', 'Call the same function on each child.', 'invert_tree(root.____)\ninvert_tree(root.right)', 'invert_tree(root.left)\ninvert_tree(root.right)', ['recursion']),
  ('Return the root', 'The same node, now mirrored.', 'return ____', 'return root', []),
], [[[4, 2, 7, 1, 3, 6, 9]], [[2, 1, 3]], [[]]],
  postlude=TREE + '''
def _check(vals):
    return _level(invert_tree(_tree(vals)))
''', check='_check')

B('bp-max-depth', 'Maximum Depth of Binary Tree', 'depth-of-binary-tree', 'easy', 'tree-traversal',
  'Return the number of nodes on the longest path from the root down to a leaf.', '[3,9,20,null,null,15,7] → 3', 'def max_depth(root):', [
  ('Base case: an empty tree has depth 0', 'Return 0 for None.', 'if not root:\n    return ____', 'if not root:\n    return 0', ['recursion']),
  ('Get the depth of the left subtree', 'Recursive call on root.left.', 'left = max_depth(root.____)', 'left = max_depth(root.left)', ['recursion']),
  ('Get the depth of the right subtree', 'Same for the right.', 'right = ____(root.right)', 'right = max_depth(root.right)', ['recursion']),
  ('This node adds 1 to the deeper side', 'max() of the two, plus one.', 'return 1 + ____(left, right)', 'return 1 + max(left, right)', ['max-min']),
], [[[3, 9, 20, None, None, 15, 7]], [[1, None, 2]], [[]]],
  postlude=TREE + '''
def _check(vals):
    return max_depth(_tree(vals))
''', check='_check')

# ───────────────────────── Graphs ─────────────────────────
B('bp-islands', 'Number of Islands', 'count-number-of-islands', 'medium', 'matrix',
  'Count groups of "1" cells connected up, down, left or right.', '[["1","1","0"],["0","1","0"],["0","0","1"]] → 2', 'def num_islands(grid):', [
  ('Save the grid size and start the count at 0', 'rows is len(grid), cols is len(grid[0]).', 'rows, cols = len(grid), len(grid[____])\ncount = 0', 'rows, cols = len(grid), len(grid[0])\ncount = 0', []),
  ('Write a helper that sinks one island: stop if out of bounds or not land, otherwise mark it and visit the 4 neighbors', 'Check bounds first, then the value. Marking "0" means you never count it twice.', 'def sink(r, c):\n    if r < 0 or c < 0 or r >= rows or c >= ____ or grid[r][c] != "1":\n        return\n    grid[r][c] = "0"\n    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):\n        sink(r + dr, c + ____)', 'def sink(r, c):\n    if r < 0 or c < 0 or r >= rows or c >= cols or grid[r][c] != "1":\n        return\n    grid[r][c] = "0"\n    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):\n        sink(r + dr, c + dc)', ['grid-bounds', 'recursion']),
  ('Scan every cell, and every time you hit land count an island and sink it', 'Two nested loops over range(rows) and range(cols).', 'for r in range(rows):\n    for c in range(____):\n        if grid[r][c] == "1":\n            count += 1\n            sink(r, c)', 'for r in range(rows):\n    for c in range(cols):\n        if grid[r][c] == "1":\n            count += 1\n            sink(r, c)', []),
  ('Return the count', 'After the loops.', 'return ____', 'return count', []),
], [[[['1', '1', '0'], ['0', '1', '0'], ['0', '0', '1']]], [[['1', '1', '1', '1', '0'], ['1', '1', '0', '1', '0'], ['1', '1', '0', '0', '0'], ['0', '0', '0', '0', '0']]], [[['0']]]])

# ───────────────────────── DP ─────────────────────────
B('bp-climbing', 'Climbing Stairs', 'climbing-stairs', 'easy', 'dp',
  'You climb 1 or 2 steps at a time. How many ways reach step n?', 'n = 3 → 3', 'def climb_stairs(n):', [
  ('Ways to reach the two previous steps start at 1 and 1', 'one and two hold the answers for the last two steps.', 'one, two = 1, ____', 'one, two = 1, 1', ['multi-assign']),
  ('Repeat n - 1 times', 'range(n - 1) runs that many times. _ means you do not need the loop number.', 'for _ in range(n - ____):', 'for _ in range(n - 1):', []),
  ('The new answer is the sum of the last two, then shift', 'Update both at once so you do not lose the old value.', '    one, two = one + two, ____', '    one, two = one + two, one', ['multi-assign']),
  ('Return the latest answer', 'one holds it.', 'return ____', 'return one', []),
], [[2], [3], [5], [1], [10]])

B('bp-house-robber', 'House Robber', 'house-robber', 'medium', 'dp',
  'You cannot rob two adjacent houses. Return the most money you can rob.', '[2, 7, 9, 3, 1] → 12', 'def rob(nums):', [
  ('Best totals for two houses back and one house back both start at 0', 'Two variables on one line.', 'prev2, prev1 = 0, ____', 'prev2, prev1 = 0, 0', ['multi-assign']),
  ('Walk through each house', 'A plain for loop.', 'for x in ____:', 'for x in nums:', []),
  ('Either skip this house (prev1) or rob it (prev2 + x), keep the better, and shift', 'max() of the two choices. Update both names together.', '    prev2, prev1 = prev1, ____(prev1, prev2 + x)', '    prev2, prev1 = prev1, max(prev1, prev2 + x)', ['multi-assign', 'max-min']),
  ('Return the best total', 'prev1 holds it after the loop.', 'return ____', 'return prev1', []),
], [[[1, 2, 3, 1]], [[2, 7, 9, 3, 1]], [[]], [[5]]])

B('bp-coin-change', 'Coin Change', 'coin-change', 'medium', 'dp',
  'Return the fewest coins that make amount, or -1 if impossible.', 'coins = [1, 2, 5], amount = 11 → 3', 'def coin_change(coins, amount):', [
  ('dp[a] = fewest coins for amount a. Start dp[0] at 0 and everything else at infinity', "[0] + [float('inf')] * amount builds it.", "dp = [0] + [float('____')] * amount", "dp = [0] + [float('inf')] * amount", ['infinity', 'list-mult']),
  ('Fill amounts from 1 up to amount, trying each coin', 'range(1, amount + 1) includes amount itself.', 'for a in range(1, amount + ____):\n    for c in coins:', 'for a in range(1, amount + 1):\n    for c in coins:', []),
  ('If the coin fits, using it costs dp[a - c] + 1', 'Only use coins no bigger than a, and keep the min.', '        if c <= a:\n            dp[a] = ____(dp[a], dp[a - c] + 1)', '        if c <= a:\n            dp[a] = min(dp[a], dp[a - c] + 1)', ['max-min']),
  ('Return dp[amount], or -1 if it is still infinity', 'A conditional expression: x if cond else y.', "return dp[amount] if dp[amount] != float('inf') ____ -1", "return dp[amount] if dp[amount] != float('inf') else -1", ['infinity']),
], [[[1, 2, 5], 11], [[2], 3], [[1], 0], [[1, 3, 4], 6]])

# ───────────────────────── Heap, intervals, backtracking ─────────────────────────
B('bp-kth-largest', 'Kth Largest Element in an Array', 'kth-largest-element-in-an-array', 'medium', 'top-k',
  'Return the kth largest number without sorting the whole array.', '[3, 2, 1, 5, 6, 4], k = 2 → 5', 'def find_kth_largest(nums, k):', [
  ('Import heapq and make an empty heap', 'heapq works on a plain list.', 'import ____\nheap = []', 'import heapq\nheap = []', ['heapq']),
  ('Push every number onto the heap', 'heapq.heappush(heap, x).', 'for n in nums:\n    heapq.____(heap, n)', 'for n in nums:\n    heapq.heappush(heap, n)', ['heapq']),
  ('If the heap grows past k, pop the smallest', 'heapq is a min-heap, so heappop removes the smallest. That keeps the k largest.', '    if len(heap) > k:\n        heapq.____(heap)', '    if len(heap) > k:\n        heapq.heappop(heap)', ['heapq']),
  ('The smallest of the k largest is the answer', 'heap[0] is always the smallest item.', 'return heap[____]', 'return heap[0]', ['heapq']),
], [[[3, 2, 1, 5, 6, 4], 2], [[3, 2, 3, 1, 2, 4, 5, 5, 6], 4], [[1], 1]])

B('bp-merge-intervals', 'Merge Intervals', 'merge-intervals', 'medium', 'intervals',
  'Merge all overlapping [start, end] intervals.', '[[1,3],[2,6],[8,10]] → [[1,6],[8,10]]', 'def merge(intervals):', [
  ('Sort by start time and make the output list', 'sort with key=lambda x: x[0] sorts by the first value.', 'intervals.sort(key=lambda x: x[____])\nout = []', 'intervals.sort(key=lambda x: x[0])\nout = []', ['sort']),
  ('Loop over each interval, unpacking start and end', 'for s, e in ... unpacks the pair.', 'for s, e in ____:', 'for s, e in intervals:', []),
  ('If it overlaps the last merged interval, extend that end', 'out[-1] is the last one, out[-1][1] its end. Use max so a contained interval never shrinks it.', '    if out and s <= out[-1][1]:\n        out[-1][1] = ____(out[-1][1], e)', '    if out and s <= out[-1][1]:\n        out[-1][1] = max(out[-1][1], e)', ['max-min']),
  ('Otherwise start a new interval, and return the list after the loop', 'Append a new list [s, e].', '    else:\n        out.append([s, ____])\nreturn out', '    else:\n        out.append([s, e])\nreturn out', []),
], [[[[1, 3], [2, 6], [8, 10], [15, 18]]], [[[1, 4], [4, 5]]], [[[1, 4], [0, 4]]], [[[1, 10], [2, 3]]]])

B('bp-subsets', 'Subsets', 'subsets', 'medium', 'backtracking',
  'Return every subset of a list of distinct numbers.', '[1, 2, 3] → 8 subsets', 'def subsets(nums):', [
  ('Make the results list and the current path', 'Two empty lists.', 'res, path = [], ____', 'res, path = [], []', []),
  ('Write a backtrack helper that records a COPY of the path', 'path[:] copies it. Without the copy every entry ends up as the same list.', 'def bt(start):\n    res.append(path[____])', 'def bt(start):\n    res.append(path[:])', ['slicing', 'recursion']),
  ('Try each remaining number: choose it, explore, then un-choose it', 'append, recurse with i + 1, then pop.', '    for i in range(start, len(nums)):\n        path.append(nums[i])\n        bt(i + ____)\n        path.____()', '    for i in range(start, len(nums)):\n        path.append(nums[i])\n        bt(i + 1)\n        path.pop()', ['stack', 'recursion']),
  ('Start the search at index 0 and return the results', 'Call the helper, then return.', 'bt(____)\nreturn res', 'bt(0)\nreturn res', []),
], [[[1, 2, 3]], [[0]], [[]]],
  postlude='''
def _check(nums):
    return sorted(sorted(s) for s in subsets(nums))
''', check='_check')


# ───────────────────────── More NeetCode 150, in roadmap order ─────────────────────────
B('bp-encode-decode', 'Encode and Decode Strings', 'string-encode-and-decode', 'medium', 'hashing',
  'Write encode (a list of strings into one string) and decode (back again). Strings can contain any character, including "#". decode(encode(strs)) must return the original list.', '["neet","code","#love"] round trips unchanged', 'class Codec:', [
  ('encode: put each word\'s length and a "#" in front of it, and join everything', 'f"{len(w)}#{w}" builds one piece. "".join(...) glues the pieces with nothing between.', 'def encode(self, strs):\n    return "".join(f"{____(w)}#{w}" for w in strs)', 'def encode(self, strs):\n    return "".join(f"{len(w)}#{w}" for w in strs)', ['str-methods']),
  ('decode: start a result list and a position at 0', 'A second method.', 'def decode(self, s):\n    res, i = [], ____', 'def decode(self, s):\n    res, i = [], 0', ['multi-assign']),
  ('Read digits up to the next "#" to get the length', 'Move j forward until s[j] is "#". The length is int(s[i:j]).', '    while i < len(s):\n        j = i\n        while s[j] != "____":\n            j += 1\n        length = int(s[i:j])', '    while i < len(s):\n        j = i\n        while s[j] != "#":\n            j += 1\n        length = int(s[i:j])', ['slicing']),
  ('Slice out exactly that many characters, jump past them, and return the list', 'The word starts right after the "#": s[j + 1 : j + 1 + length].', '        res.append(s[j + 1 : j + 1 + ____])\n        i = j + 1 + length\n    return res', '        res.append(s[j + 1 : j + 1 + length])\n        i = j + 1 + length\n    return res', ['slicing']),
], [[['neet', 'code', 'love', 'you']], [['we', 'say', ':', 'yes', '#4#']], [[]], [['']]],
  postlude="""
def _check(strs):
    c = Codec()
    return c.decode(c.encode(strs))
""", check='_check', want=[['neet', 'code', 'love', 'you'], ['we', 'say', ':', 'yes', '#4#'], [], ['']])

B('bp-trapping-rain', 'Trapping Rain Water', 'trapping-rain-water', 'hard', 'two-pointers',
  'Given bar heights, return how much rain water is trapped between them.', '[0,1,0,2,1,0,1,3,2,1,2,1] → 6', 'def trap(height):', [
  ('Two pointers at the ends, the tallest bar seen from each side, and the total', 'Start left_max and right_max at the end bars.', 'if not height:\n    return 0\nl, r = 0, len(height) - ____\nleft_max, right_max = height[l], height[r]\nwater = 0', 'if not height:\n    return 0\nl, r = 0, len(height) - 1\nleft_max, right_max = height[l], height[r]\nwater = 0', ['two-pointers']),
  ('Loop until the pointers meet, always moving the side with the smaller max', 'The smaller side is the one that limits the water.', 'while l < r:\n    if left_max < ____:', 'while l < r:\n    if left_max < right_max:', ['two-pointers']),
  ('Left side: step in, update its max, and add the water above this bar', 'Water above a bar is max on that side minus the bar.', '        l += 1\n        left_max = max(left_max, height[l])\n        water += left_max - height[____]', '        l += 1\n        left_max = max(left_max, height[l])\n        water += left_max - height[l]', ['max-min']),
  ('Otherwise do the same from the right, and return the total', 'Mirror image: r -= 1.', '    else:\n        r -= 1\n        right_max = max(right_max, height[r])\n        water += right_max - height[____]\nreturn water', '    else:\n        r -= 1\n        right_max = max(right_max, height[r])\n        water += right_max - height[r]\nreturn water', ['max-min']),
], [[[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]], [[4, 2, 0, 3, 2, 5]], [[]], [[3]]], want=[6, 9, 0, 0])

B('bp-char-replacement', 'Longest Repeating Character Replacement', 'longest-repeating-substring-with-replacement', 'medium', 'sliding-window',
  'You may replace at most k characters. Return the length of the longest substring that can become one repeated letter.', 's = "AABABBA", k = 1 → 4', 'def character_replacement(s, k):', [
  ('A dict of letter counts in the window, the left edge, the top count, and the best', 'Four setup values.', 'count = {}\nl = 0\ntop = 0\nbest = ____', 'count = {}\nl = 0\ntop = 0\nbest = 0', ['dict-get']),
  ('Grow the window to the right and count the new letter', 'count.get(ch, 0) + 1, then track the most common letter count.', 'for r in range(len(s)):\n    count[s[r]] = count.____(s[r], 0) + 1\n    top = max(top, count[s[r]])', 'for r in range(len(s)):\n    count[s[r]] = count.get(s[r], 0) + 1\n    top = max(top, count[s[r]])', ['dict-get', 'max-min']),
  ('If the letters to replace (window size minus top) exceed k, drop the left letter', 'Window size is r - l + 1. One step left is enough, so use if, not while.', '    if (r - l + 1) - top > ____:\n        count[s[l]] -= 1\n        l += 1', '    if (r - l + 1) - top > k:\n        count[s[l]] -= 1\n        l += 1', []),
  ('Record the window size, and return the best', 'max() again.', '    best = max(best, r - l + ____)\nreturn best', '    best = max(best, r - l + 1)\nreturn best', ['max-min']),
], [['ABAB', 2], ['AABABBA', 1], ['A', 0], ['AAAA', 0]], want=[4, 4, 1, 4])

B('bp-permutation-string', 'Permutation in String', 'permutation-string', 'medium', 'sliding-window',
  'Return True if some window of s2 is a rearrangement of s1.', 's1 = "ab", s2 = "eidbaooo" → True', 'def check_inclusion(s1, s2):', [
  ('If s1 is longer it can never fit; otherwise count the letters of s1', 'Counter(s1) counts every letter at once.', 'from collections import Counter\nif len(s1) > len(s2):\n    return False\nneed = ____(s1)', 'from collections import Counter\nif len(s1) > len(s2):\n    return False\nneed = Counter(s1)', ['counter']),
  ('Count the first window of s2, the same length as s1', 'Slice s2[:len(s1)].', 'window = Counter(s2[:____(s1)])\nif window == need:\n    return True', 'window = Counter(s2[:len(s1)])\nif window == need:\n    return True', ['counter', 'slicing']),
  ('Slide one step at a time: add the new letter on the right, remove the old one on the left', 'The letter leaving is s2[i - len(s1)].', 'for i in range(len(s1), len(s2)):\n    window[s2[i]] += 1\n    window[s2[i - ____(s1)]] -= 1', 'for i in range(len(s1), len(s2)):\n    window[s2[i]] += 1\n    window[s2[i - len(s1)]] -= 1', []),
  ('Compare after each step (drop zero counts first), and return False at the end', '+Counter() removes zero counts, so the comparison is fair.', '    if +window == ____:\n        return True\nreturn False', '    if +window == need:\n        return True\nreturn False', ['counter']),
], [['ab', 'eidbaooo'], ['ab', 'eidboaoo'], ['adc', 'dcda'], ['abc', 'ab']], want=[True, False, True, False])

B('bp-search-2d', 'Search a 2D Matrix', 'search-2d-matrix', 'medium', 'binary-search',
  'Each row is sorted, and each row starts after the previous one ends. Return True if target is in the matrix, in O(log(m·n)).', 'target 3 in [[1,3,5,7],[10,11,16,20],[23,30,34,60]] → True', 'def search_matrix(matrix, target):', [
  ('Treat the whole matrix as one sorted list of rows times cols cells', 'lo = 0, hi = rows * cols - 1.', 'rows, cols = len(matrix), len(matrix[0])\nlo, hi = 0, rows * ____ - 1', 'rows, cols = len(matrix), len(matrix[0])\nlo, hi = 0, rows * cols - 1', []),
  ('Binary search, turning the middle index back into a row and column', 'Row is mid // cols, column is mid % cols.', 'while lo <= hi:\n    mid = (lo + hi) // 2\n    val = matrix[mid // ____][mid % cols]', 'while lo <= hi:\n    mid = (lo + hi) // 2\n    val = matrix[mid // cols][mid % cols]', ['floor-div']),
  ('Found it, or throw away the half that can\'t hold it', 'Too small: lo = mid + 1. Too big: hi = mid - 1.', '    if val == target:\n        return True\n    if val < target:\n        lo = mid + ____\n    else:\n        hi = mid - 1', '    if val == target:\n        return True\n    if val < target:\n        lo = mid + 1\n    else:\n        hi = mid - 1', []),
  ('Not found after the loop', 'Return after the loop.', 'return ____', 'return False', []),
], [[[[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 3], [[[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 13], [[[1]], 1], [[[1, 3]], 3]], want=[True, False, True, True])

B('bp-find-min-rotated', 'Find Minimum in Rotated Sorted Array', 'find-minimum-in-rotated-sorted-array', 'medium', 'binary-search',
  'A sorted list of distinct numbers was rotated. Return the smallest value in O(log N).', '[3, 4, 5, 1, 2] → 1', 'def find_min(nums):', [
  ('Search the whole list', 'lo and hi at both ends.', 'lo, hi = 0, len(nums) - ____', 'lo, hi = 0, len(nums) - 1', []),
  ('Loop while lo is before hi and look at the middle', 'lo < hi, because you stop when one index is left.', 'while lo ____ hi:\n    mid = (lo + hi) // 2', 'while lo < hi:\n    mid = (lo + hi) // 2', ['floor-div']),
  ('If the middle is bigger than the right end, the drop (the minimum) is to the right; otherwise it is at mid or left', 'Compare with nums[hi]. Keep mid in the range in the second case: hi = mid.', '    if nums[mid] > nums[____]:\n        lo = mid + 1\n    else:\n        hi = mid', '    if nums[mid] > nums[hi]:\n        lo = mid + 1\n    else:\n        hi = mid', []),
  ('lo now points at the minimum', 'Return the value, not the index.', 'return nums[____]', 'return nums[lo]', []),
], [[[3, 4, 5, 1, 2]], [[4, 5, 6, 7, 0, 1, 2]], [[11, 13, 15, 17]], [[2, 1]]], want=[1, 0, 11, 1])

B('bp-search-rotated', 'Search in Rotated Sorted Array', 'find-target-in-rotated-sorted-array', 'medium', 'binary-search',
  'A sorted list of distinct numbers was rotated. Return the index of target or -1, in O(log N).', '[4,5,6,7,0,1,2], target 0 → 4', 'def search_rotated(nums, target):', [
  ('Standard binary search setup and loop', 'Inclusive hi, so lo <= hi.', 'lo, hi = 0, len(nums) - 1\nwhile lo <= hi:\n    mid = (lo + hi) // ____\n    if nums[mid] == target:\n        return mid', 'lo, hi = 0, len(nums) - 1\nwhile lo <= hi:\n    mid = (lo + hi) // 2\n    if nums[mid] == target:\n        return mid', ['floor-div']),
  ('If the left half is sorted, check whether the target lies inside it', 'Left half sorted when nums[lo] <= nums[mid]. Target inside means nums[lo] <= target < nums[mid].', '    if nums[lo] <= nums[mid]:\n        if nums[lo] <= target < nums[____]:\n            hi = mid - 1\n        else:\n            lo = mid + 1', '    if nums[lo] <= nums[mid]:\n        if nums[lo] <= target < nums[mid]:\n            hi = mid - 1\n        else:\n            lo = mid + 1', []),
  ('Otherwise the right half is sorted: check whether the target lies inside it', 'Inside means nums[mid] < target <= nums[hi].', '    else:\n        if nums[mid] < target <= nums[____]:\n            lo = mid + 1\n        else:\n            hi = mid - 1', '    else:\n        if nums[mid] < target <= nums[hi]:\n            lo = mid + 1\n        else:\n            hi = mid - 1', []),
  ('Not found', 'After the loop.', 'return ____', 'return -1', []),
], [[[4, 5, 6, 7, 0, 1, 2], 0], [[4, 5, 6, 7, 0, 1, 2], 3], [[1], 0], [[3, 1], 1]], want=[4, -1, -1, 1])

B('bp-time-map', 'Time Based Key-Value Store', 'time-based-key-value-store', 'medium', 'binary-search',
  'Build a TimeMap: set(key, value, timestamp) stores a value; get(key, timestamp) returns the value with the largest timestamp <= the given one, or "". Timestamps for a key always increase.', 'set("foo","bar",1); get("foo",3) → "bar"', 'class TimeMap:', [
  ('In __init__, make a dict from key to a list of [timestamp, value] pairs', 'self.store = {}', 'def __init__(self):\n    self.store = ____', 'def __init__(self):\n    self.store = {}', []),
  ('set appends the pair to that key\'s list', 'setdefault(key, []) creates the list the first time.', 'def set(self, key, value, timestamp):\n    self.store.____(key, []).append([timestamp, value])', 'def set(self, key, value, timestamp):\n    self.store.setdefault(key, []).append([timestamp, value])', ['dict-get']),
  ('get binary searches that list for the last timestamp <= the query', 'Pairs are in timestamp order. When pairs[mid][0] <= timestamp, it is a candidate: save it and search right.', 'def get(self, key, timestamp):\n    pairs = self.store.get(key, [])\n    res, lo, hi = "", 0, len(pairs) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if pairs[mid][0] <= ____:\n            res = pairs[mid][1]\n            lo = mid + 1\n        else:\n            hi = mid - 1', 'def get(self, key, timestamp):\n    pairs = self.store.get(key, [])\n    res, lo, hi = "", 0, len(pairs) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if pairs[mid][0] <= timestamp:\n            res = pairs[mid][1]\n            lo = mid + 1\n        else:\n            hi = mid - 1', ['floor-div']),
  ('Return the best candidate (or "" if none)', 'res started as "".', '    return ____', '    return res', []),
], [[['set', 'get', 'get', 'set', 'get', 'get'], [['foo', 'bar', 1], ['foo', 1], ['foo', 3], ['foo', 'bar2', 4], ['foo', 4], ['foo', 5]]], [['get'], [['x', 1]]], [['set', 'get'], [['a', 'b', 5], ['a', 4]]]],
  postlude="""
def _check(ops, args):
    tm, out = TimeMap(), []
    for op, a in zip(ops, args):
        out.append(getattr(tm, op)(*a))
    return out
""", check='_check', want=[[None, 'bar', 'bar', None, 'bar2', 'bar2'], [''], [None, '']])

B('bp-merge-two-lists', 'Merge Two Sorted Lists', 'merge-two-sorted-linked-lists', 'easy', 'reverse-ll',
  'Merge two sorted linked lists into one sorted list and return its head.', '1→2→4 and 1→3→4 → 1→1→2→3→4→4', 'def merge_two_lists(l1, l2):', [
  ('Make a dummy node so the head is easy to return, and a tail pointer', 'ListNode() is a placeholder in front of the answer.', 'dummy = ____()\ntail = dummy', 'dummy = ListNode()\ntail = dummy', []),
  ('While both lists have nodes, attach the smaller one', 'Compare .val, attach with tail.next, and move that list forward.', 'while l1 and l2:\n    if l1.val <= l2.val:\n        tail.next, l1 = l1, l1.____\n    else:\n        tail.next, l2 = l2, l2.next', 'while l1 and l2:\n    if l1.val <= l2.val:\n        tail.next, l1 = l1, l1.next\n    else:\n        tail.next, l2 = l2, l2.next', ['multi-assign']),
  ('Move the tail forward after each attach', 'tail = tail.next, inside the loop.', '    tail = tail.____', '    tail = tail.next', []),
  ('Attach whatever is left, and return the node after the dummy', 'One list may still have nodes: l1 or l2 picks the non-empty one.', 'tail.next = l1 ____ l2\nreturn dummy.next', 'tail.next = l1 or l2\nreturn dummy.next', []),
], [[[1, 2, 4], [1, 3, 4]], [[], []], [[], [0]], [[5], [1, 2, 3]]],
  postlude=LL + """
def _check(a, b):
    return _to_list(merge_two_lists(_build(a), _build(b)))
""", check='_check', want=[[1, 1, 2, 3, 4, 4], [], [0], [1, 2, 3, 5]])

B('bp-ll-cycle', 'Linked List Cycle', 'linked-list-cycle-detection', 'easy', 'fast-slow',
  'Return True if the linked list has a cycle, using O(1) memory.', '3→2→0→-4→(back to 2) → True', 'def has_cycle(head):', [
  ('Start a slow and a fast pointer at the head', 'Both start at head.', 'slow, fast = head, ____', 'slow, fast = head, head', ['multi-assign']),
  ('Loop while fast can still take two steps', 'Check fast and fast.next, or fast.next.next crashes on None.', 'while fast and fast.____:', 'while fast and fast.next:', []),
  ('Slow moves one step, fast moves two; if they meet there is a cycle', 'Compare the nodes themselves with is.', '    slow = slow.next\n    fast = fast.next.next\n    if slow ____ fast:\n        return True', '    slow = slow.next\n    fast = fast.next.next\n    if slow is fast:\n        return True', []),
  ('Fast fell off the end, so there is no cycle', 'After the loop.', 'return ____', 'return False', []),
], [[[3, 2, 0, -4], 1], [[1, 2], 0], [[1], -1], [[], -1]],
  postlude=LL + """
def _check(vals, pos):
    head = _build(vals)
    if pos >= 0:
        nodes, cur = [], head
        while cur:
            nodes.append(cur); cur = cur.next
        nodes[-1].next = nodes[pos]
    return has_cycle(head)
""", check='_check', want=[True, True, False, False])

B('bp-reorder-list', 'Reorder List', 'reorder-linked-list', 'medium', 'fast-slow',
  'Reorder L0→L1→…→Ln into L0→Ln→L1→Ln-1→… in place.', '1→2→3→4 → 1→4→2→3', 'def reorder_list(head):', [
  ('Find the middle with slow and fast pointers', 'fast starts one ahead so slow stops at the end of the first half.', 'slow, fast = head, head.____\nwhile fast and fast.next:\n    slow, fast = slow.next, fast.next.next', 'slow, fast = head, head.next\nwhile fast and fast.next:\n    slow, fast = slow.next, fast.next.next', ['multi-assign']),
  ('Cut the list after the middle and reverse the second half', 'Standard reverse with prev and cur.', 'second, slow.next = slow.next, None\nprev = None\nwhile second:\n    nxt = second.next\n    second.next = ____\n    prev, second = second, nxt', 'second, slow.next = slow.next, None\nprev = None\nwhile second:\n    nxt = second.next\n    second.next = prev\n    prev, second = second, nxt', ['multi-assign']),
  ('Weave: one node from the front, one from the reversed back, alternating', 'Save both next pointers before rewiring.', 'first, second = head, prev\nwhile second:\n    n1, n2 = first.next, second.____\n    first.next = second\n    second.next = n1\n    first, second = n1, n2', 'first, second = head, prev\nwhile second:\n    n1, n2 = first.next, second.next\n    first.next = second\n    second.next = n1\n    first, second = n1, n2', ['multi-assign']),
  ('It changes the list in place, so return nothing', 'Just return.', 'return ____', 'return None', []),
], [[[1, 2, 3, 4]], [[1, 2, 3, 4, 5]], [[1]], [[1, 2]]],
  postlude=LL + """
def _check(vals):
    head = _build(vals)
    if head:
        reorder_list(head)
    return _to_list(head)
""", check='_check', want=[[1, 4, 2, 3], [1, 5, 2, 4, 3], [1], [1, 2]])

B('bp-remove-nth', 'Remove Nth Node From End of List', 'remove-node-from-end-of-linked-list', 'medium', 'fast-slow',
  'Remove the n-th node from the end of the list in one pass, and return the head.', '1→2→3→4→5, n = 2 → 1→2→3→5', 'def remove_nth_from_end(head, n):', [
  ('A dummy node in front, so removing the head is not a special case', 'dummy.next = head.', 'dummy = ListNode(0, ____)\nleft = dummy\nright = head', 'dummy = ListNode(0, head)\nleft = dummy\nright = head', []),
  ('Move right n steps ahead', 'A for loop n times.', 'for _ in range(____):\n    right = right.next', 'for _ in range(n):\n    right = right.next', []),
  ('Move both until right falls off the end; left stops just before the node to remove', 'Walk together while right exists.', 'while ____:\n    left = left.next\n    right = right.next', 'while right:\n    left = left.next\n    right = right.next', []),
  ('Skip over the node, and return the real head', 'left.next jumps two ahead.', 'left.next = left.next.____\nreturn dummy.next', 'left.next = left.next.next\nreturn dummy.next', []),
], [[[1, 2, 3, 4, 5], 2], [[1], 1], [[1, 2], 1], [[1, 2], 2]],
  postlude=LL + """
def _check(vals, n):
    return _to_list(remove_nth_from_end(_build(vals), n))
""", check='_check', want=[[1, 2, 3, 5], [], [1], [2]])

B('bp-add-two-numbers', 'Add Two Numbers', 'add-two-numbers', 'medium', 'reverse-ll',
  'Two numbers are stored as linked lists with digits in reverse order. Return their sum as a linked list, also reversed.', '2→4→3 + 5→6→4 → 7→0→8 (342 + 465 = 807)', 'def add_two_numbers(l1, l2):', [
  ('A dummy head, a tail pointer, and a carry of 0', 'Three setup lines.', 'dummy = ListNode()\ntail = dummy\ncarry = ____', 'dummy = ListNode()\ntail = dummy\ncarry = 0', []),
  ('Keep going while either list has digits or there is a carry left', 'Missing digits count as 0.', 'while l1 or l2 or ____:\n    a = l1.val if l1 else 0\n    b = l2.val if l2 else 0', 'while l1 or l2 or carry:\n    a = l1.val if l1 else 0\n    b = l2.val if l2 else 0', []),
  ('Add the digits, split into the new digit and the carry, and attach a node', 'divmod(total, 10) gives (carry, digit).', '    carry, digit = ____(a + b + carry, 10)\n    tail.next = ListNode(digit)\n    tail = tail.next', '    carry, digit = divmod(a + b + carry, 10)\n    tail.next = ListNode(digit)\n    tail = tail.next', ['floor-div']),
  ('Move both lists forward, and return the result after the loop', 'Only move a list if it still has nodes.', '    l1 = l1.next if l1 else None\n    l2 = l2.next if l2 else ____\nreturn dummy.next', '    l1 = l1.next if l1 else None\n    l2 = l2.next if l2 else None\nreturn dummy.next', []),
], [[[2, 4, 3], [5, 6, 4]], [[0], [0]], [[9, 9, 9, 9], [9, 9]], [[1], [9, 9]]],
  postlude=LL + """
def _check(a, b):
    return _to_list(add_two_numbers(_build(a), _build(b)))
""", check='_check', want=[[7, 0, 8], [0], [8, 9, 0, 0, 1], [0, 0, 1]])

B('bp-find-duplicate', 'Find the Duplicate Number', 'find-duplicate-integer', 'medium', 'fast-slow',
  'nums has n + 1 numbers, each from 1 to n, and exactly one value repeats. Find it without changing nums and with O(1) memory.', '[1, 3, 4, 2, 2] → 2', 'def find_duplicate(nums):', [
  ('Treat each value as a pointer to an index; start slow and fast at 0', 'This turns the list into a linked list with a cycle.', 'slow, fast = 0, ____', 'slow, fast = 0, 0', ['multi-assign']),
  ('Move slow one step and fast two steps until they meet', 'One step is nums[slow]; two steps is nums[nums[fast]].', 'while True:\n    slow = nums[slow]\n    fast = nums[nums[____]]\n    if slow == fast:\n        break', 'while True:\n    slow = nums[slow]\n    fast = nums[nums[fast]]\n    if slow == fast:\n        break', []),
  ('Start a second pointer at 0 and move both one step until they meet: that is the cycle start', 'Floyd\'s trick: the meeting point is the duplicate.', 'slow2 = 0\nwhile slow2 != ____:\n    slow = nums[slow]\n    slow2 = nums[slow2]', 'slow2 = 0\nwhile slow2 != slow:\n    slow = nums[slow]\n    slow2 = nums[slow2]', []),
  ('Return where they met', 'Either pointer.', 'return ____', 'return slow', []),
], [[[1, 3, 4, 2, 2]], [[3, 1, 3, 4, 2]], [[1, 1]], [[2, 2, 2, 2]]], want=[2, 3, 1, 2])

B('bp-lru-cache', 'LRU Cache', 'lru-cache', 'medium', 'hashing',
  'Build an LRUCache with get(key) and put(key, value), both O(1). When over capacity, evict the least recently used key. get returns -1 for a missing key.', 'capacity 2: put(1,1), put(2,2), get(1) → 1, put(3,3) evicts 2', 'class LRUCache:', [
  ('In __init__, remember the capacity and make an OrderedDict (it keeps keys in use order)', 'from collections import OrderedDict at the top of __init__ works.', 'def __init__(self, capacity):\n    from collections import OrderedDict\n    self.cap = capacity\n    self.cache = ____()', 'def __init__(self, capacity):\n    from collections import OrderedDict\n    self.cap = capacity\n    self.cache = OrderedDict()', ['defaultdict']),
  ('get: missing key gives -1; otherwise mark it as most recent and return it', 'move_to_end(key) marks it most recent.', 'def get(self, key):\n    if key not in self.cache:\n        return -1\n    self.cache.____(key)\n    return self.cache[key]', 'def get(self, key):\n    if key not in self.cache:\n        return -1\n    self.cache.move_to_end(key)\n    return self.cache[key]', ['in-check']),
  ('put: store the value and mark it most recent', 'Set it, then move_to_end.', 'def put(self, key, value):\n    self.cache[key] = value\n    self.cache.move_to_end(____)', 'def put(self, key, value):\n    self.cache[key] = value\n    self.cache.move_to_end(key)', []),
  ('If over capacity, drop the oldest key (the first one)', 'popitem(last=False) removes the oldest.', '    if len(self.cache) > self.cap:\n        self.cache.popitem(last=____)', '    if len(self.cache) > self.cap:\n        self.cache.popitem(last=False)', []),
], [[2, ['put', 'put', 'get', 'put', 'get', 'put', 'get', 'get', 'get'], [[1, 1], [2, 2], [1], [3, 3], [2], [4, 4], [1], [3], [4]]], [1, ['put', 'get', 'put', 'get', 'get'], [[2, 1], [2], [3, 2], [2], [3]]]],
  postlude="""
def _check(cap, ops, args):
    c, out = LRUCache(cap), []
    for op, a in zip(ops, args):
        out.append(getattr(c, op)(*a))
    return out
""", check='_check', want=[[None, None, 1, None, -1, None, -1, 3, 4], [None, 1, None, -1, 2]])

B('bp-min-stack', 'Min Stack', 'minimum-stack', 'medium', 'monotonic-stack',
  'Build a MinStack with push, pop, top and getMin, all O(1).', 'push(-2), push(0), push(-3), getMin() → -3, pop(), getMin() → -2', 'class MinStack:', [
  ('In __init__, one stack for values and one for the minimum at each level', 'Two empty lists.', 'def __init__(self):\n    self.stack = []\n    self.mins = ____', 'def __init__(self):\n    self.stack = []\n    self.mins = []', ['stack']),
  ('push adds the value, and the smaller of it and the current minimum', 'If mins is empty, the value itself is the minimum.', 'def push(self, val):\n    self.stack.append(val)\n    self.mins.append(min(val, self.mins[-1]) if self.____ else val)', 'def push(self, val):\n    self.stack.append(val)\n    self.mins.append(min(val, self.mins[-1]) if self.mins else val)', ['stack', 'max-min']),
  ('pop removes from both stacks', 'Two .pop() calls.', 'def pop(self):\n    self.stack.pop()\n    self.mins.____()', 'def pop(self):\n    self.stack.pop()\n    self.mins.pop()', ['stack']),
  ('top and getMin just read the last item of each', 'stack[-1] is the top.', 'def top(self):\n    return self.stack[____]\n\ndef getMin(self):\n    return self.mins[-1]', 'def top(self):\n    return self.stack[-1]\n\ndef getMin(self):\n    return self.mins[-1]', ['stack']),
], [[['push', 'push', 'push', 'getMin', 'pop', 'top', 'getMin'], [[-2], [0], [-3], [], [], [], []]], [['push', 'getMin', 'push', 'getMin'], [[5], [], [7], []]]],
  postlude="""
def _check(ops, args):
    st, out = MinStack(), []
    for op, a in zip(ops, args):
        out.append(getattr(st, op)(*a))
    return out
""", check='_check', want=[[None, None, None, -3, None, 0, -2], [None, 5, None, 5]])

B('bp-eval-rpn', 'Evaluate Reverse Polish Notation', 'evaluate-reverse-polish-notation', 'medium', 'monotonic-stack',
  'Evaluate an expression in reverse Polish notation with + - * /. Division truncates toward zero.', '["2","1","+","3","*"] → 9', 'def eval_rpn(tokens):', [
  ('Make a stack and loop over the tokens', 'An empty list.', 'stack = ____\nfor t in tokens:', 'stack = []\nfor t in tokens:', ['stack']),
  ('A number goes straight onto the stack', 'Anything that is not one of the four operators is a number: int(t).', '    if t not in "+-*/":\n        stack.append(____(t))\n        continue', '    if t not in "+-*/":\n        stack.append(int(t))\n        continue', ['stack', 'in-check']),
  ('An operator pops two numbers; the second pop is the LEFT operand', 'b = pop(), then a = pop(), then compute a op b. int(a / b) truncates toward zero.', '    b, a = stack.pop(), stack.____()\n    if t == "+": stack.append(a + b)\n    elif t == "-": stack.append(a - b)\n    elif t == "*": stack.append(a * b)\n    else: stack.append(int(a / b))', '    b, a = stack.pop(), stack.pop()\n    if t == "+": stack.append(a + b)\n    elif t == "-": stack.append(a - b)\n    elif t == "*": stack.append(a * b)\n    else: stack.append(int(a / b))', ['stack', 'multi-assign']),
  ('The answer is the one value left', 'stack[0] or stack[-1].', 'return stack[____]', 'return stack[0]', []),
], [[['2', '1', '+', '3', '*']], [['4', '13', '5', '/', '+']], [['10', '6', '9', '3', '+', '-11', '*', '/', '*', '17', '+', '5', '+']], [['3', '-4', '/']]], want=[9, 6, 22, 0])

B('bp-generate-parens', 'Generate Parentheses', 'generate-parentheses', 'medium', 'backtracking',
  'Return every valid string of n pairs of parentheses.', 'n = 3 → ["((()))","(()())","(())()","()(())","()()()"]', 'def generate_parenthesis(n):', [
  ('Results list and a helper that tracks how many ( and ) are used', 'The helper builds the string as it goes.', 'res = ____\ndef bt(cur, opened, closed):', 'res = []\ndef bt(cur, opened, closed):', ['recursion']),
  ('When both counts reach n, the string is complete', 'Save it and return.', '    if opened == closed == ____:\n        res.append(cur)\n        return', '    if opened == closed == n:\n        res.append(cur)\n        return', ['recursion']),
  ('You can add ( while fewer than n are open, and ) while fewer ) than ( are used', 'Two separate ifs, both may happen.', '    if opened < n:\n        bt(cur + "(", opened + 1, closed)\n    if closed < ____:\n        bt(cur + ")", opened, closed + 1)', '    if opened < n:\n        bt(cur + "(", opened + 1, closed)\n    if closed < opened:\n        bt(cur + ")", opened, closed + 1)', ['recursion']),
  ('Start empty and return the results', 'bt("", 0, 0).', 'bt("", 0, ____)\nreturn res', 'bt("", 0, 0)\nreturn res', []),
], [[3], [1], [2]],
  postlude="""
def _check(n):
    return sorted(generate_parenthesis(n))
""", check='_check', want=[['((()))', '(()())', '(())()', '()(())', '()()()'], ['()'], ['(())', '()()']])

B('bp-car-fleet', 'Car Fleet', 'car-fleet', 'medium', 'monotonic-stack',
  'Cars drive toward target on one lane and can\'t pass. A car that catches up joins the slower fleet. Return how many fleets arrive.', 'target 12, position [10,8,0,5,3], speed [2,4,1,1,3] → 3', 'def car_fleet(target, position, speed):', [
  ('Pair each car\'s position with its speed, sorted from closest to the target first', 'sorted(zip(...), reverse=True).', 'cars = sorted(zip(position, speed), reverse=____)\nstack = []', 'cars = sorted(zip(position, speed), reverse=True)\nstack = []', ['sort', 'stack']),
  ('For each car, work out the time it needs to reach the target', 'Time is distance over speed.', 'for p, s in cars:\n    time = (target - p) / ____', 'for p, s in cars:\n    time = (target - p) / s', []),
  ('If it needs MORE time than the fleet ahead, it can\'t catch it: it starts a new fleet', 'Compare with stack[-1], the slowest fleet ahead so far.', '    if not stack or time > stack[____]:\n        stack.append(time)', '    if not stack or time > stack[-1]:\n        stack.append(time)', ['stack']),
  ('The number of fleets is the stack size', 'len().', 'return ____(stack)', 'return len(stack)', []),
], [[12, [10, 8, 0, 5, 3], [2, 4, 1, 1, 3]], [10, [3], [3]], [100, [0, 2, 4], [4, 2, 1]]], want=[3, 1, 1])

B('bp-diameter', 'Diameter of Binary Tree', 'binary-tree-diameter', 'easy', 'tree-traversal',
  'Return the number of edges on the longest path between any two nodes.', '[1,2,3,4,5] → 3', 'def diameter_of_binary_tree(root):', [
  ('Keep the best answer in a list so the helper can update it', 'A one item list is easy to change inside a nested function.', 'best = [____]', 'best = [0]', []),
  ('A helper returns the height of a subtree; empty is 0', 'Base case first.', 'def height(node):\n    if not node:\n        return ____', 'def height(node):\n    if not node:\n        return 0', ['recursion']),
  ('Get both heights; the longest path through this node is their sum', 'Update best[0] with max.', '    l, r = height(node.left), height(node.right)\n    best[0] = max(best[0], l + ____)\n    return 1 + max(l, r)', '    l, r = height(node.left), height(node.right)\n    best[0] = max(best[0], l + r)\n    return 1 + max(l, r)', ['recursion', 'max-min']),
  ('Run it from the root and return the best', 'Call, then return best[0].', 'height(root)\nreturn best[____]', 'height(root)\nreturn best[0]', []),
], [[[1, 2, 3, 4, 5]], [[1, 2]], [[]], [[1]]],
  postlude=TREE + """
def _check(vals):
    return diameter_of_binary_tree(_tree(vals))
""", check='_check', want=[3, 1, 0, 0])

B('bp-balanced', 'Balanced Binary Tree', 'balanced-binary-tree', 'easy', 'tree-traversal',
  'A tree is balanced if, at every node, the left and right heights differ by at most 1.', '[3,9,20,null,null,15,7] → True', 'def is_balanced(root):', [
  ('A helper returns the height, or -1 as soon as anything below is unbalanced', 'Empty tree has height 0.', 'def check(node):\n    if not node:\n        return ____', 'def check(node):\n    if not node:\n        return 0', ['recursion']),
  ('Check both sides; pass -1 straight up if either is unbalanced', 'Return early so you don\'t do extra work.', '    l = check(node.left)\n    r = check(node.right)\n    if l == -1 or r == ____:\n        return -1', '    l = check(node.left)\n    r = check(node.right)\n    if l == -1 or r == -1:\n        return -1', ['recursion']),
  ('If the heights differ by more than 1, it\'s unbalanced; otherwise return the height', 'abs() of the difference.', '    if ____(l - r) > 1:\n        return -1\n    return 1 + max(l, r)', '    if abs(l - r) > 1:\n        return -1\n    return 1 + max(l, r)', ['max-min']),
  ('Balanced means the helper didn\'t return -1', 'Compare with != -1.', 'return check(root) != ____', 'return check(root) != -1', []),
], [[[3, 9, 20, None, None, 15, 7]], [[1, 2, 2, 3, 3, None, None, 4, 4]], [[]], [[1, 2]]],
  postlude=TREE + """
def _check(vals):
    return is_balanced(_tree(vals))
""", check='_check', want=[True, False, True, True])

B('bp-same-tree', 'Same Tree', 'same-binary-tree', 'easy', 'tree-traversal',
  'Return True if two binary trees have the same shape and the same values.', '[1,2,3] and [1,2,3] → True', 'def is_same_tree(p, q):', [
  ('Both empty: the same', 'not p and not q.', 'if not p and not ____:\n    return True', 'if not p and not q:\n    return True', ['recursion']),
  ('Only one empty: different', 'After the first check, "not p or not q" means exactly one is empty.', 'if not p or not ____:\n    return False', 'if not p or not q:\n    return False', []),
  ('Different values: different', 'Compare .val.', 'if p.val != q.____:\n    return False', 'if p.val != q.val:\n    return False', []),
  ('Otherwise both left subtrees and both right subtrees must match', 'Two recursive calls joined with and.', 'return is_same_tree(p.left, q.left) and is_same_tree(p.____, q.right)', 'return is_same_tree(p.left, q.left) and is_same_tree(p.right, q.right)', ['recursion']),
], [[[1, 2, 3], [1, 2, 3]], [[1, 2], [1, None, 2]], [[1, 2, 1], [1, 1, 2]], [[], []]],
  postlude=TREE + """
def _check(a, b):
    return is_same_tree(_tree(a), _tree(b))
""", check='_check', want=[True, False, False, True])

B('bp-subtree', 'Subtree of Another Tree', 'subtree-of-a-binary-tree', 'easy', 'tree-traversal',
  'Return True if subRoot appears inside root as a whole subtree (same shape and values).', 'root [3,4,5,1,2], subRoot [4,1,2] → True', 'def is_subtree(root, sub):', [
  ('A helper that checks if two trees are identical', 'Same as the Same Tree problem.', 'def same(a, b):\n    if not a and not b:\n        return True\n    if not a or not b or a.val != b.val:\n        return ____\n    return same(a.left, b.left) and same(a.right, b.right)', 'def same(a, b):\n    if not a and not b:\n        return True\n    if not a or not b or a.val != b.val:\n        return False\n    return same(a.left, b.left) and same(a.right, b.right)', ['recursion']),
  ('An empty sub is always a subtree; an empty root can\'t contain a non-empty one', 'Check sub first.', 'if not sub:\n    return True\nif not ____:\n    return False', 'if not sub:\n    return True\nif not root:\n    return False', []),
  ('If the tree starting here matches, done', 'Call the helper on root and sub.', 'if same(root, ____):\n    return True', 'if same(root, sub):\n    return True', []),
  ('Otherwise look for it in the left or right subtree', 'Recurse on both sides with or.', 'return is_subtree(root.left, sub) ____ is_subtree(root.right, sub)', 'return is_subtree(root.left, sub) or is_subtree(root.right, sub)', ['recursion']),
], [[[3, 4, 5, 1, 2], [4, 1, 2]], [[3, 4, 5, 1, 2, None, None, None, None, 0], [4, 1, 2]], [[1, 1], [1]]],
  postlude=TREE + """
def _check(a, b):
    return is_subtree(_tree(a), _tree(b))
""", check='_check', want=[True, False, True])

B('bp-lca-bst', 'Lowest Common Ancestor of a BST', 'lowest-common-ancestor-in-binary-search-tree', 'medium', 'tree-traversal',
  'In a binary search tree, return the value of the lowest node that has both p and q below it (a node counts as below itself).', 'BST [6,2,8,0,4,7,9,null,null,3,5], p 2, q 8 → 6', 'def lowest_common_ancestor(root, p, q):', [
  ('Start at the root and walk down', 'A loop, no recursion needed.', 'cur = ____\nwhile cur:', 'cur = root\nwhile cur:', []),
  ('If both values are bigger, the answer is in the right subtree', 'In a BST, bigger values live on the right.', '    if p > cur.val and q > cur.val:\n        cur = cur.____', '    if p > cur.val and q > cur.val:\n        cur = cur.right', []),
  ('If both are smaller, go left', 'Mirror image.', '    elif p < cur.val and q < cur.val:\n        cur = cur.____', '    elif p < cur.val and q < cur.val:\n        cur = cur.left', []),
  ('Otherwise they split here (or one IS this node): this is the answer', 'Return its value.', '    else:\n        return cur.____', '    else:\n        return cur.val', []),
], [[[6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 2, 8], [[6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 2, 4], [[2, 1], 2, 1]],
  postlude=TREE + """
def _check(vals, p, q):
    return lowest_common_ancestor(_tree(vals), p, q)
""", check='_check', want=[6, 2, 2])

B('bp-level-order', 'Binary Tree Level Order Traversal', 'level-order-traversal-of-binary-tree', 'medium', 'bfs',
  'Return the node values level by level, left to right.', '[3,9,20,null,null,15,7] → [[3],[9,20],[15,7]]', 'def level_order(root):', [
  ('Results list and a queue that starts with the root (if there is one)', 'deque([root]) if root else deque().', 'from collections import deque\nres = []\nq = ____([root] if root else [])', 'from collections import deque\nres = []\nq = deque([root] if root else [])', ['deque']),
  ('While the queue has nodes, take exactly one level: as many nodes as are in the queue now', 'len(q) at the start of the loop is this level\'s size.', 'while q:\n    level = []\n    for _ in range(____(q)):', 'while q:\n    level = []\n    for _ in range(len(q)):', ['deque']),
  ('Pop each node, record its value, and queue its children', 'popleft() takes from the front.', '        node = q.____()\n        level.append(node.val)\n        if node.left: q.append(node.left)\n        if node.right: q.append(node.right)', '        node = q.popleft()\n        level.append(node.val)\n        if node.left: q.append(node.left)\n        if node.right: q.append(node.right)', ['deque']),
  ('Save the level, and return all levels at the end', 'Append the list after the inner loop.', '    res.append(____)\nreturn res', '    res.append(level)\nreturn res', []),
], [[[3, 9, 20, None, None, 15, 7]], [[1]], [[]]],
  postlude=TREE + """
def _check(vals):
    return level_order(_tree(vals))
""", check='_check', want=[[[3], [9, 20], [15, 7]], [[1]], []])

B('bp-right-side', 'Binary Tree Right Side View', 'binary-tree-right-side-view', 'medium', 'bfs',
  'Return the values you would see standing on the right side of the tree, top to bottom.', '[1,2,3,null,5,null,4] → [1,3,4]', 'def right_side_view(root):', [
  ('Results and a queue starting with the root', 'Same start as level order.', 'from collections import deque\nres = []\nq = deque([root] if root else ____)', 'from collections import deque\nres = []\nq = deque([root] if root else [])', ['deque']),
  ('Process one level at a time', 'Loop len(q) times.', 'while q:\n    for i in range(____(q)):', 'while q:\n    for i in range(len(q)):', ['deque']),
  ('Pop each node and queue its children, left then right', 'popleft().', '        node = q.popleft()\n        if node.left: q.append(node.left)\n        if node.right: q.append(node.____)', '        node = q.popleft()\n        if node.left: q.append(node.left)\n        if node.right: q.append(node.right)', ['deque']),
  ('The last node popped in each level is the one you see; return the list at the end', 'After the inner loop, node is the last one of the level.', '    res.append(node.____)\nreturn res', '    res.append(node.val)\nreturn res', []),
], [[[1, 2, 3, None, 5, None, 4]], [[1, None, 3]], [[]], [[1, 2]]],
  postlude=TREE + """
def _check(vals):
    return right_side_view(_tree(vals))
""", check='_check', want=[[1, 3, 4], [1, 3], [], [1, 2]])

B('bp-good-nodes', 'Count Good Nodes in Binary Tree', 'count-good-nodes-in-binary-tree', 'medium', 'dfs',
  'A node is good if no node on the path from the root to it has a bigger value. Count the good nodes.', '[3,1,4,3,null,1,5] → 4', 'def good_nodes(root):', [
  ('A helper that carries the biggest value seen on the path so far', 'Empty node adds 0.', 'def dfs(node, top):\n    if not node:\n        return ____', 'def dfs(node, top):\n    if not node:\n        return 0', ['recursion']),
  ('This node is good if it is at least as big as everything above it', '1 if good else 0.', '    good = 1 if node.val >= ____ else 0', '    good = 1 if node.val >= top else 0', []),
  ('Update the path max and add the counts from both children', 'max(top, node.val) is the new path max.', '    top = max(top, node.____)\n    return good + dfs(node.left, top) + dfs(node.right, top)', '    top = max(top, node.val)\n    return good + dfs(node.left, top) + dfs(node.right, top)', ['recursion', 'max-min']),
  ('Start at the root with its own value as the max', 'The root is always good.', 'return dfs(root, root.val) if root else ____', 'return dfs(root, root.val) if root else 0', []),
], [[[3, 1, 4, 3, None, 1, 5]], [[3, 3, None, 4, 2]], [[1]]],
  postlude=TREE + """
def _check(vals):
    return good_nodes(_tree(vals))
""", check='_check', want=[4, 3, 1])

B('bp-validate-bst', 'Validate Binary Search Tree', 'valid-binary-search-tree', 'medium', 'dfs',
  'Return True if the tree is a valid BST: every node is bigger than everything in its left subtree and smaller than everything in its right subtree.', '[5,1,4,null,null,3,6] → False', 'def is_valid_bst(root):', [
  ('A helper that carries the allowed range (low, high) for each node', 'An empty node is always valid.', 'def ok(node, low, high):\n    if not node:\n        return ____', 'def ok(node, low, high):\n    if not node:\n        return True', ['recursion']),
  ('The node must be strictly inside its range', 'Equal values are not allowed.', '    if not (low < node.val < ____):\n        return False', '    if not (low < node.val < high):\n        return False', []),
  ('Left children must be below this value, right children above it', 'Tighten one bound on each side.', '    return ok(node.left, low, node.val) and ok(node.right, node.____, high)', '    return ok(node.left, low, node.val) and ok(node.right, node.val, high)', ['recursion']),
  ('Start with no limits', "float('-inf') and float('inf').", "return ok(root, float('-inf'), float('____'))", "return ok(root, float('-inf'), float('inf'))", ['infinity']),
], [[[2, 1, 3]], [[5, 1, 4, None, None, 3, 6]], [[5, 4, 6, None, None, 3, 7]], [[1, 1]]],
  postlude=TREE + """
def _check(vals):
    return is_valid_bst(_tree(vals))
""", check='_check', want=[True, False, False, False])

B('bp-kth-smallest-bst', 'Kth Smallest Element in a BST', 'kth-smallest-integer-in-bst', 'medium', 'dfs',
  'Return the k-th smallest value in a BST (1-indexed).', '[3,1,4,null,2], k = 1 → 1', 'def kth_smallest(root, k):', [
  ('In-order traversal visits a BST in sorted order; do it with a stack', 'cur starts at root.', 'stack, cur = [], ____', 'stack, cur = [], root', ['stack']),
  ('Go as far left as possible, pushing nodes on the way', 'The smallest unvisited value is the leftmost.', 'while stack or cur:\n    while cur:\n        stack.append(cur)\n        cur = cur.____', 'while stack or cur:\n    while cur:\n        stack.append(cur)\n        cur = cur.left', ['stack']),
  ('Pop the next smallest; count it, and stop at the k-th', 'k -= 1 each visit.', '    cur = stack.pop()\n    k -= 1\n    if k == ____:\n        return cur.val', '    cur = stack.pop()\n    k -= 1\n    if k == 0:\n        return cur.val', ['stack']),
  ('Then continue into its right subtree', 'cur = cur.right.', '    cur = cur.____', '    cur = cur.right', []),
], [[[3, 1, 4, None, 2], 1], [[5, 3, 6, 2, 4, None, None, 1], 3], [[1], 1]],
  postlude=TREE + """
def _check(vals, k):
    return kth_smallest(_tree(vals), k)
""", check='_check', want=[1, 3, 1])

B('bp-build-tree', 'Construct Binary Tree from Preorder and Inorder', 'binary-tree-from-preorder-and-inorder-traversal', 'medium', 'dfs',
  'Rebuild a binary tree (unique values) from its preorder and inorder lists.', 'pre [3,9,20,15,7], in [9,3,15,20,7] → [3,9,20,15,7]', 'def build_tree(preorder, inorder):', [
  ('Map each value to its index in inorder for O(1) lookups, and keep a position in preorder', 'A dict comprehension with enumerate.', 'idx = {v: i for i, v in ____(inorder)}\npos = [0]', 'idx = {v: i for i, v in enumerate(inorder)}\npos = [0]', ['enumerate']),
  ('A helper builds the subtree for the inorder range lo..hi; an empty range is no node', 'lo > hi means nothing left.', 'def build(lo, hi):\n    if lo > ____:\n        return None', 'def build(lo, hi):\n    if lo > hi:\n        return None', ['recursion']),
  ('The next preorder value is this subtree\'s root', 'Read preorder[pos[0]], then move pos forward.', '    val = preorder[pos[0]]\n    pos[0] += 1\n    node = TreeNode(____)\n    mid = idx[val]', '    val = preorder[pos[0]]\n    pos[0] += 1\n    node = TreeNode(val)\n    mid = idx[val]', []),
  ('Everything left of it in inorder is the left subtree; build left first, then right', 'Order matters: preorder lists the left subtree before the right.', '    node.left = build(lo, mid - 1)\n    node.right = build(mid + 1, ____)\n    return node\nreturn build(0, len(inorder) - 1)', '    node.left = build(lo, mid - 1)\n    node.right = build(mid + 1, hi)\n    return node\nreturn build(0, len(inorder) - 1)', ['recursion']),
], [[[3, 9, 20, 15, 7], [9, 3, 15, 20, 7]], [[-1], [-1]], [[1, 2], [2, 1]]],
  postlude=TREE + """
def _check(pre, ino):
    return _level(build_tree(pre, ino))
""", check='_check', want=[[3, 9, 20, 15, 7], [-1], [1, 2]])

# ───────────────────────── Build, verify, emit ─────────────────────────
def assemble(p, use='code'):
    body = '\n'.join(s[use] for s in p['steps'])
    return p['signature'] + '\n' + textwrap.indent(body, '    ') + '\n'

for p in P:
    src = assemble(p)
    p['solution'] = src
    full = src + ('\n\n' + p['postlude'] if p['postlude'] else '')
    ns = {}
    exec(full, ns)
    fname = re.match(r'(?:def|class) (\w+)', p['signature']).group(1)
    fn = ns[p['check'] or fname]
    p['func'] = p['check'] or fname
    p['expected'] = [json.loads(json.dumps(fn(*copy.deepcopy(t)))) for t in p['tests']]
    if p.get('want') is not None:
        assert p['expected'] == p['want'], (p['id'], p['expected'], p['want'])
    p.pop('want', None)
    # Every template must have blanks and still be the same shape as the code.
    for s in p['steps']:
        assert '____' in s['template'], (p['id'], s['text'])
        assert len(s['template'].splitlines()) == len(s['code'].splitlines()), (p['id'], s['text'])
        for i in s['idioms']:
            assert i in IDIOMS, i
    assert len(p['steps']) == 4, p['id']

assert len({p['id'] for p in P}) == len(P)
print(len(P), 'blueprints verified')
root = pathlib.Path(__file__).resolve().parent.parent
idioms = {k: {'label': v[0], 'example': v[1]} for k, v in IDIOMS.items()}
(root / 'src/data/blueprints.ts').write_text(
    '// Generated by scripts/blueprints.py. Edit that file, then run: python3 scripts/blueprints.py\n'
    "import type { Blueprint } from '../types';\n\n"
    'export const IDIOMS: Record<string, { label: string; example: string }> = ' + json.dumps(idioms, indent=1) + ';\n\n'
    'export const BLUEPRINTS: Blueprint[] = ' + json.dumps(P, indent=1) + ';\n')
