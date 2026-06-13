from pydantic import BaseModel

class ScenarioProfile(BaseModel):
    tenant_id: str
    domain: str
    services: list[str]
    teams: list[str]
    requirements: list[str]
    bugs: list[str]
    incident_themes: list[str]
    eval_queries: list[str]
