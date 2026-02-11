"""
Generate architecture diagrams for AI-Powered HR Decision Assistant.
Run from this folder: python make_architecture_diagram.py
Outputs: hr_decision_graph.png, policy_ingestion_graph.png, architecture.png, architecture_spec.png
"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Tuple, List, Optional

@dataclass(frozen=True)
class Edge:
    src: str
    dst: str
    label: Optional[str] = None
    style: str = "solid"
    curve: float = 0.0


def _connect_points(
    src_xy: Tuple[float, float],
    dst_xy: Tuple[float, float],
    box_w: float,
    box_h: float,
) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
    x1, y1 = src_xy
    x2, y2 = dst_xy
    dx, dy = x2 - x1, y2 - y1
    if abs(dx) > abs(dy):
        if dx >= 0:
            start = (x1 + box_w / 2, y1)
            end = (x2 - box_w / 2, y2)
        else:
            start = (x1 - box_w / 2, y1)
            end = (x2 + box_w / 2, y2)
        label_xy = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2 + 0.02)
    else:
        if dy >= 0:
            start = (x1, y1 + box_h / 2)
            end = (x2, y2 - box_h / 2)
        else:
            start = (x1, y1 - box_h / 2)
            end = (x2, y2 + box_h / 2)
        label_xy = ((start[0] + end[0]) / 2 + 0.02, (start[1] + end[1]) / 2)
    return start, end, label_xy


def draw_flowchart(nodes, edges, positions, title, outpath, figsize=(18,10), dpi=220):
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    ax.set_axis_off()
    ax.set_title(title, fontsize=16, pad=18)
    box_w, box_h = 0.19, 0.085
    for nid, label in nodes.items():
        x, y = positions[nid]
        rect = FancyBboxPatch(
            (x - box_w/2, y - box_h/2), box_w, box_h,
            boxstyle="round,pad=0.012,rounding_size=0.02",
            linewidth=1.4, facecolor="white", edgecolor="black"
        )
        ax.add_patch(rect)
        ax.text(x, y, label, ha="center", va="center", fontsize=9, wrap=True)
    for e in edges:
        if isinstance(e, tuple):
            src, dst, elabel, style = e
            e = Edge(src=src, dst=dst, label=elabel, style=style, curve=0.0)
        start, end, label_xy = _connect_points(
            positions[e.src], positions[e.dst], box_w=box_w, box_h=box_h
        )
        ls = "--" if e.style == "dashed" else "-"
        conn = f"arc3,rad={e.curve}" if e.curve else "arc3,rad=0"
        ax.annotate("", xy=end, xytext=start,
                    arrowprops=dict(arrowstyle="->", linewidth=1.1, linestyle=ls, connectionstyle=conn))
        if e.label:
            ax.text(label_xy[0], label_xy[1], e.label, ha="center", va="center", fontsize=8)
    fig.tight_layout()
    outpath = Path(outpath)
    fig.savefig(outpath, bbox_inches="tight")
    plt.close(fig)
    print("Saved:", outpath.resolve())


def draw_architecture(outpath):
    nodes = {
        "user": "User",
        "cli": "CLI (cli_chat.py)\nlogin + chat loop",
        "langgraph": "LangGraph Runtime\n(graph.py + HelpServiceState.py)\nvalidate → classify → route",
        "llm": "LLM (Ollama)\nqwen2.5",
        "mcp": "MCP Server\nazure-postgresql-mcp\n(query_data/update_values)",
        "db": "PostgreSQL\nemployees + attendance",
        "policies": "Policy Docs\n(hr_rules_content.py)\n+ PDFs (poc_data/hr_rules)",
        "langsmith": "LangSmith\nTracing/Observability\n(smith.langchain.com)",
    }
    pos = {
        "user": (0.10, 0.70), "cli": (0.28, 0.70), "langgraph": (0.50, 0.70),
        "llm": (0.72, 0.82), "mcp": (0.72, 0.58), "db": (0.90, 0.58),
        "policies": (0.72, 0.34), "langsmith": (0.50, 0.40),
    }
    edges = [
        Edge("user", "cli", "input", "solid"),
        Edge("cli", "langgraph", "run_help_service()", "solid"),
        Edge("langgraph", "llm", "classify / RAG / format", "solid", curve=0.10),
        Edge("langgraph", "mcp", "DB reads/writes", "solid", curve=-0.10),
        Edge("mcp", "db", "SQL", "solid"),
        Edge("langgraph", "policies", "policy Q&A context", "dashed"),
        Edge("langgraph", "langsmith", "trace runs", "dashed"),
    ]
    draw_flowchart(nodes, edges, pos, "Project3 Architecture (High-Level)", outpath, figsize=(18, 9), dpi=240)


def main(out_dir: Optional[Path] = None):
    out_dir = out_dir or Path.cwd()
    out_dir = Path(out_dir)

    online_nodes = {
        "start": "__start__",
        "load_session": "load_session_memory\n(short-term)",
        "validate_user": "validate_user\n(MCP auth + role)",
        "load_ltm": "load_long_term_memory\n(MCP/DB: profile + patterns)",
        "classify": "classify_issue\n(LLM intent → {domain, op, sensitivity})",
        "simple_read": "fetch_simple_data\n(MCP read)",
        "rag": "rag_policy_retrieve\n(MCP semantic search)",
        "policy_reason": "policy_reasoning_agent\n(interpret clauses)",
        "draft_action": "draft_action_plan\n(LLM → proposed_action JSON)",
        "data_reason": "data_reasoning_agent\n(validate constraints/SQL)",
        "critic": "critic_compliance_agent\n(second-pass review)",
        "guardrails": "decision_guardrails\n(route: approve/deny/HITL/clarify)",
        "clarify": "ask_clarifying_question",
        "hitl": "human_in_the_loop\n(MCP approval request)",
        "await": "await_approval_event",
        "execute": "execute_update\n(MCP write)",
        "audit": "persist_audit_log\n(MCP)",
        "format": "format_response\n(decision + why + policy_ref)",
        "end": "__end__",
    }
    online_positions = {
        "start": (0.5, 0.95), "load_session": (0.5, 0.88), "validate_user": (0.5, 0.80),
        "load_ltm": (0.5, 0.72), "classify": (0.5, 0.64),
        "simple_read": (0.18, 0.52), "rag": (0.50, 0.52), "draft_action": (0.82, 0.52),
        "policy_reason": (0.50, 0.42), "data_reason": (0.72, 0.42), "critic": (0.92, 0.42),
        "guardrails": (0.82, 0.32), "clarify": (0.66, 0.22), "hitl": (0.82, 0.22),
        "await": (0.82, 0.14), "execute": (0.82, 0.06), "audit": (0.50, 0.22),
        "format": (0.50, 0.12), "end": (0.50, 0.04),
    }
    online_edges = [
        Edge("start", "load_session"), Edge("load_session", "validate_user"),
        Edge("validate_user", "load_ltm"), Edge("load_ltm", "classify"),
        Edge("classify", "simple_read", "read", "dashed", curve=0.10),
        Edge("classify", "rag", "policy_qna", "dashed", curve=0.00),
        Edge("classify", "draft_action", "write/update", "dashed", curve=-0.10),
        Edge("simple_read", "format"), Edge("rag", "policy_reason"), Edge("policy_reason", "format"),
        Edge("draft_action", "data_reason", curve=0.10), Edge("draft_action", "critic", curve=-0.10),
        Edge("data_reason", "guardrails"), Edge("critic", "guardrails"),
        Edge("guardrails", "clarify", "need_clarification", "dashed", curve=0.15),
        Edge("clarify", "classify", "user answers → re-route", "dashed", curve=0.25),
        Edge("guardrails", "hitl", "need_HITL", "dashed", curve=-0.10), Edge("hitl", "await"),
        Edge("await", "execute", "approved", "dashed"), Edge("await", "format", "rejected", "dashed"),
        Edge("guardrails", "execute", "approve_auto", "dashed", curve=-0.25),
        Edge("guardrails", "format", "deny", "dashed", curve=0.00),
        Edge("execute", "audit"), Edge("audit", "format"), Edge("format", "end"),
    ]
    draw_flowchart(
        online_nodes, online_edges, online_positions,
        "Online Decision Graph (LangGraph Runtime) — HR Decision Assistant",
        out_dir / "hr_decision_graph.png", figsize=(20, 11), dpi=240
    )

    offline_nodes = {
        "start": "ingest_docs_start", "extract": "extract_text\n(PDF → text)",
        "chunk": "chunk_documents\n+ metadata (doc,page,section)",
        "embed": "embed_chunks\n(embedding model)",
        "upsert": "upsert_vector_store\n(vectors + metadata)",
        "manifest": "build_policy_index_manifest\n(versioning + freshness)",
        "end": "ingest_docs_end",
    }
    offline_positions = {
        "start": (0.5, 0.90), "extract": (0.5, 0.76), "chunk": (0.5, 0.62),
        "embed": (0.5, 0.48), "upsert": (0.5, 0.34), "manifest": (0.5, 0.20), "end": (0.5, 0.08),
    }
    offline_edges = [
        ("start", "extract", None, "solid"), ("extract", "chunk", None, "solid"),
        ("chunk", "embed", None, "solid"), ("embed", "upsert", None, "solid"),
        ("upsert", "manifest", None, "solid"), ("manifest", "end", None, "solid"),
    ]
    draw_flowchart(
        offline_nodes, offline_edges, offline_positions,
        "Offline Policy Ingestion Graph — PDFs → Chunks → Embeddings → Vector DB",
        out_dir / "policy_ingestion_graph.png", figsize=(14, 9), dpi=240
    )
    draw_architecture(out_dir / "architecture.png")
    draw_architecture_spec_overview(out_dir / "architecture_spec.png")


def draw_architecture_spec_overview(outpath):
    fig = plt.figure(figsize=(20, 14), dpi=180)
    fig.suptitle("AI-Powered HR Decision Assistant — Architecture (from ARCHITECTURE spec)", fontsize=14, y=0.98)

    def draw_box(ax, xy, w, h, label, color="white", ec="black"):
        rect = FancyBboxPatch(xy, w, h, boxstyle="round,pad=0.01,rounding_size=0.02",
                              facecolor=color, edgecolor=ec, linewidth=1.2)
        ax.add_patch(rect)
        ax.text(xy[0] + w/2, xy[1] + h/2, label, ha="center", va="center", fontsize=9, wrap=True)

    ax1 = fig.add_subplot(3, 1, 1)
    ax1.set_axis_off()
    ax1.set_title("1. System overview", fontsize=12, pad=8)
    draw_box(ax1, (0.02, 0.35), 0.12, 0.35, "User", "#e3f2fd")
    draw_box(ax1, (0.16, 0.35), 0.14, 0.35, "CLI / App\n(login, chat)", "#fff3e0")
    draw_box(ax1, (0.32, 0.25), 0.22, 0.55, "LangGraph Runtime\nvalidate → memory →\nclassify → route → act", "#e8f5e9")
    draw_box(ax1, (0.58, 0.55), 0.14, 0.25, "LLM\n(classify, RAG,\nformat)", "#fce4ec")
    draw_box(ax1, (0.58, 0.25), 0.14, 0.25, "MCP\n(auth, DB,\nsearch, audit)", "#f3e5f5")
    draw_box(ax1, (0.76, 0.55), 0.12, 0.25, "Policies\n(vector store)", "#e0f7fa")
    draw_box(ax1, (0.76, 0.25), 0.12, 0.25, "LangSmith\ntracing", "#fff8e1")
    draw_box(ax1, (0.90, 0.35), 0.08, 0.35, "PostgreSQL\n+ Vector DB", "#eceff1")
    for (a, b) in [(0.14, 0.16), (0.30, 0.32), (0.54, 0.58)]:
        ax1.annotate("", xy=(b, 0.52), xytext=(a, 0.52), arrowprops=dict(arrowstyle="->", lw=1.2))
    ax1.annotate("", xy=(0.58, 0.65), xytext=(0.54, 0.65), arrowprops=dict(arrowstyle="->", lw=1.2))
    ax1.annotate("", xy=(0.58, 0.38), xytext=(0.54, 0.38), arrowprops=dict(arrowstyle="->", lw=1.2))
    ax1.plot([0.54, 0.76], [0.52, 0.52], "k--", lw=1)
    ax1.annotate("", xy=(0.76, 0.52), xytext=(0.54, 0.52), arrowprops=dict(arrowstyle="->", lw=1, linestyle="--"))
    ax1.set_xlim(0, 1); ax1.set_ylim(0, 1)

    ax2 = fig.add_subplot(3, 1, 2)
    ax2.set_axis_off()
    ax2.set_title("2. Online decision graph (per request)", fontsize=12, pad=8)
    n_val, n_mem, n_cls, n_route = (0.5, 0.88, "validate_user (MCP)"), (0.5, 0.76, "load_session_memory"), (0.5, 0.64, "classify_issue (LLM)"), (0.5, 0.52, "route_by_intent")
    n_fetch, n_rag, n_write = (0.18, 0.36, "fetch_simple_data"), (0.5, 0.36, "rag_policy → policy_agent"), (0.82, 0.36, "draft_action → guardrails")
    n_fmt, n_upd = (0.5, 0.20, "format_response"), (0.5, 0.08, "update_short_term_memory")
    for x, y, label in [n_val, n_mem, n_cls, n_route, n_fetch, n_rag, n_write, n_fmt, n_upd]:
        draw_box(ax2, (x - 0.08, y - 0.06), 0.16, 0.10, label, "white", "black")
    for (x1, y1, _), (x2, y2, _) in [(n_val, n_mem), (n_mem, n_cls), (n_cls, n_route)]:
        ax2.annotate("", xy=(x2, y2 - 0.06), xytext=(x1, y1 + 0.06), arrowprops=dict(arrowstyle="->", lw=1.2))
    for bx, by, _ in [n_fetch, n_rag, n_write]:
        ax2.annotate("", xy=(bx, by + 0.06), xytext=(0.5, 0.52 - 0.06), arrowprops=dict(arrowstyle="->", lw=1.1, connectionstyle="arc3,rad=0.15"))
    for bx, by, _ in [n_fetch, n_rag, n_write]:
        ax2.annotate("", xy=(0.5, 0.20 + 0.06), xytext=(bx, by - 0.06), arrowprops=dict(arrowstyle="->", lw=1.1, connectionstyle="arc3,rad=0.1"))
    ax2.annotate("", xy=(0.5, 0.08 + 0.06), xytext=(0.5, 0.20 - 0.06), arrowprops=dict(arrowstyle="->", lw=1.2))
    ax2.text(0.5, 0.44, "read │ policy Q&A │ write/update", ha="center", fontsize=9, style="italic")
    ax2.set_xlim(0, 1); ax2.set_ylim(0, 1)

    ax3 = fig.add_subplot(3, 1, 3)
    ax3.set_axis_off()
    ax3.set_title("3. Offline policy ingestion (batch)", fontsize=12, pad=8)
    off_nodes = [(0.08, 0.5, "PDFs"), (0.24, 0.5, "extract_text"), (0.40, 0.5, "chunk"), (0.56, 0.5, "embed"), (0.72, 0.5, "upsert_vector_store"), (0.88, 0.5, "manifest")]
    for x, y, label in off_nodes:
        draw_box(ax3, (x - 0.06, y - 0.08), 0.12, 0.16, label, "#e8f5e9", "black")
    for i in range(len(off_nodes) - 1):
        x1, y1, _ = off_nodes[i]; x2, y2, _ = off_nodes[i + 1]
        ax3.annotate("", xy=(x2 - 0.06, y2), xytext=(x1 + 0.06, y1), arrowprops=dict(arrowstyle="->", lw=1.2))
    ax3.set_xlim(0, 1); ax3.set_ylim(0, 1)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    Path(outpath).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(outpath, bbox_inches="tight")
    plt.close(fig)
    print("Saved:", Path(outpath).resolve())


if __name__ == "__main__":
    main(out_dir=Path(__file__).resolve().parent)
