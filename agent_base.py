# agents/agent_base.py
from abc import ABC, abstractmethod
from typing import Any, Dict

class AgentBase(ABC):
    def __init__(self, name: str, shared_state: Dict[str, Any]):
        self.name = name
        self.shared_state = shared_state

    @abstractmethod
    def act(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a step for the given task. Return a result dict."""
        pass
