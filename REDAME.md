# arXiv CS Daily Agent System

## 📋 Overview

This project implements a multi-agent AI system that collaboratively develops a complete FastAPI web application from scratch. The system demonstrates "agentic AI" in software engineering, where specialized AI agents work together to plan, code, evaluate, and refine software projects based on natural language task descriptions.

## 🏗️ System Architecture

### Agent Roles & Responsibilities

| Agent | Role | Key Responsibilities |
|-------|------|----------------------|
| **PlannerAgent** | Project Planning | Translates goals into task lists with dependencies |
| **CodeAgent** | Code Generation | Generates Python/HTML/JS code using Qwen LLM |
| **EvalAgent** | Code Evaluation | Scores code quality against requirements |
| **AutoRefineAgent** | Self-Refinement | Improves code based on evaluation feedback |

### System Flow

1. **Planning Phase**: PlannerAgent creates task sequence
2. **Code Generation**: CodeAgent writes initial code
3. **Evaluation**: EvalAgent scores code quality
4. **Refinement Loop**: AutoRefineAgent fixes issues until target score reached
5. **Completion**: Final web application ready

### Repository Structure

```
workspace/
├── agents/
│   ├── agent_base.py          # Abstract agent base class
│   ├── planner_agent.py       # Task planning agent
│   ├── code_agent.py          # Code generation agent
│   ├── eval_agent.py          # Code evaluation agent
│   └── refine_agent.py        # Self-refinement agent
├── tools/
│   ├── arxiv_tools.py         # arXiv RSS fetching
│   └── fs_tools.py            # File system operations
├── webapp/                    # Generated application
│   ├── main.py               # FastAPI backend
│   ├── templates/
│   │   ├── index.html        # Main page
│   │   └── paper.html        # Paper detail page
│   └── static/
│       └── copy.js           # Clipboard functionality
├── orchestrator.py           # Main orchestration
├── requirements.txt          # Dependencies
└── README.md                # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- DashScope API key (for Qwen LLM)

### Installation

1. **Clone and setup**:
   ```bash
   git clone https://github.com/yourusername/arxiv-cs-daily-agent.git
   cd arxiv-cs-daily-agent
   python -m venv venv
   
   # Activate virtual environment
   # Windows: venv\Scripts\activate
   # Mac/Linux: source venv/bin/activate
   
   pip install -r requirements.txt
   ```

2. **Configure API key**:
   ```bash
   # Linux/Mac
   export DASHSCOPE_API_KEY="your-api-key-here"
   
   # Windows
   set DASHSCOPE_API_KEY=your-api-key-here
   ```

### Running the System

1. **Generate the web application**:
   ```bash
   python orchestrator.py
   ```

   This will:
   - Create project structure in `workspace/`
   - Generate all code files
   - Run evaluation and refinement cycles
   - Output progress and final scores

2. **Run the web application**:
   ```bash
   cd workspace/webapp
   uvicorn main:app --reload --port 8000
   ```

3. **Access the application**:
   - Open browser: http://localhost:8000
   - Browse arXiv CS papers by category (cs.AI, cs.CV, cs.CL, cs.LG, cs.NE)
   - Click titles for arXiv abstracts
   - Use copy buttons for BibTeX and citations

## 📖 Key Features

### 1. Multi-Agent Collaboration

Four specialized agents work together:
- **PlannerAgent**: Breaks down "build arXiv CS Daily webapp" into concrete tasks
- **CodeAgent**: Generates FastAPI backend, templates, and static files using Qwen LLM
- **EvalAgent**: Evaluates code against strict quality criteria (40-point scoring system)
- **AutoRefineAgent**: Iteratively improves code based on evaluation feedback

### 2. Self-Refinement Loop

The system automatically refines its output:
```python
# In refine_agent.py
refiner = AutoRefineAgent(
    workspace=workspace,
    call_qwen=ca.call_qwen,
    target_score=36,   # Target quality score (out of 40)
    max_rounds=3       # Maximum refinement attempts
)
```

### 3. arXiv Integration

Real-time paper fetching from arXiv RSS feeds:
```python
# Fetch papers for a category
from tools.arxiv_tools import fetch_category_rss

papers = fetch_category_rss("cs.AI", max_items=20)
# Returns: title, authors, abstract, PDF link, BibTeX, citation
```

### 4. Modern Web Interface

- Responsive two-column layout (categories on left, papers on right)
- Clean card-based paper display
- One-click BibTeX and citation copying
- Direct links to arXiv abstracts and PDFs

## 🔧 Configuration

### Custom Categories

Modify in `webapp/main.py`:
```python
CATEGORIES = [
    "cs.AI",      # Artificial Intelligence
    "cs.CV",      # Computer Vision
    "cs.CL",      # Computational Linguistics
    "cs.LG",      # Machine Learning
    "cs.NE",      # Neural and Evolutionary Computing
    # Add more categories as needed
]
```

### Evaluation Criteria

The 40-point scoring system evaluates:
- **main.py** (10 pts): FastAPI setup, routing, template configuration
- **index.html** (10 pts): Layout, responsiveness, paper cards, buttons
- **paper.html** (10 pts): Detail page, BibTeX display
- **copy.js** (10 pts): Clipboard functionality, error handling

## 📊 Example Output

### Generated Application Files

**main.py** (FastAPI backend):
```python
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from tools.arxiv_tools import fetch_category_rss

app = FastAPI()
CATEGORIES = ["cs.AI", "cs.CV", "cs.CL", "cs.LG", "cs.NE"]

@app.get("/")
async def read_root(request: Request, category: str = "cs.AI"):
    selected = category if category in CATEGORIES else "cs.AI"
    papers = {cat: fetch_category_rss(cat) for cat in CATEGORIES}
    return templates.TemplateResponse("index.html", {
        "request": request,
        "categories": CATEGORIES,
        "selected": selected,
        "papers": papers
    })
```

**index.html** (Main template):
- Left sidebar: Category navigation with active highlighting
- Right content: Paper cards with title, authors, summary, metadata
- Copy buttons: BibTeX and citation with JavaScript clipboard functionality

**copy.js** (Clipboard utility):
- Handles JSON-escaped strings from templates
- Uses `navigator.clipboard.writeText`
- Visual feedback with "Copied!" text


### Testing

```bash
# Run the system
python orchestrator.py

# Test the web application
cd workspace/webapp
uvicorn main:app --reload

# Test arXiv fetching directly
python -c "from tools.arxiv_tools import fetch_category_rss; print(fetch_category_rss('cs.AI', max_items=2))"
```

## 🔍 Troubleshooting

### Common Issues

1. **API Key Error**:
   ```
   Error: No API key provided for Qwen
   ```
   Solution: Ensure `DASHSCOPE_API_KEY` is set correctly

2. **Missing Dependencies**:
   ```
   ModuleNotFoundError: No module named 'feedparser'
   ```
   Solution: Run `pip install -r requirements.txt`

3. **Template Errors**:
   ```
   jinja2.exceptions.TemplateNotFound: index.html
   ```
   Solution: Check that `workspace/webapp/templates/` directory exists

### Debug Mode

Add logging to `orchestrator.py`:
```python
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
```


