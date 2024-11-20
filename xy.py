from itertools import combinations, chain

def powerset(iterable):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

def naive(text, width):
    words = text.split()
    count = len(words)

    minimum = 10 ** 20
    breaks = ()
    for b in powerset(range(1, count)):
        m = 0
        i = 0
        for j in chain(b, (count,)):
            w = len(' '.join(words[i:j]))
            if w > width:
                break
            m += (width - w) ** 2
            i = j
        else:
            if m < minimum:
                minimum = m
                breaks = b

    lines = []
    i = 0
    for j in chain(breaks, (count,)):
        lines.append(' '.join(words[i:j]))
        i = j
    return lines

# %%
def dynamic(text, width):
    words = text.split()
    count = len(words)
    slack = [[0] * count for i in range(count)]
    for i in range(count):
        slack[i][i] = width - len(words[i])
        for j in range(i + 1, count):
            slack[i][j] = slack[i][j - 1] - len(words[j]) - 1

    minima = [0] + [10 ** 20] * count
    breaks = [0] * count
    for j in range(count):
        i = j
        while i >= 0:
            if slack[i][j] < 0:
                cost = 10 ** 10
            else:
                cost = minima[i] + slack[i][j] ** 2
            if minima[j + 1] > cost:
                minima[j + 1] = cost
                breaks[j] = i
            i -= 1

    lines = []
    j = count
    while j > 0:
        i = breaks[j - 1]
        lines.append(' '.join(words[i:j]))
        j = i
    lines.reverse()
    return lines

# %%
def shortest(text, width):
    words = text.split()
    count = len(words)
    offsets = [0]
    for w in words:
        offsets.append(offsets[-1] + len(w))

    minima = [0] + [10 ** 20] * count
    breaks = [0] * (count + 1)
    for i in range(count):
        j = i + 1
        while j <= count:
            w = offsets[j] - offsets[i] + j - i - 1
            if w > width:
                break
            cost = minima[i] + (width - w) ** 2
            if cost < minima[j]:
                minima[j] = cost
                breaks[j] = i
            j += 1

    lines = []
    j = count
    while j > 0:
        i = breaks[j]
        lines.append(' '.join(words[i:j]))
        j = i
    lines.reverse()
    return lines

# %%
from collections import deque

def binary(text, width):
    words = text.split()
    count = len(words)
    offsets = [0]
    for w in words:
        offsets.append(offsets[-1] + len(w))

    minima = [0] * (count + 1)
    breaks = [0] * (count + 1)

    def c(i, j):
        w = offsets[j] - offsets[i] + j - i - 1
        if w > width:
            return 10 ** 10 * (w - width)
        return minima[i] + (width - w) ** 2

    def h(l, k):
        low, high = l + 1, count
        while low < high:
            mid = (low + high) // 2
            if c(l, mid) <= c(k, mid):
                high = mid
            else:
                low = mid + 1
        if c(l, high) <= c(k, high):
            return high
        return l + 2

    q = deque([(0, 1)])
    for j in range(1, count + 1):
        l = q[0][0]
        if c(j - 1, j) <= c(l, j):
            minima[j] = c(j - 1, j)
            breaks[j] = j - 1
            q.clear()
            q.append((j - 1, j + 1))
        else:
            minima[j] = c(l, j)
            breaks[j] = l
            while c(j - 1, q[-1][1]) <= c(q[-1][0], q[-1][1]):
                q.pop()
            q.append((j - 1, h(j - 1, q[-1][0])))
            if j + 1 == q[1][1]:
                q.popleft()
            else:
                q[0] = q[0][0], (q[0][1] + 1)

    lines = []
    j = count
    while j > 0:
        i = breaks[j]
        lines.append(' '.join(words[i:j]))
        j = i
    lines.reverse()
    return lines


# %%
def linear(text, width):
    count = len(words)
    offsets = [0]
    for w in words:
        offsets.append(offsets[-1] + len(w))

    minima = [0] + [10 ** 20] * count
    breaks = [0] * (count + 1)

    def cost(i, j):
        w = offsets[j] - offsets[i] + j - i - 1
        if w > width:
            return 10 ** 10 * (w - width)
        return minima[i] + (width - w) ** 2

    def smawk(rows, columns):
        stack = []
        i = 0
        while i < len(rows):
            if stack:
                c = columns[len(stack) - 1]
                if cost(stack[-1], c) < cost(rows[i], c):
                    if len(stack) < len(columns):
                        stack.append(rows[i])
                    i += 1
                else:
                    stack.pop()
            else:
                stack.append(rows[i])
                i += 1
        rows = stack

        if len(columns) > 1:
            smawk(rows, columns[1::2])

        i = j = 0
        while j < len(columns):
            if j + 1 < len(columns):
                end = breaks[columns[j + 1]]
            else:
                end = rows[-1]
            c = cost(rows[i], columns[j])
            if c < minima[columns[j]]:
                minima[columns[j]] = c
                breaks[columns[j]] = rows[i]
            if rows[i] < end:
                i += 1
            else:
                j += 2

    n = count + 1
    i = 0
    offset = 0
    while True:
        r = min(n, 2 ** (i + 1))
        edge = 2 ** i + offset
        smawk(range(0 + offset, edge), range(edge, r + offset))
        x = minima[r - 1 + offset]
        for j in range(2 ** i, r - 1):
            y = cost(j + offset, r - 1 + offset)
            if y <= x:
                n -= j
                i = 0
                offset += j
                break
        else:
            if r == n:
                break
            i = i + 1

    lines = []
    j = count
    while j > 0:
        i = breaks[j]
        lines.append(' '.join(words[i:j]))
        j = i
    lines.reverse()
    return lines



# %%
def divide(text, width):
    words = text.split()
    count = len(words)
    offsets = [0]
    for w in words:
        offsets.append(offsets[-1] + len(w))

    minima = [0] + [10 ** 20] * count
    breaks = [0] * (count + 1)

    def cost(i, j):
        w = offsets[j] - offsets[i] + j - i - 1
        if w > width:
            return 10 ** 10
        return minima[i] + (width - w) ** 2

    def search(i0, j0, i1, j1):
        stack = [(i0, j0, i1, j1)]
        while stack:
            i0, j0, i1, j1 = stack.pop()
            if j0 < j1:
                j = (j0 + j1) // 2
                for i in range(i0, i1):
                    c = cost(i, j)
                    if c <= minima[j]:
                        minima[j] = c
                        breaks[j] = i
                stack.append((breaks[j], j+1, i1, j1))
                stack.append((i0, j0, breaks[j]+1, j))

    n = count + 1
    i = 0
    offset = 0
    while True:
        r = min(n, 2 ** (i + 1))
        edge = 2 ** i + offset
        search(0 + offset, edge, edge, r + offset)
        x = minima[r - 1 + offset]
        for j in range(2 ** i, r - 1):
            y = cost(j + offset, r - 1 + offset)
            if y <= x:
                n -= j
                i = 0
                offset += j
                break
        else:
            if r == n:
                break
            i = i + 1

    lines = []
    j = count
    while j > 0:
        i = breaks[j]
        lines.append(' '.join(words[i:j]))
        j = i
    lines.reverse()
    return lines
