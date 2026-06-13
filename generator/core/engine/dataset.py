from typing import List

from pydantic import BaseModel, Field

from generator.core.models import (
    API,
    Alert,
    ArchitectureDecisionRecord,
    Deployment,
    DesignDoc,
    Employee,
    GithubCommit,
    GithubPullRequest,
    Incident,
    JiraIssue,
    Log,
    MeetingNote,
    Metric,
    Postmortem,
    Release,
    Repository,
    Requirement,
    Runbook,
    Service,
    SlackMessage,
    Team,
    TestCase,
)

# uncomment the corresponding imports below to avoid NameError:
# from .simulation_engine import SimulationEngine


class generator(BaseModel):
    employees: List[Employee] = Field(default_factory=list)
    teams: List[Team] = Field(default_factory=list)
    services: List[Service] = Field(default_factory=list)
    repositories: List[Repository] = Field(default_factory=list)
    apis: List[API] = Field(default_factory=list)
    adrs: List[ArchitectureDecisionRecord] = Field(default_factory=list)
    runbooks: List[Runbook] = Field(default_factory=list)
    requirements: List[Requirement] = Field(default_factory=list)
    tickets: List[JiraIssue] = Field(default_factory=list)
    commits: List[GithubCommit] = Field(default_factory=list)
    pull_requests: List[GithubPullRequest] = Field(default_factory=list)
    releases: List[Release] = Field(default_factory=list)
    deployments: List[Deployment] = Field(default_factory=list)
    metrics: List[Metric] = Field(default_factory=list)
    logs: List[Log] = Field(default_factory=list)
    alerts: List[Alert] = Field(default_factory=list)
    incidents: List[Incident] = Field(default_factory=list)
    postmortems: List[Postmortem] = Field(default_factory=list)
    slack_messages: List[SlackMessage] = Field(default_factory=list)
    design_docs: List[DesignDoc] = Field(default_factory=list)
    test_cases: List[TestCase] = Field(default_factory=list)
    meeting_notes: List[MeetingNote] = Field(default_factory=list)
