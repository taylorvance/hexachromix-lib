from copy import deepcopy
from functools import reduce
from collections import defaultdict, deque
from queue import Queue, PriorityQueue
import random
import re
from time import time

import cProfile
import pstats

from multimcts import MCTS, GameState

# https://www.redblobgames.com/grids/hexagons/


COLORS = "RYGCBM"
RED = 1 << 0
YELLOW = 1 << 1
GREEN = 1 << 2
CYAN = 1 << 3
BLUE = 1 << 4
MAGENTA = 1 << 5

PLAYS = [
    {'-':'R', 'r':'R', 'B':'m', 'G':'y'},
    {'-':'Y', 'y':'Y', 'M':'r', 'C':'g'},
    {'-':'G', 'g':'G', 'R':'y', 'B':'c'},
    {'-':'C', 'c':'C', 'Y':'g', 'M':'b'},
    {'-':'B', 'b':'B', 'G':'c', 'R':'m'},
    {'-':'M', 'm':'M', 'C':'b', 'Y':'r'},
]

OCCUPANTS = [
    'mRy',
    'rYg',
    'yGc',
    'gCb',
    'cBm',
    'bMr',
]


class HexachromixState(GameState):
    def __init__(self, board:list=['-']*19, player:int=0, variant:str="MRY"):
        self.board = board

        # RYGCBM := 012345
        self.player = player % 6
        self.prev_player = (self.player - 1) % 6

        self.variant = variant

    def get_current_team(self):
        if self.variant == "MRY":
            return "MRY" if self.player in [5,0,1] else "GCB"
        elif self.variant == "MR":
            if self.player in [5,0]:
                return "MR"
            elif self.player in [1,2]:
                return "YG"
            else:
                return "CB"
        else:
            return COLORS[self.player]

    def get_legal_moves(self):
        moves = []
        board = list(self.board)
        plays_set = set(PLAYS[self.player].keys())
        for i, c in enumerate(self.board):
            if c in plays_set:
                # moves.append(self.board[:i] + PLAYS[self.player][c] + self.board[i+1:])
                # continue
                b = list(self.board)
                b[i] = PLAYS[self.player][c]
                moves.append(b)
        return moves

    def make_move(self, move):
        return HexachromixState(move, self.player+1, self.variant)

    def is_terminal(self):
        return self.has_path(self.prev_player) or len(self.get_legal_moves()) == 0

    def get_reward(self):
        # reward a winner and slightly punish a CAT causer
        return 1 if self.has_path(self.prev_player) else -0.5

    def has_path(self, color_idx):
        starts, ends = SIDES[color_idx]
        return bfs(starts, ends, self.board, OCCUPANTS[color_idx])

    def render(self):
        CHAR2COLORS = {
            '-':'-',
            'R':'R',
            'Y':'Y',
            'G':'G',
            'C':'C',
            'B':'B',
            'M':'M',
            'r':'MY',
            'y':'RG',
            'g':'YC',
            'c':'GB',
            'b':'CM',
            'm':'BR',
        }

        spaces = [''.join(colorize(x,x) for x in CHAR2COLORS[c].ljust(2)) for c in self.board]

        out = '    ' + colorize('R', '-- -- --')
        out += '\n  ' + colorize('M', '/') + ' ' + ' '.join(spaces[:3]) + ' ' + colorize('Y', '\\')
        out += '\n ' + colorize('M', '/') + ' ' + ' '.join(spaces[3:7]) + ' ' + colorize('Y', '\\')
        out += '\n| ' + ' '.join(spaces[7:12]) + '|'
        out += '\n ' + colorize('B', '\\') + ' ' + ' '.join(spaces[12:16]) + ' ' + colorize('G', '/')
        out += '\n  ' + colorize('B', '\\') + ' ' + ' '.join(spaces[16:]) + ' ' + colorize('G', '/')
        out += '\n    ' + colorize('C', '-- -- --')

        return out

    def get_hfen(self):
        board = '/'.join([''.join(self.board[i:j]) for i,j in [(0,3), (3,7), (7,12), (12,16), (16,19)]])
        board = re.sub(r'-+', lambda m: str(len(m.group())), board)
        return f'{board} {COLORS[self.player]} {self.variant}'

    def __repr__(self):
        return self.get_hfen()


"""
    -- -- --
  / 0  1  2  \
 / 3  4  5  6  \
| 7  8  9  10 11|
 \ 12 13 14 15 /
  \ 16 17 18 /
    -- -- --
"""
ADJACENCIES = [
    [1,3,4],
    [0,2,4,5],
    [1,5,6],
    [0,4,7,8],
    [0,1,3,5,8,9],
    [1,2,4,6,9,10],
    [2,5,10,11],
    [3,8,12],
    [3,4,7,9,12,13],
    [4,5,8,10,13,14],
    [5,6,9,11,14,15],
    [6,10,15],
    [7,8,13,16],
    [8,9,12,14,16,17],
    [9,10,13,15,17,18],
    [10,11,14,18],
    [12,13,17],
    [13,14,16,18],
    [14,15,17],
]

SIDES = [
    ((0,1,2), (16,17,18)), # R
    ((2,6,11), (7,12,16)), # Y
    ((11,15,18), (0,3,7)), # G
    ((0,1,2), (16,17,18)), # C
    ((2,6,11), (7,12,16)), # B
    ((11,15,18), (0,3,7)), # M
]

def bfs(start_idxs, end_idxs, board, chars):
    q = deque(start_idxs)
    visited = [False] * len(ADJACENCIES)
    while q:
        cur_idx = q.popleft()
        if cur_idx in end_idxs and board[cur_idx] in chars:
            return True
        if not visited[cur_idx] and board[cur_idx] in chars:
            visited[cur_idx] = True
            neighbours = ADJACENCIES[cur_idx]
            for neighbour in neighbours:
                if not visited[neighbour]:
                    q.append(neighbour)
    return False


COLORCODES = {
    'R': '\033[31m',
    'Y': '\033[93m',
    'G': '\033[32m',
    'C': '\033[36m',
    'B': '\033[34m',
    'M': '\033[35m',
}
def colorize(c, thing):
    if c not in COLORCODES:
        return thing
    return f"{COLORCODES[c]}{thing}\033[0m"


def sim():
    t = time()
    mcts = MCTS()
    state = HexachromixState()
    iterations = 10
    i = 0
    while not state.is_terminal():
        print(state.render(), state)
        state = mcts.search(state, max_iterations=iterations)
        i += 1
    print(state.render(), state)
    t = time() - t
    print()
    print(f'{i} turns')
    print(f'avg {round(t*1000/i/iterations, 3)} ms per move per iteration ({round(t*1000)}/{i}/{iterations})')
    print()

if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()

    # for move in HexachromixState().get_legal_moves(): print(move)
    sim()

    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('tottime')
    stats.print_stats(20)
