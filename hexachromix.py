import re

from multimcts import MCTS, GameState


# Set up some constants.
COLORS = "RYGCBM"

CHAR2INT = {'-': 0}
CHAR2INT.update({c:1<<i for i,c in enumerate(COLORS)})
CHAR2INT.update({c.lower(): CHAR2INT[COLORS[i-1]] | CHAR2INT[COLORS[(i+1)%6]] for i,c in enumerate(COLORS)})

INT2CHAR = {v:k for k,v in CHAR2INT.items()}

COLOR_PLAYS = tuple({
    0: CHAR2INT[c],
    CHAR2INT[c.lower()]: CHAR2INT[c],
    CHAR2INT[COLORS[i-2]]: CHAR2INT[COLORS[i-1].lower()],
    CHAR2INT[COLORS[(i+2)%6]]: CHAR2INT[COLORS[(i+1)%6].lower()],
} for i,c in enumerate(COLORS))


class HexachromixState(GameState):
    def __init__(self, board:int=0, player:int=0, variant:str="MRY", hfen:str=None):
        if hfen is not None:
            self.load_hfen(hfen)
        else:
            self.board = board
            self.player = player % 6
            self.variant = variant

    def load_hfen(self, hfen:str):
        (board, color, variant) = hfen.split(' ')
        board = re.sub(r'\d', lambda x: '-'*int(x.group(0)), board.replace('/',''))[::-1]
        board = int(''.join(f'{CHAR2INT[c]:06b}' for c in board), 2)
        self.board = board
        self.player = COLORS.index(color)
        self.variant = variant

    @property
    def hfen(self) -> str:
        board = [INT2CHAR[get_cell(self.board,i)] for i in range(19)]
        board = '/'.join([''.join(board[i:j]) for i,j in [(0,3), (3,7), (7,12), (12,16), (16,19)]])
        board = re.sub(r'-+', lambda x: str(len(x.group(0))), board)
        return f'{board} {COLORS[self.player]} {self.variant}'

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
        plays = COLOR_PLAYS[self.player]
        moves = []
        for i in range(19):
            x = get_cell(self.board, i)
            if x in plays:
                moves.append((i, plays[x]))
        return moves

    def make_move(self, move): return HexachromixState(set_cell(self.board,move[0],move[1]), self.player+1, self.variant)

    def is_terminal(self): return self.has_path() or len(self.get_legal_moves()) == 0

    def get_reward(self): return 1 if self.has_path() else 0

    def has_path(self): return bfs(self.player-1, self.board)

    def render(self): return render_hfen(self.hfen)

    def __repr__(self): return self.hfen


def get_cell(board:int, i:int) -> int:
    return (board >> (6*i)) & 0b111111
def set_cell(board:int, i:int, x:int):
    return (board & ~(0b111111 << (6*i))) | (x << (6*i))


"""
    -- -- --
  / 0  1  2  \
 / 3  4  5  6  \
| 7  8  9  10 11|
 \ 12 13 14 15 /
  \ 16 17 18 /
    -- -- --
"""
ADJACENCIES = (
    {1,3,4},
    {0,2,4,5},
    {1,5,6},
    {0,4,7,8},
    {0,1,3,5,8,9},
    {1,2,4,6,9,10},
    {2,5,10,11},
    {3,8,12},
    {3,4,7,9,12,13},
    {4,5,8,10,13,14},
    {5,6,9,11,14,15},
    {6,10,15},
    {7,8,13,16},
    {8,9,12,14,16,17},
    {9,10,13,15,17,18},
    {10,11,14,18},
    {12,13,17},
    {13,14,16,18},
    {14,15,17},
)

SIDES = (
    ({0,1,2}, {16,17,18}),
    ({2,6,11}, {7,12,16}),
    ({11,15,18}, {0,3,7}),
    ({0,1,2}, {16,17,18}),
    ({2,6,11}, {7,12,16}),
    ({11,15,18}, {0,3,7}),
)

OCCUPANTS = tuple({CHAR2INT[c] for c in chars} for chars in ('mRy','rYg','yGc','gCb','cBm','bMr'))

def bfs(color_idx, board):
    start_idxs, end_idxs = SIDES[color_idx]
    occupants = OCCUPANTS[color_idx]
    visited = [False] * len(ADJACENCIES)
    q = [i for i in start_idxs if get_cell(board,i) in occupants]
    while len(q) > 0:
        idx = q.pop()
        does_occupy = get_cell(board,idx) in occupants
        if idx in end_idxs and does_occupy:
            return True
        if not visited[idx] and does_occupy:
            visited[idx] = True
            neighbours = ADJACENCIES[idx]
            for neighbour in neighbours:
                if not visited[neighbour]:
                    q.append(neighbour)
    return False


def colorize(c, txt):
    COLORCODES = {'R':'\033[31m', 'Y':'\033[93m', 'G':'\033[32m', 'C':'\033[36m', 'B':'\033[34m', 'M':'\033[35m'}
    return f'{COLORCODES[c]}{txt}\033[0m' if c in COLORCODES else txt

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


def params_v_params(params1:tuple, params2:tuple, max_time:float):
    mcts1 = MCTS(exploration_bias=params1[0], rave_bias=params1[1])
    mcts2 = MCTS(exploration_bias=params2[0], rave_bias=params2[1])
    state = HexachromixState()
    terminal_team = state.get_current_team()
    while not state.is_terminal():
        terminal_team = state.get_current_team()
        mcts = mcts1 if terminal_team=='MRY' else mcts2
        state = mcts.search(state, max_time=max_time)
    if state.get_reward() == 0:
        return None
    return params1 if terminal_team=='MRY' else params2

def tune():
    import numpy as np

    # Initialize a population of agents with random parameters
    population_size = 5
    exploration_biases = np.random.uniform(0.0, 2.0, population_size)
    rave_biases = np.random.uniform(0.0, 1.0, population_size)

    # Combine the biases into parameter tuples for each agent
    parameters = list(zip(exploration_biases, rave_biases))

    # How many generations to run
    num_generations = 2

    for generation in range(num_generations):
        # Have each agent play against each other agent
        wins = [0] * population_size
        for i in range(population_size):
            for j in range(i + 1, population_size):
                winner = params_v_params(parameters[i], parameters[j], 0.1)
                if winner == parameters[i]:
                    wins[i] += 1
                elif winner == parameters[j]:
                    wins[j] += 1

        # Select the top performers
        top_performers = np.argsort(wins)[-population_size//2:]

        # Breed new parameters for the next generation
        for i in range(population_size):
            if i not in top_performers:
                # Choose two parents at random from the top performers
                parent1, parent2 = np.random.choice(top_performers, 2)

                # Breed new parameters by averaging the parent parameters
                exploration_biases[i] = (exploration_biases[parent1] + exploration_biases[parent2]) / 2
                rave_biases[i] = (rave_biases[parent1] + rave_biases[parent2]) / 2

                # Optionally, add some mutation (random variation)
                exploration_biases[i] += np.random.normal(0, 0.1)
                rave_biases[i] += np.random.normal(0, 0.05)

        # Update the parameter tuples for each agent
        parameters = list(zip(exploration_biases, rave_biases))

def sim():
    m0 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    t0 = time()
    mcts = MCTS(exploration_bias=1.414, rave_bias=1.414)
    state = HexachromixState()
    print(state.hfen)
    iterations = 100
    i = 0
    while not state.is_terminal():
        state = mcts.search(state, max_iterations=iterations)
        print(state.render(), state.hfen)
        print(f'{COLORS[state.player-1]} has path?', state.has_path())
        print(f'{COLORS[state.player]} has move?', len(state.get_legal_moves()))
        i += 1
        print(f'mem = {(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss - m0) / (1024**2)} MB', )
    t = time() - t0
    print()
    print(f'{i} turns')
    if i != 0:
        print(f'avg {round(t*1000/i/iterations, 3)} ms per turn per iteration ({round(t*1000)}/{i}/{iterations})')
    print()

def play(hfen=None):
    state = HexachromixState(hfen=hfen)
    while not state.is_terminal():
        print(state.render(), state.hfen)
        if state.get_current_team() != 'MRY':
            state = MCTS(exploration_bias=1.414, rave_bias=1.414).search(state, max_time=1)
        else:
            moves = state.get_legal_moves()
            while True:
                try:
                    idx = int(input(f'Choose an index {[i for i,c in moves]}: '))
                    move = None
                    for m in moves:
                        if idx == m[0]:
                            move = m
                            break
                    if move is None:
                        raise ValueError
                    state = state.make_move(move)
                    break
                except KeyboardInterrupt: exit()
                except: pass
    print(state.render(), state.hfen)

def agent_v_agent(mcts1:MCTS, mcts2:MCTS):
    m0 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    t0 = time()
    state = HexachromixState()
    print(state.hfen)
    iterations = 10
    i = 0
    while not state.is_terminal():
        mcts = {'MRY':mcts1, 'GCB':mcts2}[state.get_current_team()]
        state = mcts.search(state, max_iterations=iterations)
        print(state.render(), state.hfen)
        print(f'{COLORS[state.player-1]} has path?', state.has_path())
        print(f'{COLORS[state.player]} has move?', len(state.get_legal_moves()))
        i += 1
        print(f'mem = {(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss - m0) / (1024**2)} MB', )
    t = time() - t0
    print()
    print(f'{i} turns')
    if i != 0:
        print(f'avg {round(t*1000/i/iterations, 3)} ms per move per iteration ({round(t*1000)}/{i}/{iterations})')
    print()

def best_move(hfen=None):
    m0 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    t0 = time()
    mcts = MCTS()
    state = HexachromixState(hfen=hfen)
    print(state.render(), state.hfen)
    move = mcts.search(state, max_time=1, return_type='move')
    print('best:', move[0], INT2CHAR[move[1]])
    state = state.make_move(move)
    print(state.render(), state.hfen)
    print(f'{(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss - m0) / (1024**2)} MB', )
    print(f'{round(time()-t0,3)} seconds')

def node_stuff(hfen=None, node=None):
    rave_bias = 1.414
    if hfen:
        node = MCTS(1.414, rave_bias).search(HexachromixState(hfen=hfen), max_time=0.01, return_type='node').get_parent()
    state = node.get_state()
    print(state.render(), state.hfen)
    print('move', node.get_move() if node.get_parent() else 'n/a')
    print('team', node.get_team())
    print('visits', node.get_visits())
    print('rave visits', node.get_rave_visits())
    print('rewards', node.get_rewards())
    print('rave rewards', node.get_rave_rewards())
    print('avg reward', round(node.get_rewards()[node.get_team()] / node.get_visits(), 3))
    print('avg rave reward', round(node.get_rave_rewards()[node.get_team()] / node.get_rave_visits(), 3))
    print('ucb', node.ucb(1.414) if node.get_parent() else 'n/a')
    print('raveBeta', node.rave_beta(rave_bias))
    print('score', node.score(1.414,rave_bias) if node.get_parent() else 'n/a')
    children = [(move,child) for move,child in node.get_children().items()]
    children = sorted(children, key=lambda x:x[1].score(1.414,rave_bias), reverse=True)
    for i,pair in enumerate(children):
        (move, child) = pair
        if i < 5: print(child.get_state().render(), child.get_state().hfen)
        print(f'  {move} | ucb={round(child.ucb(1.414),3)} | raveBeta={round(child.rave_beta(rave_bias),3)} | score={round(child.score(1.414,rave_bias),3)} | visits={child.get_visits()} | rave visits={child.get_rave_visits()} | rewards={child.get_rewards()} | rave rewards={child.get_rave_rewards()}')


if __name__ == "__main__":
    from time import time
    import cProfile
    import pstats
    import resource

    profiler = cProfile.Profile()
    profiler.enable()

    # node_stuff('3/4/5/4/3 R MRY')
    # node_stuff('GGG/Mcbc/rRgYY/rmRc/mCr C MRY')
    sim()
    # play()
    # agent_v_agent(MCTS(1.414, 0.0), MCTS(1.414, 1.414))
    # paramses = ((1.414,0), (1.414,2))
    # for _ in range(10):
        # print(f'{paramses[0]} v {paramses[1]} = {params_v_params(paramses[0],paramses[1],0.1)}')
        # print(f'{paramses[1]} v {paramses[0]} = {params_v_params(paramses[1],paramses[0],0.1)}')
        # print()
    # for _ in range(10): best_move('GGG/Mcbc/rRgYY/rmRc/mCr C MRY')
    '''
    hfen = 'bbm/YbmC/bMmrY/gmyG/rcy Y MRY'
    state = HexachromixState(hfen=hfen)
    print(state.render(), state.hfen)
    print(f'{COLORS[state.player-1]} has path?', state.has_path())
    print(f'{COLORS[state.player]} has move?', len(state.get_legal_moves()))
    '''

    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('tottime')
    stats.print_stats(20)
