import logging
from typing import Any, TypedDict
from langgraph.graph import END, StateGraph

logger = logging.getLogger(__name__)


class PipelineState(TypedDict):
    campaign_id: str
    product_name: str
    product_url: str
    product_price: str
    avatar: dict
    angle: str
    awareness_stage: int
    emotional_driver: str
    platforms: list
    copy_model: str
    use_local_models: bool
    research_output: dict
    strategy_output: dict
    copy_output: dict
    creative_brief_output: dict
    image_output: dict
    qa_output: dict
    status: str


def _merge(state: PipelineState, updates: dict) -> PipelineState:
    """Return a new state dict with updates merged in."""
    return {**state, **updates}


async def research_node(state: PipelineState) -> PipelineState:
    from agents.research_agent import run_research
    logger.info("=== Research Agent running ===")
    research_output = await run_research(state)
    return _merge(state, {"research_output": research_output})


async def strategy_node(state: PipelineState) -> PipelineState:
    from agents.strategy_agent import run_strategy
    logger.info("=== Strategy Agent running ===")
    strategy_output = await run_strategy(state)
    return _merge(state, {"strategy_output": strategy_output})


async def copy_node(state: PipelineState) -> PipelineState:
    from agents.copy_agent import run_copy
    logger.info("=== Copy Agent running ===")
    copy_output = await run_copy(state)
    return _merge(state, {"copy_output": copy_output})


async def creative_brief_node(state: PipelineState) -> PipelineState:
    from agents.creative_brief_agent import run_creative_brief
    logger.info("=== Creative Brief Agent running ===")
    creative_brief_output = await run_creative_brief(state)
    return _merge(state, {"creative_brief_output": creative_brief_output})


async def image_gen_node(state: PipelineState) -> PipelineState:
    from agents.image_gen_agent import run_image_gen
    logger.info("=== Image Gen Agent running ===")
    image_output = await run_image_gen(state)
    return _merge(state, {"image_output": image_output})


async def qa_node(state: PipelineState) -> PipelineState:
    from agents.qa_agent import run_qa
    logger.info("=== QA Agent running ===")
    qa_output = await run_qa(state)
    return _merge(state, {"qa_output": qa_output, "status": "complete"})


# Build the graph
def build_graph() -> StateGraph:
    graph = StateGraph(PipelineState)

    graph.add_node("research", research_node)
    graph.add_node("strategy", strategy_node)
    graph.add_node("copy", copy_node)
    graph.add_node("creative_brief", creative_brief_node)
    graph.add_node("image_gen", image_gen_node)
    graph.add_node("qa", qa_node)

    graph.set_entry_point("research")
    graph.add_edge("research", "strategy")
    graph.add_edge("strategy", "copy")
    graph.add_edge("copy", "creative_brief")
    graph.add_edge("creative_brief", "image_gen")
    graph.add_edge("image_gen", "qa")
    graph.add_edge("qa", END)

    return graph.compile()


_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


async def run_pipeline(campaign_data: dict) -> dict:
    initial_state: PipelineState = {
        "campaign_id": campaign_data.get("campaign_id", ""),
        "product_name": campaign_data.get("product_name", ""),
        "product_url": campaign_data.get("product_url", ""),
        "product_price": campaign_data.get("product_price", ""),
        "avatar": campaign_data.get("avatar", {}),
        "angle": campaign_data.get("angle", ""),
        "awareness_stage": campaign_data.get("awareness_stage", 1),
        "emotional_driver": campaign_data.get("emotional_driver", "Desire"),
        "platforms": campaign_data.get("platforms", []),
        "copy_model": campaign_data.get("copy_model", "claude-opus-4-5"),
        "use_local_models": campaign_data.get("use_local_models", True),
        "research_output": {},
        "strategy_output": {},
        "copy_output": {},
        "creative_brief_output": {},
        "image_output": {},
        "qa_output": {},
        "status": "running",
    }

    graph = get_graph()
    final_state = await graph.ainvoke(initial_state)
    return {
        "research_output": final_state.get("research_output", {}),
        "strategy_output": final_state.get("strategy_output", {}),
        "copy_output": final_state.get("copy_output", {}),
        "creative_brief_output": final_state.get("creative_brief_output", {}),
        "image_output": final_state.get("image_output", {}),
        "qa_output": final_state.get("qa_output", {}),
        "models_used": {
            "copy": campaign_data.get("copy_model", "claude-opus-4-5"),
            "strategy": "claude-sonnet-4-5",
            "research": "claude-sonnet-4-5",
            "creative_brief": "llama3.1:8b" if campaign_data.get("use_local_models") else "gpt-4o-mini",
            "qa": "llama3.1:8b" if campaign_data.get("use_local_models") else "gpt-4o-mini",
        },
    }
