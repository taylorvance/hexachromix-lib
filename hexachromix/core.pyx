# cython: language_level=3
# cython: profile=False

import re
from typing import Tuple, Hashable
from random import choice

cimport cython


# Set up some constants.
COLORS = 'RYGCBM'

VARIANT_PLAYER_TEAM = {
    variant: {
        c: next(team for team in teams if c in team)
        for c in COLORS
    }
    for variant,teams in {
        'MRY': ['MRY','GCB'],
        'MR': ['MR','YG','CB'],
        'R': ['R','Y','G','C','B','M'],
    }.items()
}

INT2CHAR = ['-','R','Y','G','C','B','M','r','y','g','c','b','m']
CHAR2INT = {c:i for i,c in enumerate(INT2CHAR)}

cdef unsigned char[6][4][2] TRANSFORMATIONS = [
    [
        [CHAR2INT[c] for c in pair]
        for pair in group
    ]
    for group in [
        [['-','R'], ['r','R'], ['G','y'], ['B','m']],
        [['-','Y'], ['y','Y'], ['C','g'], ['M','r']],
        [['-','G'], ['g','G'], ['B','c'], ['R','y']],
        [['-','C'], ['c','C'], ['M','b'], ['Y','g']],
        [['-','B'], ['b','B'], ['R','m'], ['G','c']],
        [['-','M'], ['m','M'], ['Y','r'], ['C','b']],
    ]
]


cdef class HexachromixState:
    cdef unsigned char[19] board
    cdef unsigned char player
    cdef variant

    def __init__(self, board:list=[0]*19, player:int=0, variant:str="MRY", hfen:str=None):
        if hfen is not None:
            (boardstr, color, variant) = hfen.split()
            # Strip slashes and replace ints with dashes.
            boardstr = re.sub(r'\d', lambda x: '-'*int(x.group(0)), boardstr.replace('/',''))
            board = [CHAR2INT[c] for c in boardstr]
            player = COLORS.index(color)

        for i in range(19): self.board[i] = board[i]
        self.player = player
        self.variant = variant

    @property
    def hfen(self) -> str:
        board = [INT2CHAR[self.board[i]] for i in range(19)]
        board = '/'.join([''.join(board[i:j]) for i,j in [(0,3), (3,7), (7,12), (12,16), (16,19)]])
        board = re.sub(r'-+', lambda x: str(len(x.group(0))), board)
        return f'{board} {self.color} {self.variant}'

    @property
    def color(self) -> str: return COLORS[self.player]

    @cython.boundscheck(False)
    @cython.wraparound(False)
    cpdef get_current_team(self):
        if self.variant == "MRY":
            if self.player in [5,0,1]:
                return "MRY"
            else:
                return "GCB"
        elif self.variant == "MR":
            if self.player in [5,0]:
                return "MR"
            elif self.player in [1,2]:
                return "YG"
            else:
                return "CB"
        else:
            return COLORS[self.player]

    @cython.boundscheck(False)
    @cython.wraparound(False)
    cpdef get_legal_moves(self):
        cdef unsigned char i, j, c, n = 0
        cdef unsigned char[19][2] moves
        for i in range(19):
            c = self.board[i]
            for j in range(4):
                if c == TRANSFORMATIONS[self.player][j][0]:
                    moves[n] = [i, TRANSFORMATIONS[self.player][j][1]]
                    n += 1
                    break
        return [(moves[i][0], moves[i][1]) for i in range(n)]

    @cython.boundscheck(False)
    @cython.wraparound(False)
    cpdef HexachromixState make_move(self, (int,int) move):
        cdef unsigned char i = move[0], c = move[1]
        board = [self.board[i] for i in range(19)]
        board[i] = c
        return HexachromixState(board, (self.player+1)%6, self.variant)

    cpdef bint is_terminal(self): return self.has_path() or len(self.get_legal_moves()) == 0

    cpdef get_reward(self): return 1 if self.has_path() else 0

    cpdef bint has_path(self): return bfs((self.player-1)%6, self.board)

    cpdef Tuple[Hashable,HexachromixState] suggest_move(self):
        cdef unsigned char i
        cdef unsigned char[19] board

        moves = self.get_legal_moves()
        for move in moves:
            # Make a temp board to check for a path.
            for i in range(19): board[i] = self.board[i]
            board[move[0]] = move[1]
            if bfs(self.player, board):
                return (move, self.make_move(move))

        # If the above did not return a move, pick one at random.
        move = choice(moves)
        return (move, self.make_move(move))

    def get_result(self):
        if self.has_path():
            prev = COLORS[(self.player - 1) % 6]
            return f'{prev} {VARIANT_PLAYER_TEAM[self.variant][prev]}'
        if len(self.get_legal_moves()) == 0:
            return 'DRAW'
        return None

    def __repr__(self): return self.hfen


"""  ——  ——  ——
   / 00  01  02 \
 / 03  04  05  06 \
|07  08  09  10  11|
 \ 12  13  14  15 /
   \ 16  17  18 /
     ——  ——  ——
"""
# 255 is the sentinel value used in bfs to indicate "no more neighbors".
cdef unsigned char[19][6] ADJACENCIES = [
    [1,3,4,255],
    [0,2,4,5,255],
    [1,5,6,255],
    [0,4,7,8,255],
    [0,1,3,5,8,9],
    [1,2,4,6,9,10],
    [2,5,10,11,255],
    [3,8,12,255],
    [3,4,7,9,12,13],
    [4,5,8,10,13,14],
    [5,6,9,11,14,15],
    [6,10,15,255],
    [7,8,13,16,255],
    [8,9,12,14,16,17],
    [9,10,13,15,17,18],
    [10,11,14,18,255],
    [12,13,17,255],
    [13,14,16,18,255],
    [14,15,17,255],
]

cdef unsigned char[6][2][3] SIDES = [
    [[0,1,2], [16,17,18]],
    [[2,6,11], [7,12,16]],
    [[11,15,18], [0,3,7]],
    [[0,1,2], [16,17,18]],
    [[2,6,11], [7,12,16]],
    [[11,15,18], [0,3,7]],
]

cdef unsigned char[6][3] OCCUPANTS = [[CHAR2INT[c] for c in chars] for chars in ['mRy','rYg','yGc','gCb','cBm','bMr']]

@cython.boundscheck(False)
@cython.wraparound(False)
cdef bint bfs(unsigned char color_idx, unsigned char[19] board):
    cdef unsigned char neighbor, idx, i, n = 0
    cdef bint does_occupy
    cdef unsigned char[3] ends = SIDES[color_idx][1]
    cdef bint[19] visited = [False] * 19
    cdef unsigned char[19] frontier

    # Initialize the frontier with the three starting indices.
    (frontier[0],frontier[1],frontier[2]) = SIDES[color_idx][0]
    n = 3

    # print(f'initial frontier: {[frontier[i] for i in range(n)]}')
    while n > 0:
        # "Pop" a cell off of the frontier.
        idx = frontier[n-1]
        n -= 1

        # print(f'idx={idx}, n={n}')

        # If the color doesn't occupy this cell, skip it.
        does_occupy = False
        for i in range(3):
            if OCCUPANTS[color_idx][i] == board[idx]:
                does_occupy = True
                break
        if not does_occupy:
            continue

        # If this cell is an end cell, there is a path.
        for i in range(3):
            if idx == ends[i]:
                # print(f'PATH!\nfinal visited: {visited}\nfinal frontier: {[frontier[i] for i in range(n)]}')
                return True

        # Add this cell's neighbors to the frontier.
        if not visited[idx]:
            visited[idx] = True
            # print(f'{idx} visited.')
            for i in range(6):
                neighbor = ADJACENCIES[idx][i]
                # print(f'neighbor: {neighbor}')
                if neighbor == 255:
                    # print(f'found sentinel. no more neighbors.')
                    break
                if not visited[neighbor]:
                    frontier[n] = neighbor
                    n += 1
            # print(f'frontier: {[frontier[i] for i in range(n)]}')

    # No path found.
    # print(f'NO PATH!\nfinal visited: {visited}\nfinal frontier: {[frontier[i] for i in range(19) if visited[i]]}')
    return False
