from pathlib import Path
import json
class AutoRefineAgent:
    def __init__(self, workspace, call_qwen, target_score=36, max_rounds=5):
        self.workspace = Path(workspace)
        self.call_qwen = call_qwen
        self.target_score = target_score
        self.max_rounds = max_rounds
        self.best_score = -1
        self.backup_dir = self.workspace / ".backup_refine"
        self.backup_dir.mkdir(exist_ok=True)

    def _read(self, rel):
        p = self.workspace / rel
        if p.exists():
            return p.read_text(encoding="utf-8")
        return ""

    def _write(self, rel, content):
        p = self.workspace / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    def _safe_write(self, rel, old_code, new_code):
        # 防止写空文件
        if not new_code.strip():
            print(f"[SKIP] Empty output for {rel}")
            return False

        # 防止模型突然大幅度删减代码
        if len(new_code.strip()) < len(old_code.strip()) * 0.4:
            print(f"[SKIP] Output too short, possible corruption: {rel}")
            return False

        self._write(rel, new_code)
        return True

    def _backup(self):
        for f in [
            "webapp/main.py",
            "webapp/templates/index.html",
            "webapp/templates/paper.html",
            "webapp/static/copy.js"
        ]:
            src = self.workspace / f
            if src.exists():
                dst = self.backup_dir / f.replace("/", "_")
                dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    def _restore(self):
        print("[INFO] Rolling back to last stable version...")
        for f in self.backup_dir.iterdir():
            orig = f.name.replace("_", "/")
            dest = self.workspace / orig
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
    def refine(self, eval_agent):
        for round_id in range(1, self.max_rounds + 1):
            print(f"\n[Self-Refine] Round {round_id} start...")

            eval_result = eval_agent.act({
                "id": "evaluate_webapp",
                "webapp_result": {
                    "status": "ok",
                    "files": [
                        "webapp/main.py",
                        "webapp/templates/index.html",
                        "webapp/templates/paper.html",
                        "webapp/static/copy.js"
                    ]
                }
            })

            # 如果返回的是字符串，尝试解析为 JSON
            if isinstance(eval_result, str):
                try:
                    eval_result = json.loads(eval_result)
                except json.JSONDecodeError:
                    print("[WARN] eval_agent returned invalid JSON string. Using empty dict.")
                    eval_result = {}

            print("Eval result:", eval_result)

            overall = eval_result.get("overall_score", -1)

            if overall >= self.target_score:
                print(f"[DONE] Target score {self.target_score} reached.")
                break

            if self.best_score != -1 and overall < self.best_score:
                print(f"[REGRESSION] Score dropped {self.best_score} → {overall}")
                self._restore()
                break

            self.best_score = max(self.best_score, overall)
            self._backup()
            self._apply_refine(eval_result)


    def _apply_refine(self, eval_json):
        main_code = self._read("webapp/main.py")
        index_code = self._read("webapp/templates/index.html")
        paper_code = self._read("webapp/templates/paper.html")
        js_code = self._read("webapp/static/copy.js")

        refine_prompt = f"""
You are a professional software engineer.

You must ONLY apply targeted fixes based on the evaluation report.
Do NOT rewrite everything.
Do NOT delete working code.

Evaluation Report:
{eval_json}

Files follow.

=== main.py ===
{main_code}

=== index.html ===
{index_code}

=== paper.html ===
{paper_code}

=== copy.js ===
{js_code}

Rules:
1. Keep all unrelated code unchanged.
2. Fix only reported errors and warnings.
3. If a file is already correct, output it unchanged.
4. NEVER return empty files.
5. Output pure code only, no markdown, no commentary.

Return results structured exactly like:

---main.py---
(full code)
---index.html---
(full code)
---paper.html---
(full code)
---copy.js---
(full code)
"""

        result = self.call_qwen(refine_prompt)

        # 解析输出
        blocks = {}
        current = None
        buffer = []

        for line in result.splitlines():
            if line.strip().startswith("---") and line.strip().endswith("---"):
                if current and buffer:
                    blocks[current] = "\n".join(buffer).strip()
                    buffer = []
                current = line.strip().replace("---", "")
            else:
                buffer.append(line)

        if current and buffer:
            blocks[current] = "\n".join(buffer).strip()

        # 安全写入
        if "main.py" in blocks:
            self._safe_write("webapp/main.py", main_code, blocks["main.py"])

        if "index.html" in blocks:
            self._safe_write("webapp/templates/index.html", index_code, blocks["index.html"])

        if "paper.html" in blocks:
            self._safe_write("webapp/templates/paper.html", paper_code, blocks["paper.html"])

        if "copy.js" in blocks:
            self._safe_write("webapp/static/copy.js", js_code, blocks["copy.js"])
