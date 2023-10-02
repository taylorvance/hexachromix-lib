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
                        print(render_hfen(state.hfen,True), state.hfen)
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


def colorize(txt:str, c:str=None):
    COLORCODES = {'R':31, 'Y':93, 'G':32, 'C':36, 'B':34, 'M':35}
    if c in COLORCODES: return f'\033[{COLORCODES[c]}m{txt}\033[0m'
    if c is None: return ''.join(colorize(x,x.upper()) for x in txt)
    return txt

def render_hfen(hfen:str, show_indices:bool=False):
    # Pad right with emdashes.
    SPACEMAP = {k: v.ljust(2,'—') for k,v in {
        '-':'',
        'R':'R', 'Y':'Y', 'G':'G', 'C':'C', 'B':'B', 'M':'M',
        'r':'MY', 'y':'RG', 'g':'YC', 'c':'GB', 'b':'CM', 'm':'BR',
    }.items()}

    board = hfen.split(' ')[0]
    board = re.sub(r'\d', lambda x: '-'*int(x.group(0)), board).replace('/','')

    if show_indices:
        spaces = []
        for i,c in enumerate(board):
            idx = str(i).zfill(2)
            space = SPACEMAP[c]
            spaces.append(colorize(idx[0],space[0]) + colorize(idx[1],space[1]))
    else:
        spaces = [colorize(SPACEMAP[c]) for c in board]

    out = '   ' + colorize('  __'*3,'R')
    out += '\n   ' + colorize('/','M') + ' ' + '  '.join(spaces[:3]) + ' ' + colorize('\\','Y')
    out += '\n ' + colorize('/','M') + ' ' + '  '.join(spaces[3:7]) + ' ' + colorize('\\','Y')
    out += '\n|' + '  '.join(spaces[7:12]) + '|'
    out += '\n ' + colorize('\\','B') + ' ' + '  '.join(spaces[12:16]) + ' ' + colorize('/','G')
    out += '\n   ' + colorize('\\','B') + ' ' + '  '.join(spaces[16:]) + ' ' + colorize('/','G')
    out += '\n   ' + colorize('  ‾‾'*3,'C')

    return out


if __name__ == "__main__":
    main()
