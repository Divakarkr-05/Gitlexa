"""Controlled evaluation scenarios for Gitlexa."""

from app.evidence.schemas import Evidence, EvidenceBundle, EvidenceType


def ci_failure_scenario() -> EvidenceBundle:
    """Create a known CI failure scenario."""

    bundle = EvidenceBundle(repository="evaluation/demo-repository")

    bundle.add(
        Evidence(
            id="issue-101",
            type=EvidenceType.ISSUE,
            title="Deployment is blocked",
            description="Production deployment is failing.",
        )
    )

    bundle.add(
        Evidence(
            id="pr-42",
            type=EvidenceType.PULL_REQUEST,
            title="Fix deployment configuration",
            description="Updates deployment configuration.",
        )
    )

    bundle.add(
        Evidence(
            id="ci-900",
            type=EvidenceType.CI_RUN,
            title="Build failed",
            description="The deployment pipeline failed.",
            metadata={"status": "failure"},
        )
    )

    bundle.add(
        Evidence(
            id="commit-abc",
            type=EvidenceType.COMMIT,
            title="Update deployment config",
            description="Changes deployment configuration.",
        )
    )

    return bundle