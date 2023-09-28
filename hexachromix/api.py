from fastapi import FastAPI
from multimcts import MCTS

from .gamestate import HexachromixState

app = FastAPI()

@app.get("/best_move/")
async def get_best_move(hfen:str):
    mcts = MCTS(exploration_bias=0.5, rave_bias=1.5)
    state = HexachromixState(hfen=hfen)
    state = mcts.search(state, max_time=1)
    return state.hfen
