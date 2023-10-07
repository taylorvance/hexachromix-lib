from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from multimcts import MCTS

from .core import HexachromixState


class MCTSParams(BaseModel):
    exploration_bias: float = 1
    rave_bias: float = 1
    max_iterations: Optional[int] = None
    max_time: Optional[float] = None

class MCTSNode(BaseModel):
    hfen: str
    visits: int
    reward: float


app = FastAPI()

@app.get("/best/", description="Analyzes the game state and returns the HFEN of the best move.")
async def get_best(hfen:str='3/4/5/4/3 R MRY', mcts_params:MCTSParams=Depends(MCTSParams)):
    try:
        mcts = MCTS(exploration_bias=mcts_params.exploration_bias, rave_bias=mcts_params.rave_bias)
        state = HexachromixState(hfen=hfen)
        state = mcts.search(state, max_iterations=mcts_params.max_iterations, max_time=mcts_params.max_time)
        return state.hfen
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/analysis/", response_model=List[MCTSNode], description="Analyzes the game state and returns information about each legal move.")
async def get_analysis(hfen:str='3/4/5/4/3 R MRY', mcts_params:MCTSParams=Depends(MCTSParams)):
    try:
        mcts = MCTS(exploration_bias=mcts_params.exploration_bias, rave_bias=mcts_params.rave_bias)
        state = HexachromixState(hfen=hfen)

        # Find the best child node.
        best = mcts.search(
            state,
            max_iterations=mcts_params.max_iterations,
            max_time=mcts_params.max_time,
            return_type='node',
        )

        # Back up to the parent, gather info about all children (best's siblings).
        parent = best.get_parent()
        children = [
            MCTSNode(
                hfen=n.get_state().hfen,
                visits=n.get_visits(),
                reward=n.get_avg_reward(),
            )
            for n in parent.get_children().values()
        ]
        # Sort by visits and reward.
        children.sort(key=lambda n:(n.visits,n.reward), reverse=True)

        return children
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=80, reload=True)
