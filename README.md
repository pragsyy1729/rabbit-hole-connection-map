# Rabbit Hole Knowledge Mapper

A visual, interactive tool to map semantic connections between two distinct concepts. By leveraging the Wikipedia API and large language models (LLaMA 3.1 70B via NVIDIA NIM), the Rabbit Hole Knowledge Mapper generates a logical, step-by-step path that connects "Concept A" to "Concept B."

Illustration of the demo - [Rabbit Hole Connection Map](https://www.youtube.com/watch?v=RkLWcFhlYek)

## Features

- **Semantic Path Generation:** Connect any two concepts through a logical N-step path.
- **LLM-Powered Reasoning:** Uses NVIDIA's LLaMA 3.1 70B Instruct model to reason about connections.
- **Real-Time UI Updates:** The frontend receives live updates as the backend generates the path using Server-Sent Events (SSE).
- **Persistent Library:** Paths are automatically saved locally (`knowledge_graph.json`) and can be exported, imported, or deleted.
- **MCP Server Integration:** Built using `FastMCP`, exposing tools for Wikipedia context fetching, graph CRUD operations, and Prefab UI rendering via the Model Context Protocol (MCP).

## Project Structure

- **`mcp_server.py`**: The core backend application. It defines the FastMCP server, MCP tools, and FastAPI endpoints (`/find-path`, `/library`, etc.).
- **`frontend/`**: The React + TypeScript frontend application, built with Vite.
- **`pyproject.toml`**: Python dependencies and project configuration (using Hatchling).

## Prerequisites

- **Python 3.11+**
- **Node.js 18+ & npm** (for the frontend)
- **NVIDIA API Key**: Required for LLaMA 3.1 inference. You can get one from the [NVIDIA API catalog](https://build.nvidia.com/).

## Getting Started

### 1. Backend Setup

1. Open a terminal in the project root directory.
2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
   ```
3. Install the dependencies:
   ```bash
   pip install -e .
   ```
4. Start the backend server:
   ```bash
   uvicorn mcp_server:app --host 0.0.0.0 --port 8000 --reload
   ```
   The backend will start running on `http://localhost:8000`.

### 2. Frontend Setup

1. Open a new terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install the frontend dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   The frontend will start running (typically on `http://localhost:5173`).

### 3. Usage

1. Open the frontend application in your browser.
2. Click the **Settings (⚙)** button in the top right corner and enter your **NVIDIA API Key**. (This is securely stored in your browser's local storage).
3. Enter two distinct concepts (e.g., "Quantum Computing" and "Pizza") and click the action button to generate the path.
4. The system will fetch context, query the LLM to generate intermediate connection steps, and stream the results back to the UI.

## Architecture

1. **`fetch_concept_context` (MCP Tool 1):** Fetches the Wikipedia summary for a concept.
2. **NVIDIA NIM LLM:** Acts as the reasoning engine to deduce exactly how the two concepts link in a specified number of steps.
3. **Enrichment:** The backend enriches the LLM's output by looking up the specific Wikipedia articles for the intermediate steps.
4. **`crud_knowledge_graph` (MCP Tool 2):** Saves the final generated path locally.
5. **`render_rabbit_hole_ui` (MCP Tool 3):** Renders an interactive Prefab UI and broadcasts the state via SSE to the React client.
