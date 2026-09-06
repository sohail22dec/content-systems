"""Generate visual graph diagrams of the Content Systems LangGraph workflow."""

import json
import base64
import urllib.request
from pathlib import Path
from content_agent.graph import build_content_agent_graph

BEAUTIFUL_MERMAID = """%%{init: {'theme': 'dark', 'themeVariables': {'darkMode': true, 'fontFamily': 'Inter, system-ui, sans-serif'}}}%%
flowchart TD
    %% Boundary Nodes
    START([🚀 START]):::boundaryNode
    END([🏁 END]):::boundaryNode

    %% Functional Subgraphs
    subgraph MemoryLayer [🧠 Long-Term Memory Engine]
        retrieve_memory_node["<b>Retrieve Memory Node</b><br/><i>Load top active evolved pedagogical rules</i>"]:::memoryNode
        memory_update_node["<b>Memory Update Node</b><br/><i>Persist run trace & synthesize new rules</i>"]:::memoryNode
    end

    subgraph GenerationLayer [✍️ Adaptive Content Drafter]
        generator_node["<b>Generator Node</b><br/><i>Draft lesson calibrated for 12th grader</i>"]:::genNode
        error_injector_node["<b>Error Injector Node</b><br/><i>Inject deliberate fault (Draft 1 only)</i>"]:::injectNode
    end

    subgraph EvaluationAuditLayer [⚖️ Strict Binary Quality Gate]
        evaluator_node{"<b>Evaluator Node</b><br/><i>Strict 6-Dimension Rubric<br/>(Zero Partial Credit)</i>"}:::evalNode
        diagnose_node["<b>Diagnostician Node</b><br/><i>Surgical flaw repair & rejection log</i>"]:::diagNode
    end

    %% State Transitions
    START ==> retrieve_memory_node
    retrieve_memory_node --> generator_node
    generator_node --> error_injector_node
    error_injector_node --> evaluator_node

    %% Routing Decisions
    evaluator_node -- "✅ ALL 6 PASS<br/>or Max Retries Reached" --> memory_update_node
    evaluator_node -. "❌ FAIL<br/>(Checkpoints Violated)" .-> diagnose_node

    %% Self-Correction Feedback Loop
    diagnose_node ==> |"🔄 Surgical Remediation Feedback"| generator_node
    memory_update_node ==> END

    %% Custom Modern Palette Styling
    classDef boundaryNode fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#f8fafc,font-weight:bold;
    classDef memoryNode fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#ecfdf5;
    classDef genNode fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px,color:#eff6ff;
    classDef injectNode fill:#78350f,stroke:#f59e0b,stroke-width:2px,color:#fffbeb;
    classDef evalNode fill:#4c1d95,stroke:#a855f7,stroke-width:2px,color:#faf5ff,font-weight:bold;
    classDef diagNode fill:#881337,stroke:#f43f5e,stroke-width:2px,color:#fff1f2;

    style MemoryLayer fill:#022c22,stroke:#059669,stroke-dasharray: 5 5,color:#6ee7b7
    style GenerationLayer fill:#082f49,stroke:#0284c7,stroke-dasharray: 5 5,color:#7dd3fc
    style EvaluationAuditLayer fill:#2e1065,stroke:#7c3aed,stroke-dasharray: 5 5,color:#c4b5fd
"""


def generate_graph_artifacts(output_dir: str = "docs"):
    """Export styled Mermaid code and render high-resolution PNG diagram."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # 1. Save Styled Mermaid code
    mmd_file = out_path / "graph.mmd"
    with open(mmd_file, "w", encoding="utf-8") as f:
        f.write(BEAUTIFUL_MERMAID)
    print(f"✓ Saved styled Mermaid diagram source: {mmd_file}")

    # 2. Render high-resolution PNG diagram
    png_file = out_path / "graph.png"
    try:
        state = {"code": BEAUTIFUL_MERMAID, "mermaid": {"theme": "dark"}}
        b64 = base64.urlsafe_b64encode(json.dumps(state).encode("utf-8")).decode("utf-8")
        url = f"https://mermaid.ink/img/{b64}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            png_bytes = resp.read()
        with open(png_file, "wb") as f:
            f.write(png_bytes)
        print(f"✓ Saved high-resolution PNG graph diagram: {png_file} ({len(png_bytes)} bytes)")
    except Exception as e:
        print(f"Notice: Online PNG render fallback using LangGraph native: {e}")
        app = build_content_agent_graph()
        png_bytes = app.get_graph().draw_mermaid_png()
        with open(png_file, "wb") as f:
            f.write(png_bytes)

    return BEAUTIFUL_MERMAID, png_file


if __name__ == "__main__":
    generate_graph_artifacts()
