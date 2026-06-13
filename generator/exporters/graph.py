import json
import os
import re
from pathlib import Path

import networkx as nx
from networkx.readwrite import json_graph
from networkx.readwrite import json_graph

from generator.core.engine import generator


def export_to_graph(
    generator: generator, base_dir: str, tenant_id: str = "tenant_default"
):
    root = Path(base_dir) / tenant_id / "knowledge_graph"
    os.makedirs(root, exist_ok=True)

    G = nx.DiGraph()

    # 1. Add Nodes
    for e in generator.employees:
        G.add_node(
            e.id,
            label="Employee",
            name=f"{e.profile.get('firstName', '')} {e.profile.get('lastName', '')}",
            role=e.profile.get("title", "Unknown"),
        )
    for t in generator.teams:
        G.add_node(t.id, label="Team", name=t.name)
    for s in generator.services:
        G.add_node(s.id, label="Service", name=s.name)
    for r in generator.repositories:
        G.add_node(r.id, label="Repository", name=r.name)
    for a in generator.apis:
        G.add_node(a.id, label="API", name=a.name)
    for adr in generator.adrs:
        G.add_node(adr.id, label="ADR", title=adr.title)
    for rb in generator.runbooks:
        G.add_node(rb.id, label="Runbook", title=rb.title)
    for r in generator.requirements:
        G.add_node(r.id, label="Requirement", title=r.title)

    for tk in generator.tickets:
        G.add_node(
            tk.key,
            label="Ticket",
            title=tk.fields.summary,
            type=tk.fields.issuetype.name,
        )

    for c in generator.commits:
        G.add_node(c.sha, label="Commit", hash=c.sha)

    for pr in generator.pull_requests:
        G.add_node(str(pr.number), label="PullRequest", title=pr.title)

    for rel in generator.releases:
        G.add_node(rel.id, label="Release", version=rel.version)

    for dep in generator.deployments:
        G.add_node(dep.id, label="Deployment", service=dep.service_id)

    for m in generator.metrics:
        G.add_node(m.id, label="Metric", name=m.name)
    for l in generator.logs:
        G.add_node(l.id, label="Log", level=l.level)
    for a in generator.alerts:
        G.add_node(a.id, label="Alert", name=a.summary)

    for i in generator.incidents:
        G.add_node(i.id, label="Incident", title=i.title)
    for pm in generator.postmortems:
        G.add_node(pm.id, label="Postmortem", title=pm.title)

    for sm in generator.slack_messages:
        G.add_node(sm.client_msg_id, label="SlackMessage", content=sm.text)

    for tc in generator.test_cases:
        G.add_node(tc.id, label="TestCase", title=tc.title)

    # 2. Add Edges
    for t in generator.teams:
        for m in t.members:
            G.add_edge(m, t.id, type="BELONGS_TO")

    for s in generator.services:
        G.add_edge(s.team_id, s.id, type="OWNS")

    for r in generator.repositories:
        G.add_edge(r.service_id, r.id, type="HAS_REPO")

    for adr in generator.adrs:
        G.add_edge(adr.service_id, adr.id, type="HAS_ADR")

    for rb in generator.runbooks:
        G.add_edge(rb.service_id, rb.id, type="HAS_RUNBOOK")

    for a in generator.apis:
        G.add_edge(a.service_id, a.id, type="EXPOSES")

    for r in generator.requirements:
        G.add_edge(r.owner_id, r.id, type="OWNS")
        for sid in r.affected_service_ids:
            G.add_edge(r.id, sid, type="AFFECTS")

    for tk in generator.tickets:
        if tk.fields.assignee:
            G.add_edge(tk.fields.assignee.accountId, tk.key, type="ASSIGNED_TO")
        if tk.fields.customfield_requirement_id:
            G.add_edge(tk.key, tk.fields.customfield_requirement_id, type="IMPLEMENTS")
        for sid in tk.fields.customfield_service_ids:
            G.add_edge(tk.key, sid, type="RELATES_TO")

    for c in generator.commits:
        # Match Ticket key from commit message
        ticket_key = c.commit.message.split(":")[0] if ":" in c.commit.message else None
        if ticket_key and ticket_key.startswith("TICKET-"):
            G.add_edge(c.sha, ticket_key, type="FIXES")

    for pr in generator.pull_requests:
        G.add_edge(pr.user.login, str(pr.number), type="AUTHORED")
        ticket_key = (
            pr.body.replace("Implements ", "")
            if "Implements TICKET-" in pr.body
            else None
        )
        if ticket_key:
            G.add_edge(str(pr.number), ticket_key, type="RELATES_TO")
        for sha in pr.commits:
            G.add_edge(str(pr.number), sha, type="CONTAINS")

    for rel in generator.releases:
        G.add_edge(rel.repository_id, rel.id, type="PRODUCES")
        for pr_id in rel.pr_ids:
            G.add_edge(pr_id, rel.id, type="INCLUDED_IN")

    for dep in generator.deployments:
        G.add_edge(dep.id, dep.service_id, type="DEPLOYS_TO")
        G.add_edge(dep.release_id, dep.id, type="TRIGGERS")

    for m in generator.metrics:
        G.add_edge(m.service_id, m.id, type="EMITS_METRIC")
    for l in generator.logs:
        G.add_edge(l.service_id, l.id, type="EMITS_LOG")

    for a in generator.alerts:
        service_id = a.service.get("id") if isinstance(a.service, dict) else None
        if service_id:
            G.add_edge(service_id, a.id, type="EMITS_ALERT")

    for i in generator.incidents:
        for sid in i.impacted_service_ids:
            G.add_edge(i.id, sid, type="IMPACTS")
        for aid in i.alert_ids:
            G.add_edge(aid, i.id, type="CAUSES")

    for pm in generator.postmortems:
        G.add_edge(pm.incident_id, pm.id, type="ANALYZES")

    for tc in generator.test_cases:
        G.add_edge(tc.id, tc.requirement_id, type="TESTS")
        if tc.service_id != "none":
            G.add_edge(tc.id, tc.service_id, type="TESTS")

    # Sanitize attributes to prevent lxml surrogate errors
    for node, data in G.nodes(data=True):
        for k, v in data.items():
            if isinstance(v, str):
                data[k] = re.sub(r"[\ud800-\udfff]", "", v)
    for u, v, data in G.edges(data=True):
        for k, val in data.items():
            if isinstance(val, str):
                data[k] = re.sub(r"[\ud800-\udfff]", "", val)

    # 3. Export
    nx.write_graphml(G, root / "knowledge_graph.graphml")

    data = json_graph.node_link_data(G, edges="edges")
    with open(root / "knowledge_graph.json", "w") as f:
        json.dump(data, f, indent=2)

    print(f"Exported Knowledge Graph to {root}")
