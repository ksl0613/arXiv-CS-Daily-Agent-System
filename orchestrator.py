# orchestrator.py
from agents.planner_agent import PlannerAgent
from agents.code_agent import CodeAgent
from agents.eval_agent import EvalAgent
from agents.refine_agent import AutoRefineAgent
from tools.fs_tools import ensure_workspace
import os

def run_demo():
    workspace = os.path.abspath("workspace")
    ensure_workspace(workspace)

    shared = {}

    pl = PlannerAgent("planner", shared)
    ca = CodeAgent("coder", shared, workspace=workspace)
    ev = EvalAgent("evaluator", shared, workspace=workspace, call_qwen=ca.call_qwen)

    # Self-Refine Agent
    refiner = AutoRefineAgent(
        workspace=workspace,
        call_qwen=ca.call_qwen,
        target_score=36,   # 你要的目标分
        max_rounds=3
    )

    # 1. Planning Phase
    plan_res = pl.act({"goal": "build arXiv CS Daily webapp"})
    print("Plan:", plan_res["plan"])

    # 2. Dispatch Tasks
    for task in plan_res["plan"]:

        # ===== CodeAgent =====
        if task["actor"] == "CodeAgent":
            r = ca.act(task)
            print("CodeAgent did:", task["id"], r)

        # ===== EvalAgent or Self-Refine =====
        elif task["actor"] == "EvalAgent":

            print("\n[INFO] Entering self-refinement loop...")

            # 直接对 workspace 已有代码进行自我修复
            refiner.refine(ev)

            print("\n[INFO] Self-refinement finished.")

if __name__ == "__main__":
    run_demo()
