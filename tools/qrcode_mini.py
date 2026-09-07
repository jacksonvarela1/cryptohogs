#!/usr/bin/env python3
"""A small, dependency free QR Code encoder (ISO/IEC 18004), byte mode.

Only what the club needs: versions 1 to 10, error correction levels L, M, Q and H,
byte mode, automatic version choice, automatic mask choice. Standard library only,
so tools/build-flyer.py runs on any Python 3.9+ with nothing installed.

    from qrcode_mini import encode, svg_path
    matrix = encode("https://example.com", ecl="Q")   # list of list of bool

The matrix is row major, matrix[row][col], True meaning a dark module. It carries
no quiet zone; the caller adds the required four module margin.
"""

# ------------------------------------------------------------------ GF(256)
_EXP = [0] * 512
_LOG = [0] * 256
_x = 1
for _i in range(255):
    _EXP[_i] = _x
    _LOG[_x] = _i
    _x <<= 1
    if _x & 0x100:
        _x ^= 0x11D
for _i in range(255, 512):
    _EXP[_i] = _EXP[_i - 255]


def _mul(a, b):
    if a == 0 or b == 0:
        return 0
    return _EXP[_LOG[a] + _LOG[b]]


def _generator(degree):
    """The Reed-Solomon generator polynomial of the given degree."""
    poly = [1]
    for i in range(degree):
        nxt = [0] * (len(poly) + 1)
        for j, c in enumerate(poly):
            nxt[j] ^= c
            nxt[j + 1] ^= _mul(c, _EXP[i])
        poly = nxt
    return poly


def _ec_codewords(data, count):
    gen = _generator(count)
    rem = list(data) + [0] * count
    for i in range(len(data)):
        factor = rem[i]
        if factor == 0:
            continue
        for j, g in enumerate(gen):
            rem[i + j] ^= _mul(g, factor)
    return rem[len(data):]


# -------------------------------------------------------------- code tables
# version -> total codewords in the symbol
TOTAL_CODEWORDS = {1: 26, 2: 44, 3: 70, 4: 100, 5: 134,
                   6: 172, 7: 196, 8: 242, 9: 292, 10: 346}

# (version, level) -> (ec codewords per block, [(block count, data codewords), ...])
BLOCKS = {
    (1, "L"): (7, [(1, 19)]),   (1, "M"): (10, [(1, 16)]),
    (1, "Q"): (13, [(1, 13)]),  (1, "H"): (17, [(1, 9)]),
    (2, "L"): (10, [(1, 34)]),  (2, "M"): (16, [(1, 28)]),
    (2, "Q"): (22, [(1, 22)]),  (2, "H"): (28, [(1, 16)]),
    (3, "L"): (15, [(1, 55)]),  (3, "M"): (26, [(1, 44)]),
    (3, "Q"): (18, [(2, 17)]),  (3, "H"): (22, [(2, 13)]),
    (4, "L"): (20, [(1, 80)]),  (4, "M"): (18, [(2, 32)]),
    (4, "Q"): (26, [(2, 24)]),  (4, "H"): (16, [(4, 9)]),
    (5, "L"): (26, [(1, 108)]), (5, "M"): (24, [(2, 43)]),
    (5, "Q"): (18, [(2, 15), (2, 16)]), (5, "H"): (22, [(2, 11), (2, 12)]),
    (6, "L"): (18, [(2, 68)]),  (6, "M"): (16, [(4, 27)]),
    (6, "Q"): (24, [(4, 19)]),  (6, "H"): (28, [(4, 15)]),
    (7, "L"): (20, [(2, 78)]),  (7, "M"): (18, [(4, 31)]),
    (7, "Q"): (18, [(2, 14), (4, 15)]), (7, "H"): (26, [(4, 13), (1, 14)]),
    (8, "L"): (24, [(2, 97)]),  (8, "M"): (22, [(2, 38), (2, 39)]),
    (8, "Q"): (22, [(4, 18), (2, 19)]), (8, "H"): (26, [(4, 14), (2, 15)]),
    (9, "L"): (30, [(2, 116)]), (9, "M"): (22, [(3, 36), (2, 37)]),
    (9, "Q"): (20, [(4, 16), (4, 17)]), (9, "H"): (24, [(4, 12), (4, 13)]),
    (10, "L"): (18, [(2, 68), (2, 69)]), (10, "M"): (26, [(4, 43), (1, 44)]),
    (10, "Q"): (24, [(6, 19), (2, 20)]), (10, "H"): (28, [(6, 15), (2, 16)]),
}

# version -> row and column centres of the alignment patterns
ALIGNMENT = {1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30], 6: [6, 34],
             7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 50]}

ECL_BITS = {"L": 0b01, "M": 0b00, "Q": 0b11, "H": 0b10}


def _data_capacity(version, ecl):
    _ec_per_block, groups = BLOCKS[(version, ecl)]
    return sum(n * d for n, d in groups)


def _check_tables():
    """Every block table must account for exactly the codewords in the symbol."""
    for (version, ecl), (ec_per_block, groups) in BLOCKS.items():
        blocks = sum(n for n, _ in groups)
        total = sum(n * d for n, d in groups) + blocks * ec_per_block
        if total != TOTAL_CODEWORDS[version]:
            raise AssertionError(
                "block table wrong for version %d level %s: %d not %d"
                % (version, ecl, total, TOTAL_CODEWORDS[version]))


_check_tables()


# -------------------------------------------------------------------- bits
def _encode_data(text, version, ecl):
    """Mode, length, payload, terminator and pad bytes, or None if it will not fit."""
    payload = text.encode("utf-8")
    capacity_bits = _data_capacity(version, ecl) * 8
    bits = []

    def put(value, length):
        for i in range(length - 1, -1, -1):
            bits.append((value >> i) & 1)

    put(0b0100, 4)                              # byte mode
    put(len(payload), 8 if version < 10 else 16)
    for byte in payload:
        put(byte, 8)
    if len(bits) > capacity_bits:
        return None
    put(0, min(4, capacity_bits - len(bits)))   # terminator
    while len(bits) % 8:
        bits.append(0)
    words = [int("".join(str(b) for b in bits[i:i + 8]), 2)
             for i in range(0, len(bits), 8)]
    pad = (0xEC, 0x11)
    i = 0
    while len(words) < capacity_bits // 8:
        words.append(pad[i % 2])
        i += 1
    return words


def _interleave(words, version, ecl):
    ec_per_block, groups = BLOCKS[(version, ecl)]
    blocks, ec_blocks, pos = [], [], 0
    for count, size in groups:
        for _ in range(count):
            block = words[pos:pos + size]
            pos += size
            blocks.append(block)
            ec_blocks.append(_ec_codewords(block, ec_per_block))
    out = []
    for i in range(max(len(b) for b in blocks)):
        for b in blocks:
            if i < len(b):
                out.append(b[i])
    for i in range(ec_per_block):
        for b in ec_blocks:
            out.append(b[i])
    return out


# ------------------------------------------------------------------ matrix
def _blank(size):
    return [[None] * size for _ in range(size)]


def _place_finder(m, r, c):
    size = len(m)
    for dr in range(-1, 8):
        for dc in range(-1, 8):
            rr, cc = r + dr, c + dc
            if not (0 <= rr < size and 0 <= cc < size):
                continue
            ring = (dr in (0, 6) and 0 <= dc <= 6) or (dc in (0, 6) and 0 <= dr <= 6)
            core = 2 <= dr <= 4 and 2 <= dc <= 4
            m[rr][cc] = ring or core


def _place_function_patterns(m, version):
    size = len(m)
    _place_finder(m, 0, 0)
    _place_finder(m, 0, size - 7)
    _place_finder(m, size - 7, 0)
    for i in range(size):                       # timing lines
        if m[6][i] is None:
            m[6][i] = i % 2 == 0
        if m[i][6] is None:
            m[i][6] = i % 2 == 0
    centres = ALIGNMENT[version]
    if centres:
        # Only the three centres that would land on a finder pattern are dropped.
        # The ones that sit on a timing line are drawn, and win over it.
        first, last = centres[0], centres[-1]
        skip = {(first, first), (first, last), (last, first)}
        for r in centres:
            for c in centres:
                if (r, c) in skip:
                    continue
                for dr in range(-2, 3):
                    for dc in range(-2, 3):
                        m[r + dr][c + dc] = max(abs(dr), abs(dc)) != 1
    m[size - 8][8] = True                       # the always dark module
    for i in range(9):                          # reserve the format areas
        if m[8][i] is None:
            m[8][i] = False
        if m[i][8] is None:
            m[i][8] = False
    for i in range(8):
        if m[8][size - 1 - i] is None:
            m[8][size - 1 - i] = False
        if m[size - 1 - i][8] is None:
            m[size - 1 - i][8] = False
    if version >= 7:                            # reserve the version areas
        for i in range(6):
            for j in range(3):
                m[size - 11 + j][i] = False
                m[i][size - 11 + j] = False


def _reserved(version, size):
    probe = _blank(size)
    _place_function_patterns(probe, version)
    return [[probe[r][c] is not None for c in range(size)] for r in range(size)]


MASKS = [
    lambda i, j: (i + j) % 2 == 0,
    lambda i, j: i % 2 == 0,
    lambda i, j: j % 3 == 0,
    lambda i, j: (i + j) % 3 == 0,
    lambda i, j: (i // 2 + j // 3) % 2 == 0,
    lambda i, j: (i * j) % 2 + (i * j) % 3 == 0,
    lambda i, j: ((i * j) % 2 + (i * j) % 3) % 2 == 0,
    lambda i, j: ((i + j) % 2 + (i * j) % 3) % 2 == 0,
]


def _place_data(m, reserved, words):
    size = len(m)
    bits = []
    for w in words:
        for i in range(7, -1, -1):
            bits.append((w >> i) & 1)
    idx, upward, col = 0, True, size - 1
    while col > 0:
        if col == 6:
            col -= 1                            # skip the vertical timing line
        rows = range(size - 1, -1, -1) if upward else range(size)
        for row in rows:
            for c in (col, col - 1):
                if reserved[row][c]:
                    continue
                m[row][c] = bool(bits[idx]) if idx < len(bits) else False
                idx += 1
        upward = not upward
        col -= 2


def _bch(value, shift, generator, guard):
    """Long division of value shifted left, by the BCH generator polynomial."""
    rem = value << shift
    while rem.bit_length() > guard:
        rem ^= generator << (rem.bit_length() - generator.bit_length())
    return ((value << shift) | rem)


def _format_bits(ecl, mask):
    value = (ECL_BITS[ecl] << 3) | mask
    return _bch(value, 10, 0x537, 10) ^ 0x5412


def _version_bits(version):
    return _bch(version, 12, 0x1F25, 12)


def _apply_format(m, ecl, mask):
    size = len(m)
    bits = _format_bits(ecl, mask)
    # i counts from the least significant bit, so bit i is bit 14 - i of the
    # format string as the standard writes it, most significant first.
    for i in range(15):
        bit = bool((bits >> i) & 1)
        if i < 6:                    # up the column beside the top left finder
            m[i][8] = bit
        elif i == 6:
            m[7][8] = bit
        elif i == 7:
            m[8][8] = bit
        elif i == 8:
            m[8][7] = bit
        else:
            m[8][14 - i] = bit
        if i < 8:                    # the second copy, split across two corners
            m[8][size - 1 - i] = bit
        else:
            m[size - 15 + i][8] = bit


def _apply_version(m, version):
    if version < 7:
        return
    size = len(m)
    bits = _version_bits(version)
    for i in range(18):
        bit = bool((bits >> i) & 1)
        m[i // 3][size - 11 + i % 3] = bit
        m[size - 11 + i % 3][i // 3] = bit


_FINDER_RUN_A = [True, False, True, True, True, False, True,
                 False, False, False, False]
_FINDER_RUN_B = list(reversed(_FINDER_RUN_A))


def _penalty(m):
    size = len(m)
    score = 0
    columns = [[m[r][c] for r in range(size)] for c in range(size)]
    for line in list(m) + columns:
        run, prev = 1, line[0]
        for v in line[1:]:
            if v == prev:
                run += 1
            else:
                if run >= 5:
                    score += 3 + run - 5
                run, prev = 1, v
        if run >= 5:
            score += 3 + run - 5
        for i in range(size - 10):
            window = line[i:i + 11]
            if window == _FINDER_RUN_A or window == _FINDER_RUN_B:
                score += 40
    for r in range(size - 1):
        for c in range(size - 1):
            if m[r][c] == m[r][c + 1] == m[r + 1][c] == m[r + 1][c + 1]:
                score += 3
    dark = sum(1 for row in m for v in row if v)
    score += 10 * int(abs(dark * 100 / (size * size) - 50) / 5)
    return score


def encode(text, ecl="Q", version=None):
    """Return the QR matrix for text, in the smallest version that holds it."""
    if ecl not in ECL_BITS:
        raise ValueError("error correction level must be L, M, Q or H")
    words = None
    for v in ([version] if version else range(1, 11)):
        words = _encode_data(text, v, ecl)
        if words is not None:
            version = v
            break
    if words is None:
        raise ValueError("text does not fit in a version 10 level %s symbol" % ecl)
    final = _interleave(words, version, ecl)
    size = version * 4 + 17
    reserved = _reserved(version, size)
    best, best_score = None, None
    for mask in range(8):
        m = _blank(size)
        _place_function_patterns(m, version)
        _place_data(m, reserved, final)
        for r in range(size):
            for c in range(size):
                if not reserved[r][c] and MASKS[mask](r, c):
                    m[r][c] = not m[r][c]
        _apply_format(m, ecl, mask)
        _apply_version(m, version)
        score = _penalty(m)
        if best_score is None or score < best_score:
            best, best_score = m, score
    return best


def svg_path(matrix):
    """One SVG path covering every dark module, one module to the unit."""
    parts = []
    for r, row in enumerate(matrix):
        c = 0
        while c < len(row):
            if row[c]:
                start = c
                while c < len(row) and row[c]:
                    c += 1
                width = c - start
                parts.append("M%d %dh%dv1h-%dz" % (start, r, width, width))
            else:
                c += 1
    return "".join(parts)


def as_text(matrix, quiet=4):
    """The matrix as blocks, for eyeballing in a terminal."""
    size = len(matrix)
    pad = "  " * (size + quiet * 2)
    rows = [pad] * quiet
    for row in matrix:
        rows.append("  " * quiet
                    + "".join("##" if v else "  " for v in row)
                    + "  " * quiet)
    rows.extend([pad] * quiet)
    return "\n".join(rows)
