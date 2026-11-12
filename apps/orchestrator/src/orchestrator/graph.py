"""The agent as a LangGraph state graph (brief §6.4).

classify -> one domain node per Ask feature (attendance, fees, timetable, exams, assignments)
-> reply; every other intent gets a short templated answer. Navigate, confirm and execute
arrive later in M4; the escalation check after each node in M6.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from orchestrator import replies
from orchestrator.courses import match_course
from orchestrator.dates import NOW, campus_now, resolve_after, resolve_day
from orchestrator.intent import Classifier, Intent, ReplayMiss
from orchestrator.replies import Reply
from orchestrator.ums import MiniUms, UmsUnauthorized, UmsUnavailable

log = logging.getLogger(__name__)

# Intents with their own domain node; everything else gets a templated answer from `other`.
ASK_NODES = ("attendance", "fees", "timetable", "exams", "assignments")


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
        name = state["intent"].intent
        return name if name in ASK_NODES else "other"

    async def lookup(
        state: TurnState, what: str, link: dict[str, str], call: Callable[[], Awaitable[Any]]
    ) -> tuple[Any, Reply | None]:
        """Run one API call; on failure return the reply that says so (rule 5)."""
        try:
            return await call(), None
        except UmsUnauthorized:
            return None, replies.session_ended()
        except UmsUnavailable:
            log.warning("lookup failed", extra={"feature": what})
            return None, replies.data_unavailable(what, link)

    async def fees(state: TurnState) -> dict[str, Any]:
        data, failed = await lookup(
            state, "fee records", replies.FEES_LINK, lambda: ums.fees(state["api_token"])
        )
        head = state["intent"].fee_head
        return {"reply": failed or replies.fees(data, campus_now().date(), head)}

    async def timetable(state: TurnState) -> dict[str, Any]:
        intent, now = state["intent"], campus_now()
        try:
            day = resolve_day(intent.day, now.date())
            after = resolve_after(intent.after, now)
        except ValueError:
            return {"reply": replies.unclear_day()}
        next_only = intent.after == NOW
        data, failed = await lookup(
            state,
            "timetable",
            replies.TIMETABLE_LINK,
            lambda: ums.timetable(state["api_token"], day, after),
        )
        return {"reply": failed or replies.timetable(data, now.date(), after, next_only)}

    async def exams(state: TurnState) -> dict[str, Any]:
        rows, failed = await lookup(
            state, "exam schedule", replies.EXAMS_LINK, lambda: ums.exams(state["api_token"])
        )
        if failed:
            return {"reply": failed}
        today, mention = campus_now().date(), state["intent"].course
        if mention:
            courses = list({r["course_code"]: r for r in rows}.values())
            match = match_course(mention, courses)
            if match.course is None:
                reply = replies.exams(rows, today)
                reply.sentences.insert(
                    0,
                    f'I couldn\'t match "{mention}" to one of your courses, '
                    "so here are all your exams.",
                )
                return {"reply": reply}
            rows = [r for r in rows if r["course_code"] == match.course["course_code"]]
        return {"reply": replies.exams(rows, today)}

    async def assignments(state: TurnState) -> dict[str, Any]:
        rows, failed = await lookup(
            state,
            "assignments",
            replies.ASSIGNMENTS_LINK,
            lambda: ums.assignments(state["api_token"]),
        )
        if failed:
            return {"reply": failed}
        today, mention = campus_now().date(), state["intent"].course
        if mention:
            match = match_course(mention, list({r["course_code"]: r for r in rows}.values()))
            if match.course is None:
                # No pending work in a course that was named: say so, then list the rest.
                reply = replies.assignments(rows, today)
                reply.sentences.insert(0, f'You have no pending assignments for "{mention}".')
                return {"reply": reply}
            code = match.course["course_code"]
            reply = replies.assignments([r for r in rows if r["course_code"] == code], today)
            return {"reply": reply}
        return {"reply": replies.assignments(rows, today)}

    async def attendance(state: TurnState) -> dict[str, Any]:
        try:
            rows = await ums.attendance(state["api_token"])
        except UmsUnauthorized:
            return {"reply": replies.session_ended()}
        except UmsUnavailable:
            log.warning("attendance lookup failed")
            return {"reply": replies.data_unavailable()}

        mention, rank = state["intent"].course, state["intent"].rank
        if rank and not mention:
            return {"reply": replies.ranked_attendance(rows, rank)}
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

    nodes = {
        "attendance": attendance,
        "fees": fees,
        "timetable": timetable,
        "exams": exams,
        "assignments": assignments,
        "other": other,
    }
    graph = StateGraph(TurnState)
    graph.add_node("classify", classify)
    for name, node in nodes.items():
        graph.add_node(name, node)
        graph.add_edge(name, END)
    graph.add_edge(START, "classify")
    graph.add_conditional_edges("classify", route, {n: n for n in nodes})
    return graph.compile()
