# cython: language_level=3
# cython: profile=False

import re

cimport cython


# Set up some constants.
COLORS = "RYGCBM"

cdef int[6][13] TRANSFORMATIONS = [
    #0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12
    #-, R, Y, G, C, B, M, r, y, g, c, b, m
    [1,-1,-1, 8,-1,12,-1, 1,-1,-1,-1,-1,-1],
    [2,-1,-1,-1, 9,-1, 7,-1, 2,-1,-1,-1,-1],
    [3, 8,-1,-1,-1,10,-1,-1,-1, 3,-1,-1,-1],
    [4,-1, 9,-1,-1,-1,11,-1,-1,-1, 4,-1,-1],
    [5,12,-1,10,-1,-1,-1,-1,-1,-1,-1, 5,-1],
    [6,-1, 7,-1,11,-1,-1,-1,-1,-1,-1,-1, 6],
]

INT2CHAR = ['-','R','Y','G','C','B','M','r','y','g','c','b','m']
CHAR2INT = {c:i for i,c in enumerate(INT2CHAR)}


cdef class HexachromixState:
    cdef unsigned int[3] board
    cdef unsigned int _player
    cdef variant

    def __init__(self, board:[int,int,int]=None, player:int=0, variant:str="MRY", hfen:str=None):
        if hfen is not None:
            (board, color, variant) = hfen.split(' ')
            player = COLORS.index(color)
            # Replace ints with dashes, strip slashes, and reverse.
            board = re.sub(r'\d', lambda x: '-'*int(x.group(0)), board.replace('/',''))[::-1]
            board = [f'{CHAR2INT[c]:04b}' for c in board]
            board = [int(''.join(board[i:j]),2) for i,j in ((0,8),(8,16),(16,19))]

        if board is None: board = [0,0,0]

        for i in range(3):
            self.board[i] = board[i]
        self._player = player
        self.variant = variant

    @property
    def hfen(self) -> str:
        board = [INT2CHAR[get_cell(self.board,i)] for i in range(19)]
        board = '/'.join([''.join(board[i:j]) for i,j in [(0,3), (3,7), (7,12), (12,16), (16,19)]])
        board = re.sub(r'-+', lambda x: str(len(x.group(0))), board)
        return f'{board} {self.player} {self.variant}'

    @property
    def player(self): return COLORS[self._player]

    @cython.boundscheck(False)
    @cython.wraparound(False)
    cpdef get_current_team(self):
        if self.variant == "MRY":
            if self._player in [5,0,1]:
                return "MRY"
            else:
                return "GCB"
        elif self.variant == "MR":
            if self._player in [5,0]:
                return "MR"
            elif self._player in [1,2]:
                return "YG"
            else:
                return "CB"
        else:
            return COLORS[self._player]

    @cython.boundscheck(False)
    @cython.wraparound(False)
    cpdef get_legal_moves(self):
        cdef unsigned int i, x, n = 0
        cdef int y
        cdef unsigned int[19][2] moves
        for i in range(19):
            x = get_cell(self.board, i)
            y = TRANSFORMATIONS[self._player][x]
            if y != -1:
                moves[n] = [i,y]
                n += 1
        return [(moves[i][0],moves[i][1]) for i in range(n)]

    @cython.boundscheck(False)
    @cython.wraparound(False)
    cpdef HexachromixState make_move(self, move):
        cdef unsigned int i = move[0], x = move[1]
        cdef unsigned int[3] board
        cdef unsigned int[:] vboard = board
        for i in range(3): board[i] = self.board[i]
        set_cell(vboard, i, x)
        return HexachromixState(board, (self._player+1)%6, self.variant)

    cpdef bint is_terminal(self):
        return self.has_path() or len(self.get_legal_moves()) == 0

    cpdef int get_reward(self):
        return 1 if self.has_path() else 0

    cdef bint has_path(self):
        return bfs((self._player-1)%6, self.board)

    def get_result(self):
        if not self.is_terminal(): return None
        if self.get_reward() == 0: return 'DRAW'
        return COLORS[(self._player-1)%6]

    def __repr__(self): return self.hfen


cdef unsigned int get_cell(unsigned int[3] board, unsigned int i):
    cdef unsigned int j
    if i < 8:
        j = 0
    elif i < 16:
        j = 1
        i -= 8
    else:
        j = 2
        i -= 16
    return board[j] >> (4*i) & 0b1111
cdef void set_cell(unsigned int[:] board, unsigned int i, unsigned int x):
    cdef unsigned int j
    if i < 8:
        j = 0
    elif i < 16:
        j = 1
        i -= 8
    else:
        j = 2
        i -= 16
    board[j] = (board[j] & ~(0b1111 << (4*i))) | (x << (4*i))


"""
    -- -- --
  / 0  1  2  \
 / 3  4  5  6  \
| 7  8  9  10 11|
 \ 12 13 14 15 /
  \ 16 17 18 /
    -- -- --
"""
cdef int[19][6] ADJACENCIES = [
    [1,3,4,-1],
    [0,2,4,5,-1],
    [1,5,6,-1],
    [0,4,7,8,-1],
    [0,1,3,5,8,9],
    [1,2,4,6,9,10],
    [2,5,10,11,-1],
    [3,8,12,-1],
    [3,4,7,9,12,13],
    [4,5,8,10,13,14],
    [5,6,9,11,14,15],
    [6,10,15,-1],
    [7,8,13,16,-1],
    [8,9,12,14,16,17],
    [9,10,13,15,17,18],
    [10,11,14,18,-1],
    [12,13,17,-1],
    [13,14,16,18,-1],
    [14,15,17,-1],
]

cdef unsigned int[6][2][3] SIDES = [
    [[0,1,2], [16,17,18]],
    [[2,6,11], [7,12,16]],
    [[11,15,18], [0,3,7]],
    [[0,1,2], [16,17,18]],
    [[2,6,11], [7,12,16]],
    [[11,15,18], [0,3,7]],
]

cdef unsigned int[6][3] OCCUPANTS = [[CHAR2INT[c] for c in chars] for chars in ['mRy','rYg','yGc','gCb','cBm','bMr']]

@cython.boundscheck(False)
@cython.wraparound(False)
cdef bint bfs(unsigned int color_idx, unsigned int[3] board):
    cdef int neighbor
    cdef unsigned int idx, i, j
    cdef bint does_occupy
    cdef unsigned int[3] ends = SIDES[color_idx][1]
    cdef bint[19] visited = [False] * 19

    # Initialize the frontier with the three starting indices.
    cdef unsigned int[19] frontier
    (frontier[0],frontier[1],frontier[2]) = SIDES[color_idx][0]
    cdef unsigned int n = 3

    while n > 0:
        # "Pop" a cell off of the frontier.
        idx = frontier[n-1]
        n -= 1

        # If the color doesn't occupy this cell, skip it.
        does_occupy = False
        for i in range(3):
            if OCCUPANTS[color_idx][i] == get_cell(board, idx):
                does_occupy = True
                break
        if not does_occupy:
            continue

        # If this cell is an end cell, there is a path.
        for i in range(3):
            if idx == ends[i]:
                return True

        # Add this cell's neighbors to the frontier.
        if not visited[idx]:
            visited[idx] = True
            for i in range(6):
                neighbor = ADJACENCIES[idx][i]
                if neighbor == -1:
                    break
                if not visited[neighbor]:
                    frontier[n] = neighbor
                    n += 1

    # No path found.
    return False


def render_hfen(hfen):
    CHAR2COLORS = {
        '-':'-',
        'R':'R', 'Y':'Y', 'G':'G', 'C':'C', 'B':'B', 'M':'M',
        'r':'MY', 'y':'RG', 'g':'YC', 'c':'GB', 'b':'CM', 'm':'BR',
    }
    board = hfen.split(' ')[0]
    board = re.sub(r'\d', lambda x: '-'*int(x.group(0)), board).replace('/','')
    spaces = [''.join(colorize(x,x) for x in CHAR2COLORS[c].ljust(2,'-')) for c in board]
    out = '    ' + colorize('R', '-- -- --')
    out += '\n  ' + colorize('M', '/') + ' ' + ' '.join(spaces[:3]) + ' ' + colorize('Y', '\\')
    out += '\n ' + colorize('M', '/') + ' ' + ' '.join(spaces[3:7]) + ' ' + colorize('Y', '\\')
    out += '\n| ' + ' '.join(spaces[7:12]) + '|'
    out += '\n ' + colorize('B', '\\') + ' ' + ' '.join(spaces[12:16]) + ' ' + colorize('G', '/')
    out += '\n  ' + colorize('B', '\\') + ' ' + ' '.join(spaces[16:]) + ' ' + colorize('G', '/')
    out += '\n    ' + colorize('C', '-- -- --')
    return out

def colorize(c, txt):
    COLORCODES = {'R':'\033[31m', 'Y':'\033[93m', 'G':'\033[32m', 'C':'\033[36m', 'B':'\033[34m', 'M':'\033[35m'}
    return f'{COLORCODES[c]}{txt}\033[0m' if c in COLORCODES else txt
