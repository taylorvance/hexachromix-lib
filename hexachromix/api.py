from fastapi import FastAPI
from multimcts import MCTS

from .core import HexachromixState

app = FastAPI()

@app.get("/best_move/")
async def get_best_move(hfen:str='3/4/5/4/3 R MRY', exploration_bias:float=0.5, rave_bias:float=1.5, max_iterations:int=10000, max_time:float=1):
    mcts = MCTS(exploration_bias=exploration_bias, rave_bias=rave_bias)
    state = HexachromixState(hfen=hfen)
    state = mcts.search(state, max_iterations=max_iterations, max_time=max_time)
    return state.hfen


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=80, reload=True)
