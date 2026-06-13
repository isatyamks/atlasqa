import json
import os
from pathlib import Path

from generator.core.engine import generator


def export_to_files(
    generator: generator, base_dir: str, tenant_id: str = "tenant_default"
):
    root = Path(base_dir) / tenant_id

    folders = [
        "employees",
        "teams",
        "services",
        "apis",
        "requirements",
        "tickets",
        "commits",
        "pull_requests",
        "deployments",
        "incidents",
        "slack",
        "design_docs",
        "test_cases",
        "meeting_notes",
        "repositories",
        "adrs",
        "runbooks",
        "releases",
        "metrics",
        "logs",
        "alerts",
        "postmortems",
    ]

    for folder in folders:
        os.makedirs(root / folder, exist_ok=True)

    def _write_json(folder, filename, obj):
        path = root / folder / f"{filename}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(obj.model_dump(mode="json"), f, indent=2)

    for emp in generator.employees:
        _write_json("okta/employees", emp.id, emp)
    for team in generator.teams:
        _write_json("okta/teams", team.id, team)
    for svc in generator.services:
        _write_json("services", svc.id, svc)
    for repo in generator.repositories:
        _write_json("repositories", repo.id, repo)
    for api in generator.apis:
        _write_json("apis", api.id, api)
    for adr in generator.adrs:
        _write_json("confluence/adrs", adr.id, adr)
    for rb in generator.runbooks:
        _write_json("runbooks", rb.id, rb)
    for req in generator.requirements:
        _write_json("requirements", req.id, req)
    for t in generator.tickets:
        _write_json("tickets", t.key, t)
    for c in generator.commits:
        _write_json("commits", c.sha, c)
    for pr in generator.pull_requests:
        _write_json("pull_requests", str(pr.id), pr)
    for rel in generator.releases:
        _write_json("releases", rel.id, rel)
    for dep in generator.deployments:
        _write_json("deployments", dep.id, dep)
    for m in generator.metrics:
        _write_json("datadog/metrics", m.id, m)
    for l in generator.logs:
        _write_json("datadog/logs", l.id, l)
    for a in generator.alerts:
        _write_json("pagerduty/alerts", a.id, a)
    for inc in generator.incidents:
        _write_json("incidents", inc.id, inc)
    for pm in generator.postmortems:
        _write_json("postmortems", pm.id, pm)
    for sm in generator.slack_messages:
        _write_json("slack", sm.client_msg_id, sm)
    for doc in generator.design_docs:
        _write_json("design_docs", doc.id, doc)
    for tc in generator.test_cases:
        _write_json("test_cases", tc.id, tc)
    for mn in generator.meeting_notes:
        _write_json("meeting_notes", mn.id, mn)

    print(f"Exported file generator to {root}")
