"""The agent as a LangGraph state graph (brief §6.4).

M3 has the first slice of the brief's graph: classify -> domain node -> reply. The domain is
attendance (the one Ask feature); every other intent gets a short templated answer. Confirm,
execute, authenticate and the escalation check after each node arrive in M4 and M6.
"""

import logging
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from orchestrator import replies
from orchestrator.courses import match_course
from orchestrator.intent import Classifier, Intent, ReplayMiss
from orchestrator.replies import Reply
from orchestrator.ums import MiniUms, UmsUnauthorized, UmsUnavailable

log = logging.getLogger(__name__)


class TurnState(TypedDict, total=False):
    text: str
    api_token: str
    first_name: str
    page_id: str | None
    intent: Intent
    reply: Reply


def build_graph(classifier: Classifier, ums: MiniUms) -> Any:
    async def classify(state: TurnState) -> dict[str, Any]:
        try:
            intent = await classifier.classify(state["text"])
        except ReplayMiss:
            log.warning("no replay recording for this utterance")
            intent = Intent(intent="out_of_scope")
        log.info("classified", extra={"intent": intent.intent, "classifier": classifier.name})
        return {"intent": intent}

    def route(state: TurnState) -> str:
        return "attendance" if state["intent"].intent == "attendance" else "other"

    async def attendance(state: TurnState) -> dict[str, Any]:
        try:
            rows = await ums.attendance(state["api_token"])
        except UmsUnauthorized:
            return {"reply": replies.session_ended()}
        except UmsUnavailable:
            log.warning("attendance lookup failed")
            return {"reply": replies.data_unavailable()}

        mention = state["intent"].course
        if not mention:
            return {"reply": replies.overall_attendance(rows)}
        match = match_course(mention, rows)
        if match.course is not None:
            return {"reply": replies.course_attendance(match.course)}
        if match.ambiguous:
            return {"reply": replies.course_ambiguous(match)}
        return {"reply": replies.course_not_found(mention, rows)}

    async def other(state: TurnState) -> dict[str, Any]:
        intent = state["intent"]
        if intent.intent == "greeting":
            return {"reply": replies.greeting(state["first_name"])}
        if intent.intent == "help":
            return {"reply": replies.help_reply()}
        if intent.intent == "unsupported":
            return {"reply": replies.unsupported(intent.feature)}
        return {"reply": replies.out_of_scope()}

    graph = StateGraph(TurnState)
    graph.add_node("classify", classify)
    graph.add_node("attendance", attendance)
    graph.add_node("other", other)
    graph.add_edge(START, "classify")
    graph.add_conditional_edges("classify", route, {"attendance": "attendance", "other": "other"})
    graph.add_edge("attendance", END)
    graph.add_edge("other", END)
    return graph.compile()
