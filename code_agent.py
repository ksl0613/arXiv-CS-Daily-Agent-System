from .agent_base import AgentBase
from tools.fs_tools import write_file, ensure_workspace
from typing import Dict, Any
from pathlib import Path
import os
from openai import OpenAI
import json 
import textwrap
from unittest.mock import patch
from typing import List, Dict

class CodeAgent(AgentBase):
    def __init__(self, name: str, shared_state: Dict[str, Any],
                 workspace="workspace",
                 enable_llm=True):
        super().__init__(name, shared_state)
        self.workspace = Path(workspace)
        ensure_workspace(self.workspace)

        self.enable_llm = enable_llm  # 是否启用 QWEN 生成

        self.client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

    def call_qwen(self, prompt: str) -> str:
        """调用 QWEN 生成代码，并清洗 Markdown 格式"""
        if not self.enable_llm:
            return ""

        resp = self.client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": "You are a professional Python software engineer. Output ONLY valid pure code. Do NOT include markdown or ```."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=2048
        )

        raw = resp.choices[0].message.content.strip()

        # ===== 清洗 Markdown 代码块 =====
        if raw.startswith("```"):
            raw = raw.replace("```python", "").replace("```", "").strip()

        return raw

    def act(self, task: Dict[str, Any]) -> Dict[str, Any]:
        tid = task.get("id")

        if tid == "init_repo":
            return self._init_repo()
        elif tid == "fetch_arxiv":
            return self._generate_arxiv_tools()
        elif tid == "generate_web_app":
            return self._generate_web_app()
        else:
            return {"status": "unknown_task", "task": tid}

    # ---------------------------
    # 1. Init repo
    # ---------------------------
    def _init_repo(self):
        req = "\n".join([
            "fastapi",
            "uvicorn[standard]",
            "jinja2",
            "feedparser",
            "requests",
            "pytest",
            "openai"
        ])
        write_file(self.workspace / "requirements.txt", req)

        write_file(self.workspace / "README.md", """
        # arXiv CS Daily Agent System

        Powered by QWEN + Multi-Agent System for COMP7103C.

        Run:
        python orchestrator.py
        """)

        return {"status": "ok", "files": ["requirements.txt", "README.md"]}

    # ---------------------------
    # 2. Generate arxiv tools
    # ---------------------------
    def _generate_arxiv_tools(self):
        tools_dir = self.workspace / "tools"
        ensure_workspace(tools_dir)
        write_file(tools_dir / "__init__.py", "")

        # Prompt that will be sent to model to produce a robust arxiv_tools.py
        tools_prompt = '''
        import feedparser
        from typing import List, Dict
        from datetime import datetime

        def _normalize_date(date_str: str) -> str:
            """Convert common RSS date formats to YYYY-MM-DD; fallback to first 10 chars."""
            if not date_str:
                return ""
            for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            # fallback
            return date_str[:10]

        def fetch_category_rss(category_tag: str, max_items: int = 20) -> List[Dict]:
            """
            Fetch arXiv RSS for category_tag and return a list of normalized dicts.

            Each dict fields:
            - id: str (arXiv id)
            - title: str
            - authors: List[str]  # list of author names only (no affiliation)
            - published: str      # YYYY-MM-DD
            - arxiv_tag: str      # e.g. cs.CV or wrapped [cs.CV] depending on template needs
            - abs_link: str       # https://arxiv.org/abs/{id}
            - pdf_link: str       # https://arxiv.org/pdf/{id}.pdf
            - summary: str
            - bibtex: str
            - citation: str

            Notes:
            - Authors: handle entries where a single author field contains "A, B, C" by splitting on commas.
            - Use safe fallbacks if feed data is missing.
            """

            url = f"http://export.arxiv.org/rss/{category_tag}"
            feed = feedparser.parse(url)

            papers = []
            for entry in (feed.entries or [])[:max_items]:
                # try to get canonical id (last path segment of link), fallback to entry.id
                link = entry.get("link", "") or entry.get("id", "")
                arxiv_id = link.rstrip("/").split("/")[-1] if link else (entry.get("id", "") or "")

                abs_link = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else link
                pdf_link = f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else ""

                # parse authors => List[str]
                authors = []
                if hasattr(entry, "authors") and entry.authors:
                    for a in entry.authors:
                        raw = a.get("name") if isinstance(a, dict) and a.get("name") else str(a)
                        # split comma-separated names (common in some RSS)
                        parts = [p.strip() for p in raw.split(",") if p.strip()]
                        # if single long name like "A B C" parts may be length 1 -> keep as is
                        authors.extend(parts)
                else:
                    # some feeds include author in entry.get('author')
                    raw = entry.get("author", "") or entry.get("dc:creator", "")
                    if raw:
                        parts = [p.strip() for p in raw.split(",") if p.strip()]
                        authors.extend(parts)

                # normalize date
                published_raw = entry.get("published", "") or entry.get("updated", "")
                published = _normalize_date(published_raw)

                # build bibtex and citation (simple reasonable default)
                author_names_for_bib = " and ".join(authors) if authors else "Unknown"
                author_names_for_cite = ", ".join(authors) if authors else "Unknown"

                bibtex = f"""@article{{{arxiv_id or 'unknown'},
            title={{ {entry.get('title','').replace('{','{{').replace('}','}}')} }},
            author={{ {author_names_for_bib} }},
            journal={{arXiv preprint arXiv:{arxiv_id} }},
            year={{ {published[:4] if published else ''} }}
            }}"""

                citation = f"{author_names_for_cite}. {entry.get('title','')}. arXiv:{arxiv_id} ({published[:4] if published else ''})."

                papers.append({
                    "id": arxiv_id,
                    "title": entry.get("title", ""),
                    "authors": authors,
                    "published": published,
                    "arxiv_tag": category_tag,
                    "abs_link": abs_link,
                    "pdf_link": pdf_link,
                    "summary": entry.get("summary", ""),
                    "bibtex": bibtex,
                    "citation": citation
                })

            return papers
                '''

        tools_code = self.call_qwen(tools_prompt)
        write_file(tools_dir / "arxiv_tools.py", tools_code)

        return {"status": "ok", "files": ["tools/arxiv_tools.py"]}

        
    # ---------------------------
    # 3. Generate web app
    # ---------------------------
    def clean_code_output(self, text):
        text = text.replace("```python", "")
        text = text.replace("```html", "")
        text = text.replace("```", "")
        return text
    def _generate_web_app(self):
        app_dir = self.workspace / "webapp"
        templates_dir = app_dir / "templates"
        static_dir = app_dir / "static"

        for d in [app_dir, templates_dir, static_dir]:
            d.mkdir(parents=True, exist_ok=True)

        write_file(app_dir / "__init__.py", "")

        # main.py prompt: import and use fetch_category_rss from tools.arxiv_tools
        main_prompt = """
    Build a FastAPI backend named main.py for "arXiv CS Daily" with these strict rules:

    1) Import fetch_category_rss from tools.arxiv_tools and use it to fetch papers, remember to Import StaticFiles
    2) CATEGORIES = ["cs.AI","cs.CV","cs.CL","cs.LG","cs.NE"]
    3) Routes:
    - '/' : render templates/index.html with variables:
        request, categories, selected, papers
        Where papers is a dict mapping category -> List[paper_dict] (paper_dict as in tools).
    - No internal /paper detail route is necessary; titles link directly to arXiv abs pages.
    4) Templates directory must be configured using Jinja2Templates correctly:
        - Use absolute paths to set TEMPLATES_DIR = BASE_DIR / "templates".
        - Ensure the Jinja2Templates instance is created as:
            templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    5) Mount a safe static directory:
    STATIC_DIR = Path(__file__).parent / "static"
    Create STATIC_DIR if missing and mount at '/static'
    6) Do not transform links; keep paper['abs_link'] and paper['pdf_link'] unchanged so templates can link directly to arXiv.
    7) Provide minimal, well-formed Python code only (no comments/explanations).
    8) Do not await a synchronization function
        """
        main_code = self.call_qwen(main_prompt)
        write_file(app_dir / "main.py", main_code)

        # index.html prompt: must link title -> paper.abs_link and PDF -> paper.pdf_link; authors join
        index_prompt = """
    Create an index.html Jinja2 template.

    Input:
    - categories: list of category strings
    - selected: currently selected category
    - papers: dict mapping category -> list of paper dicts (each has title, authors (List[str]), published YYYY-MM-DD, arxiv_tag, abs_link, pdf_link, bibtex, citation)

    Requirements:
    - For each paper:
    * Title: <a href="{{ paper.abs_link }}" target="_blank">{{ paper.title }}</a>
    * Authors: display as comma-separated names: {{ paper.authors | join(', ') }}
    * Summary: {{ paper.summary }}
    * Published: {{ paper.published }}
    * Tag: display as [{{ paper.arxiv_tag }}]
    * PDF link: <a href="{{ paper.pdf_link }}" target="_blank">PDF</a>
    * Tools: two small buttons:
        - Copy BibTeX: use data-bib="{{ paper.bibtex | tojson }}" or data-bib='{{ paper.bibtex | tojson }}'
        - Copy Citation: use data-cite="{{ paper.citation | tojson }}"
        Buttons should call a simple JS function copyFromData(btn) that reads btn.dataset.bib / btn.dataset.cite and writes to clipboard.
    - DO NOT use any filter like {{ |e('js') }}
    - Use minimal inline JS at bottom to implement copyFromData; no external libraries.
    - Output only valid HTML.

    Layout Requirements:
    - The categories should be displayed in a list on the left-hand side of the page.
    - The left side (categories) is fixed, while the right side (papers) can be scrolled.
    - The papers corresponding to the selected category should be displayed on the right side.
    - Ensure proper styling (minimal CSS to create a two-column layout).

     Visual Design:
    - Use modern CSS design practices:
        - Use Flexbox or CSS Grid for responsive two-column layout.
        - Style the category list to have a clean, button-style look with hover effects.
        - Use cards or panels for displaying papers with a shadow effect and padding.
        - Use a clean color palette with complementary colors for categories and paper cards.
        - Add subtle hover effects for paper items (like light shadows or background color changes).
        - Ensure buttons have clear feedback (like changing color or text when copied).
        - Add spacing between sections and elements for a clean, organized look.
        - Ensure the page is mobile-friendly, using media queries to stack columns on smaller screens.

    """
        index_code = self.call_qwen(index_prompt)
        write_file(templates_dir / "index.html", index_code)

        # copy.js prompt (static) to implement robust copy behavior
        copyjs_prompt = """
    Create a small copy.js file content (plain JavaScript). It should export or define a global function copyFromData(btn)
    that:
    - reads btn.dataset.bib or btn.dataset.cite (may be JSON-escaped strings)
    - if value is JSON (i.e. wrapped via tojson) parse it or decode it safely; otherwise use as-is
    - writes the decoded string to clipboard using navigator.clipboard.writeText
    - updates button text briefly to "Copied!" and then revert
    Provide only valid JavaScript source.
    """
        copyjs_code = self.call_qwen(copyjs_prompt)
        write_file(static_dir / "copy.js", copyjs_code)

        # Also create a minimal paper.html used if needed (optional), but ensure it links to arXiv
        paper_prompt = """
    Create a minimal paper.html Jinja2 template that expects variable 'paper' with fields:
    title, authors (list), published, arxiv_tag, abs_link, pdf_link, bibtex, citation
    It should:
    - show title linking to paper.abs_link target _blank
    - display authors joined by comma
    - show published and tag
    - show a pre block with bibtex and a copy button using data-bib attribute
    - use the same copyFromData(btn) JS function (assume /static/copy.js is included)
    Output only valid HTML.
    """
        paper_code = self.call_qwen(paper_prompt)
        write_file(templates_dir / "paper.html", paper_code)

        return {
            "status": "ok",
            "files": [
                "webapp/main.py",
                "webapp/templates/index.html",
                "webapp/templates/paper.html",
                "webapp/static/copy.js"
            ]
        }
