from abc import ABC, abstractmethod
from typing import Any, Dict, List


class PipelineStep(ABC):
    """
    Abstract base class for a single pipeline processing step.
    Each step receives the full payload dict and returns an updated version.
    """

    name: str = "base_step"

    @abstractmethod
    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process the payload and return the (possibly mutated) payload."""
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


class Pipeline:
    """
    Composable post-processing pipeline.
    Steps are executed sequentially; each step output is the next step input.
    """

    def __init__(self, steps: List[PipelineStep] = None):
        self.steps: List[PipelineStep] = steps or []

    def add_step(self, step: PipelineStep) -> "Pipeline":
        self.steps.append(step)
        return self

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        for step in self.steps:
            payload = step.process(payload)
        return payload

    def __repr__(self) -> str:
        step_names = [s.name for s in self.steps]
        return f"Pipeline(steps={step_names})"
