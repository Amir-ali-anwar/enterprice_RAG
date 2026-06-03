from typing import TypedDict, List, Annotated
import operator


class AgentState(TypedDict):
    message: Annotated[List[dict], operator.add]
    current_query: str
    documents: List[dict]
    plan: List[str] | str
    status: str
    final_answer: str   