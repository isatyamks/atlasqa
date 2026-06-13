from typing import Literal
from datetime import datetime
from pydantic import BaseModel
from generator.core.config.profile import ScenarioProfile


class SimulationConfig(BaseModel):
    seed: int = 42
    size: Literal["small", "medium", "large"] = "small"
    domain: str = "Enterprise e-commerce platform"
    start_date: datetime
    end_date: datetime
    scenario: ScenarioProfile | None = None

    @property
    def scale_factor(self) -> int:
        if self.size == "small":
            return 1
        elif self.size == "medium":
            return 10
        elif self.size == "large":
            return 100
        return 1
