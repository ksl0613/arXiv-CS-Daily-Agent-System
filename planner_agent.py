# agents/planner_agent.py
from .agent_base import AgentBase
from typing import Dict, Any

class PlannerAgent(AgentBase):
    def act(self, task: Dict[str, Any]) -> Dict[str, Any]:
        goal = task.get('goal', '')

        plan = [
            {
                'id': 'init_repo',
                'desc': 'create project structure and requirements.txt',
                'actor': 'CodeAgent'
            },
            {
                'id': 'fetch_arxiv',
                'desc': 'implement arxiv fetch utility',
                'actor': 'CodeAgent'
            },
            {
                'id': 'generate_web_app',  # ✅ 必须和 CodeAgent.act 对齐
                'desc': 'implement FastAPI webapp for arXiv CS Daily',
                'actor': 'CodeAgent'
            },
            {
                'id': 'evaluate_webapp',   # ✅ 必须和 EvalAgent.act 对齐
                'desc': 'run eval agent on generated webapp',
                'actor': 'EvalAgent'
            },
            {
                'id': 'refine_webapp',
                'desc': 'self-refine webapp based on evaluation result',
                'actor': 'EvalAgent'
            }
        ]

        self.shared_state['plan'] = plan
        return {
            'status': 'planned',
            'plan': plan
        }
