import argparse
import time
import resource
import re

from multimcts import MCTS
from .core import HexachromixState


def main():
    allargs = {
        'profile': {'action':'store_true', 'help':'Enable profiling for performance analysis.'},
        'hfen': {'type':str, 'help':'Starting game state. Default "3/4/5/4/3 R MRY".'},
        'variant': {'choices':['MRY','MR','R'], 'help':'Hexachromix variant. Ignored if hfen is provided.', 'default':'MRY'},
        'exploration-bias': {'type':float, 'help':'MCTS exploration bias. Default sqrt(2).', 'default':1.414},
        'rave-bias': {'type':float, 'help':'MCTS RAVE bias. Default 0.', 'default':0},
        'pruning-bias': {'type':float, 'help':'MCTS pruning bias. Default 0.', 'default':0},
        'max-iterations': {'type':int, 'help':'Number of MCTS simulations to perform per move.'},
        'max-time': {'type':float, 'help':'Time (seconds) that MCTS will search per move.'},
        'colors': {'type':str, 'help':'Player colors, a string containing any of RYGCBM.'},
        'eb1': {'type':float, 'help':'Exploration bias of the first MCTS agent.'},
        'rb1': {'type':float, 'help':'RAVE bias of the first MCTS agent.'},
        'pb1': {'type':float, 'help':'Pruning bias of the first MCTS agent.'},
        'eb2': {'type':float, 'help':'Exploration bias of the second MCTS agent.'},
        'rb2': {'type':float, 'help':'RAVE bias of the second MCTS agent.'},
        'pb2': {'type':float, 'help':'Pruning bias of the second MCTS agent.'},
    }
    def add_args(parser:argparse.ArgumentParser, argnames:list):
        for argname in argnames:
            parser.add_argument('--'+argname, **allargs[argname])

    parser = argparse.ArgumentParser(description='Hexachromix MCTS Interface')
    subparsers = parser.add_subparsers(dest='command', help='Sub-command help')

    add_args(subparsers.add_parser('sim', help='Simulate a game using MCTS.'), ['profile','variant','hfen','exploration-bias','rave-bias','pruning-bias','max-iterations','max-time'])
    add_args(subparsers.add_parser('sim2', help='Simulate a game between two MCTS agents.'), ['profile','hfen','eb1','rb1','pb1','eb2','rb2','pb2','max-iterations','max-time'])
    add_args(subparsers.add_parser('play', help='Play a game against MCTS AI.'), ['profile','variant','hfen','exploration-bias','rave-bias','pruning-bias','max-iterations','max-time','colors'])
    add_args(subparsers.add_parser('best', help='Find the best move from a given position.'), ['profile','variant','hfen','exploration-bias','rave-bias','pruning-bias','max-iterations','max-time'])
    add_args(subparsers.add_parser('tree', help='Visualize the MCTS tree.'), ['profile','variant','hfen','exploration-bias','rave-bias','pruning-bias','max-iterations','max-time'])
    add_args(subparsers.add_parser('moves', help='Get legal moves from a given position.'), ['profile','hfen','variant'])

    args = parser.parse_args()

    if args.hfen:
        hfen = args.hfen
    else:
        try: hfen = '3/4/5/4/3 R ' + args.variant
        except: hfen = '3/4/5/4/3 R MRY'
    eb = getattr(args,'exploration_bias',1.414)
    rb = getattr(args,'rave_bias',0)
    pb = getattr(args,'pruning_bias',0)
    max_iterations = getattr(args,'max_iterations',None)
    max_time = getattr(args,'max_time',None)

    if args.profile:
        import cProfile
        import pstats
        profiler = cProfile.Profile()
        profiler.enable()

    if args.command == "sim":
        import psutil
        t0 = time.time()
        m0 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024**2)
        def maxmem(): return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024**2)
        mcts = MCTS(eb,rb,pb)
        state = HexachromixState(hfen=hfen)
        print(render_hfen(state.hfen), state.hfen)
        n = 0
        while not state.is_terminal():
            state = mcts.search(state, max_iterations=max_iterations, max_time=max_time)
            print(render_hfen(state.hfen), state.hfen)
            n += 1
        print(f'\nresult={state.get_result()}')
        t = time.time() - t0
        print(f'\n{n} turns')
        print(f'{t:.3f} seconds')
        print(f'{maxmem()-m0:.3f} MB')
        if n and max_iterations and not max_time: print(f'avg {t*1000/n/max_iterations:.3f} ms per turn per iteration ({round(t*1000)}/{n}/{max_iterations})')
    elif args.command == "sim2":
        import psutil
        mcts1 = MCTS(args.eb1, args.rb1, args.pb1)
        mcts2 = MCTS(args.eb2, args.rb2, args.pb2)
        # mcts3 = MCTS(args.eb3, args.rb3)
        state = HexachromixState(hfen=hfen)
        print(render_hfen(state.hfen), state.hfen)
        while not state.is_terminal():
            mcts = {'MRY':mcts1,'GCB':mcts2}[state.get_current_team()]
            state = mcts.search(state, max_iterations=max_iterations, max_time=max_time)
            print(render_hfen(state.hfen), state.hfen)
        print(f'\nresult={state.get_result()}')
    elif args.command == "play":
        mcts = MCTS(eb,rb,pb)
        state = HexachromixState(hfen=hfen)
        print(render_hfen(state.hfen), state.hfen)
        while not state.is_terminal():
            if state.color not in args.colors:
                state = mcts.search(state, max_iterations=max_iterations, max_time=max_time)
            else:
                moves = state.get_legal_moves()
                while True:
                    try:
                        print(render_hfen(state.hfen,True,True), state.hfen)
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
            print(render_hfen(state.hfen), state.hfen)
        print(state.get_result())
    elif args.command == "best":
        state = HexachromixState(hfen=hfen)
        print(render_hfen(state.hfen), state.hfen)
        state = MCTS(eb,rb,pb).search(state, max_iterations=max_iterations, max_time=max_time)
        print(render_hfen(state.hfen), state.hfen)
    elif args.command == "tree":
        node = MCTS(eb,rb,pb).search(HexachromixState(hfen=hfen), max_iterations=max_iterations, max_time=max_time, return_type='node').get_parent()
        state = node.get_state()
        print(render_hfen(state.hfen), state.hfen)
        print(f'visits:rave={node.get_visits()}:{node.get_rave_visits()} | avg:rave={node.get_avg_reward():.1f}:{node.get_avg_rave_reward():.1f}')
        children = [(move,child) for move,child in node.get_children().items()]
        children = sorted(children, key=lambda x:x[1].score(eb,rb), reverse=True)
        for i,pair in enumerate(children):
            (move, child) = pair
            if i < 3: print(render_hfen(child.get_state().hfen), child.get_state().hfen)
            print(f'  {move} | visits:rave={child.get_visits()}:{child.get_rave_visits()} | avg:rave={child.get_avg_reward():.3f}:{child.get_avg_rave_reward():.3f} | score={child.score(eb,rb):.3f} | uncertainty={child.uncertainty(eb):.3f}')
    elif args.command == "moves":
        state = HexachromixState(hfen=hfen)
        for move in state.get_legal_moves():
            print(state.make_move(move).hfen)
    else:
        print("Unknown command. Use --help for guidance.")

    if args.profile:
        profiler.disable()
        stats = pstats.Stats(profiler).sort_stats('tottime')
        stats.print_stats(20)


def colorize(txt:str, color=None):
    FG = {'R':31, 'Y':93, 'G':32, 'C':36, 'B':34, 'M':35}
    if color in FG: return f'\033[{FG[color]}m{txt}\033[39m'
    if color is None: return ''.join(colorize(x,x.upper()) for x in txt)
    return txt
def emphasize(txt:str, effect:str):
    BG = {'R':41, 'Y':43, 'G':42, 'C':46, 'B':44, 'M':45}
    if effect in BG: return f'\033[{BG[effect]}m{txt}\033[49m'
    if effect == 'bold': return f'\033[1m{txt}\033[22m'
    if effect == 'invert': return f'\033[7m{txt}\033[27m'
    return txt

def render_hfen(hfen:str, highlight_moves:bool=False, show_indices:bool=False):
    # Replace the character with the occupying color(s), and pad right with emdashes.
    SPACEMAP = {k:v.ljust(2,'—') for k,v in {
        '-':'',
        'R':'R', 'Y':'Y', 'G':'G', 'C':'C', 'B':'B', 'M':'M',
        'r':'MY', 'y':'RG', 'g':'YC', 'c':'GB', 'b':'CM', 'm':'BR',
    }.items()}

    (board, color, _) = hfen.split()
    board = re.sub(r'\d', lambda x: '-'*int(x.group(0)), board).replace('/','')

    def can_play(color, c):
        return (color=='R' and c in '-rBG') or (color=='Y' and c in '-yMC') or (color=='G' and c in '-gRB') or (color=='C' and c in '-cYM') or (color=='B' and c in '-bGR') or (color=='M' and c in '-mCY')

    spaces = []
    if show_indices:
        for i,c in enumerate(board):
            idx = str(i).zfill(2)
            space = SPACEMAP[c]
            space = colorize(idx[0],space[0]) + colorize(idx[1],space[1])
            if highlight_moves and can_play(color,c):
                space = emphasize(space,color)
            spaces.append(space)
    else:
        for c in board:
            space = colorize(SPACEMAP[c])
            if highlight_moves and can_play(color,c):
                space = emphasize(space,color)
            spaces.append(space)

    def js(start,end):
        # Join spaces.
        return '  '.join(spaces[start:end])

    # "border" constants
    bR = colorize('  ——'*3,'R')
    bY = colorize('\\','Y')
    bG = colorize('/','G')
    bC = colorize('  ——'*3,'C')
    bB = colorize('\\','B')
    bM = colorize('/','M')

    return '\n'.join([
        f'   {bR}',
        f'   {bM} {js(0,3)} {bY}',
        f' {bM} {js(3,7)} {bY}',
        f'|{js(7,12)}|',
        f' {bB} {js(12,16)} {bG}',
        f'   {bB} {js(16,19)} {bG}',
        f'   {bC}',
    ])


if __name__ == "__main__":
    main()
