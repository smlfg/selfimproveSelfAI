# Mission Control UI: The Evolution of SelfAI's Interface

## 🚀 Overview

This document details the implementation of the new **Mission Control UI** for SelfAI. We moved from a sequential, single-stream terminal output to a high-performance, parallel streaming dashboard that visualizes the "brain" of the agent in real-time.

**Key Achievement:** A "Minority Report" style interface where users can watch multiple subtasks thinking and acting simultaneously, with zero latency.

## 🌟 Features

### 1. True Parallel Streaming ("Mission Control")
- **Vertical Streamline Layout:** Subtasks are stacked vertically (full width) for maximum readability.
- **Real-Time Rolling Logs:** Each box acts like a dedicated terminal (`tail -f`), showing the last 8 lines of activity.
- **Thinking vs. Response:** Thoughts (cyan) and actions/responses (white) are visually distinct but flow in a unified stream.

### 2. High-Performance Rendering
- **Smoothing Engine:** A dedicated background thread renders the UI at a fixed 20 FPS, decoupling data ingestion from display.
- **Zero-Latency Buffer:** Incoming tokens are buffered instantly, ensuring characters appear fluidly without stuttering or waiting for newlines.
- **Visual Pulse:** A blinking cursor (`█`) indicates active processing, giving immediate visual feedback.

### 3. Deep Integration
- **SmolAgents Hook:** Tool calls (e.g., `search_selfai_code`) are intercepted and formatted as clean action logs (`🔧 ACTION: ...`) directly in the subtask box.
- **Minimax Streaming:** Enabled genuine Server-Side Events (SSE) streaming for the LLM backend, eliminating the "wait-until-done" bottleneck.
- **Robust Fallbacks:** The system gracefully degrades to standard terminal output if the `rich` library is missing or disabled.

## 🛠️ Technical Architecture

### The "Pipeline Problem" Solved
Initially, data flowed but didn't display correctly. We fixed the pipeline:

1.  **Source:** `MinimaxInterface` now yields tokens immediately via SSE (`stream=True`).
2.  **Dispatcher:** `ExecutionDispatcher` routes these tokens to the correct `task_id`.
3.  **UI Logic (`ParallelStreamUI`):**
    *   **Data Ingestion:** `add_chunk()` appends text to a raw buffer.
    *   **Escaping:** All content is strictly escaped to prevent XML tags (like `<invoke>`) from breaking the renderer.
    *   **Formatting:** System messages (`[bold yellow]Goal:...`) bypass escaping via `skip_escape=True`.
4.  **Rendering Loop:** A separate thread checks for changes every 50ms and updates only the necessary screen regions using direct object references (`task_layout_map`).

### File Structure
*   **`selfai/ui/parallel_stream_ui.py`**: The core UI engine (Dashboard, Rendering Loop).
*   **`selfai/core/execution_dispatcher.py`**: Orchestrates the plan and manages UI lifecycle.
*   **`selfai/core/minimax_interface.py`**: Provides the raw data stream.
*   **`selfai/core/smolagents_runner.py`**: Injects tool activities into the UI stream.

## 🎮 Usage

The Mission Control UI is **active by default** if `rich` is installed.

**Run a plan:**
```bash
python selfai/selfai.py
> /plan Wer bist du und was kannst du?
```

**What you see:**
1.  **Dashboard opens:** A persistent view showing all subtasks.
2.  **Live Streaming:** Tasks start thinking and acting in parallel.
3.  **Completion:** Once finished, the dashboard closes (or stays in history), and the full result is printed to the terminal for permanent record.

## 💡 Philosophy
> "Don't just show the result. Show the thinking."

This UI transforms SelfAI from a black box into a transparent glass box, building trust and engagement by showing the user exactly what is happening under the hood.

---
*Implemented by Gemini & User Collaboration - January 2025*
