from pathlib import Path


class EvalAgent:
    def __init__(self, name, shared, workspace, call_qwen):
        self.name = name
        self.shared = shared
        self.workspace = Path(workspace)
        self.call_qwen = call_qwen

    def act(self, task):
        if task["id"] == "evaluate_webapp":
            return self.evaluate_web_app(task["webapp_result"])
        return {"error": "unknown task"}
    def _read(self, rel):
        p = self.workspace / rel
        if p.exists():
            return p.read_text()
        return ""

    def evaluate_web_app(self, result_dict):
        main_code = self._read("webapp/main.py")
        index_code = self._read("webapp/templates/index.html")
        paper_code = self._read("webapp/templates/paper.html")
        copy_js = self._read("webapp/static/copy.js")

        eval_prompt = f"""
You are a strict Code Evaluation Agent.

Your task is to evaluate a generated FastAPI WebApp.

### Evaluation Rules

1. main.py
- Must import fetch_category_rss from tools.arxiv_tools and StaticFiles
- Must define TEMPLATES_DIR using absolute Path
- Must initialize:
  templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
- Must mount static directory at '/static'
- Route '/' must render index.html
- Variable papers must be dict(category -> list)
- Must NOT use 'await' on synchronous functions

2. index.html
- Two-column layout:
  Left: fixed category list
  Right: scrollable paper list
- Each paper must show:
  - Title link → paper.abs_link
  - Authors joined by comma
  - Summary
  - Published date
  - Tag in format [arxiv_tag]
  - PDF link → paper.pdf_link
- Must contain two buttons:
  - Copy BibTeX with data-bib
  - Copy Citation with data-cite
- Buttons must call copyFromData(btn)
- Must NOT use filters like |e('js')

3. copy.js
- Must define global function copyFromData(btn)
- Must read btn.dataset.bib or btn.dataset.cite
- Must safely handle JSON-escaped strings
- Must use navigator.clipboard.writeText
- Must temporarily change text to "Copied!" then revert

4. paper.html
- Must link title to paper.abs_link
- Must show authors and published + tag
- Must include BibTeX block with copy button
- Must use copyFromData(btn)
- Must include /static/copy.js

5. Overall
- Project should be logically runnable
- Template system must be correctly configured

### Output Format (pure JSON, no comments, no explanation):

{{
  "score_main": <0-10>,
  "score_index": <0-10>,
  "score_js": <0-10>,
  "score_paper": <0-10>,
  "fatal_errors": [],
  "warnings": [],
  "suggestions": [],
  "overall_score": <0-40>
}}

### Code to Evaluate:

=== main.py ===
{main_code}

=== index.html ===
{index_code}

=== paper.html ===
{paper_code}

=== copy.js ===
{copy_js}

Return ONLY valid JSON.
"""

        return self.call_qwen(eval_prompt)
