"""Source of truth for Blueprint Builder.

Each problem is a function broken into numbered plain-English steps. Every step
has three hint levels: a syntax clue, a fill-in-the-blank template, and the
exact lines. Running this file stitches the steps into a full solution, runs it
against the tests to fill in expected outputs, and writes
src/data/blueprints.ts.

Run:  python3 scripts/blueprints.py
"""
import copy, json, pathlib, textwrap

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
def B(id, title, nc, difficulty, pattern, statement, example, signature, steps, tests, postlude='', check=None):
    """steps: list of (text, clue, template, code, idioms). code/template are function-body lines (no leading indent)."""
    P.append(dict(id=id, title=title, nc=nc, difficulty=difficulty, pattern=pattern, statement=statement, example=example,
                  signature=signature, steps=[dict(text=t, clue=c, template=tm.strip('\n'), code=cd.strip('\n'), idioms=i) for t, c, tm, cd, i in steps],
                  tests=tests, postlude=textwrap.dedent(postlude).strip('\n'), check=check))

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
], [[[-1, 0, 3, 5, 9, 12], 9], [[-1, 0, 3, 5, 9, 12], 2], [[5], 5], [[1, 3], 3]])

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
    fn = ns[p['check'] or p['signature'].split('def ')[1].split('(')[0]]
    p['func'] = p['check'] or p['signature'].split('def ')[1].split('(')[0]
    p['expected'] = [json.loads(json.dumps(fn(*copy.deepcopy(t)))) for t in p['tests']]
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
