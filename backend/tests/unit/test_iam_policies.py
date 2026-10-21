"""Unit tests validating AWS IAM policy structures and least-privilege compliance.

Owned by Member 01 (Cloud Security Architect & DevOps).
Validates infra/aws/iam/policies/ and infra/aws/iam/trust-policies/ against security guardrails.
"""

import json
import re
from pathlib import Path
import unittest


class TestAWSIAMPolicies(unittest.TestCase):
    """Verifies that all IAM policy files follow least-privilege principles."""

    @classmethod
    def setUpClass(cls):
        # Locate infra/aws/iam/ directory relative to repository root
        cls.repo_root = Path(__file__).resolve().parents[3]
        cls.policies_dir = cls.repo_root / "infra" / "aws" / "iam" / "policies"
        cls.trust_dir = cls.repo_root / "infra" / "aws" / "iam" / "trust-policies"

    def _load_json(self, file_path: Path) -> dict:
        self.assertTrue(file_path.exists(), f"Policy file not found: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_all_policy_files_valid_json(self):
        """Ensure every policy file in the directory is well-formed JSON."""
        policy_files = list(self.policies_dir.glob("*.json"))
        self.assertGreater(len(policy_files), 0, "No policy files found to validate.")
        for policy_file in policy_files:
            data = self._load_json(policy_file)
            self.assertEqual(data.get("Version"), "2012-10-17")
            self.assertIn("Statement", data)
            self.assertIsInstance(data["Statement"], list)

    def test_trust_policies_valid_json_and_deployment_alternatives(self):
        """Ensure trust policies are well-formed and clearly define deployment alternatives."""
        ecs_file = self.trust_dir / "ecs-task-trust-policy.json"
        irsa_file = self.trust_dir / "irsa-trust-policy.json"

        # Verify Option A (ECS)
        ecs_data = self._load_json(ecs_file)
        self.assertEqual(ecs_data.get("Version"), "2012-10-17")
        ecs_stmt = ecs_data["Statement"][0]
        self.assertEqual(ecs_stmt["Principal"], {"Service": "ecs-tasks.amazonaws.com"})
        self.assertEqual(ecs_stmt["Action"], "sts:AssumeRole")
        self.assertTrue(ecs_stmt.get("Sid", "").startswith("DeploymentOptionA_"))

        # Verify Option B (EKS IRSA)
        irsa_data = self._load_json(irsa_file)
        self.assertEqual(irsa_data.get("Version"), "2012-10-17")
        irsa_stmt = irsa_data["Statement"][0]
        self.assertIn("Federated", irsa_stmt["Principal"])
        self.assertEqual(irsa_stmt["Action"], "sts:AssumeRoleWithWebIdentity")
        self.assertIn("Condition", irsa_stmt)
        self.assertTrue(irsa_stmt.get("Sid", "").startswith("DeploymentOptionB_"))

    def test_no_wildcard_actions(self):
        """Ensure no statement grants wildcard actions like * or service:*."""
        for policy_file in self.policies_dir.glob("*.json"):
            data = self._load_json(policy_file)
            for stmt in data.get("Statement", []):
                actions = stmt.get("Action", [])
                if isinstance(actions, str):
                    actions = [actions]
                for action in actions:
                    self.assertNotEqual(
                        action,
                        "*",
                        f"Wildcard action found in {policy_file.name}: {action}",
                    )
                    self.assertFalse(
                        action.endswith(":*"),
                        f"Full service wildcard found in {policy_file.name}: {action}",
                    )

    def test_wildcard_resources_only_where_required_by_aws(self):
        """Verify that 'Resource': '*' is strictly confined to actions lacking resource-level support.

        Legitimate AWS-required wildcards:
        1. bedrock:ListFoundationModels (AWS Bedrock listing API operates at account/region level)
        2. cloudwatch:PutMetricData (CloudWatch metrics have no ARNs; scoped via cloudwatch:namespace Condition)

        Every other action must have a specific, scoped ARN.
        """
        legitimate_wildcard_actions = {
            "bedrock:ListFoundationModels",
            "cloudwatch:PutMetricData",
        }

        for policy_file in self.policies_dir.glob("*.json"):
            data = self._load_json(policy_file)
            for stmt in data.get("Statement", []):
                resources = stmt.get("Resource", [])
                if isinstance(resources, str):
                    resources = [resources]

                if "*" in resources:
                    actions = stmt.get("Action", [])
                    if isinstance(actions, str):
                        actions = [actions]
                    for action in actions:
                        self.assertIn(
                            action,
                            legitimate_wildcard_actions,
                            f"Action {action} in {policy_file.name} incorrectly uses 'Resource': '*'",
                        )
                    # When cloudwatch:PutMetricData is present with '*', verify namespace condition guardrail
                    if "cloudwatch:PutMetricData" in actions:
                        self.assertIn(
                            "Condition",
                            stmt,
                            f"cloudwatch:PutMetricData in {policy_file.name} missing Condition guardrail",
                        )
                        condition = stmt["Condition"]
                        self.assertEqual(
                            condition.get("StringEquals", {}).get(
                                "cloudwatch:namespace"
                            ),
                            "Gitlexa",
                        )

    def test_no_administrative_or_destructive_permissions(self):
        """Disallow IAM management or deletion permissions in backend policies."""
        forbidden_prefixes = ("iam:", "organizations:", "account:", "sts:AssumeRole")
        for policy_file in self.policies_dir.glob("*.json"):
            data = self._load_json(policy_file)
            for stmt in data.get("Statement", []):
                actions = stmt.get("Action", [])
                if isinstance(actions, str):
                    actions = [actions]
                for action in actions:
                    for prefix in forbidden_prefixes:
                        self.assertFalse(
                            action.startswith(prefix),
                            f"Forbidden action {action} in {policy_file.name}",
                        )
                    self.assertNotIn(
                        "delete",
                        action.lower(),
                        f"Destructive action {action} found in {policy_file.name}",
                    )

    def test_no_hardcoded_aws_credentials_or_account_ids(self):
        """Ensure no real AWS account IDs or secret keys are in the policy files."""
        # Standard AWS account ID regex: 12 continuous digits
        account_id_pattern = re.compile(r"\b\d{12}\b")
        # AWS Access Key pattern: AKIA...
        access_key_pattern = re.compile(r"\bAKIA[0-9A-Z]{16}\b")

        all_files = list(self.policies_dir.glob("*.json")) + list(
            self.trust_dir.glob("*.json")
        )
        for p_file in all_files:
            content = p_file.read_text(encoding="utf-8")
            self.assertIsNone(
                account_id_pattern.search(content),
                f"Potential real AWS account ID found in {p_file.name}",
            )
            self.assertIsNone(
                access_key_pattern.search(content),
                f"Potential AWS access key found in {p_file.name}",
            )

    def test_bedrock_policy_least_privilege(self):
        """Verify Amazon Bedrock policy is restricted to approved Claude foundation models."""
        policy_path = self.policies_dir / "bedrock-invoke-policy.json"
        data = self._load_json(policy_path)
        statements = {s.get("Sid"): s for s in data.get("Statement", [])}

        # 1. Invocation scoped to Claude foundation models
        self.assertIn("BedrockModelInvocation", statements)
        invoke_stmt = statements["BedrockModelInvocation"]
        self.assertIn("bedrock:InvokeModel", invoke_stmt["Action"])
        self.assertIn("bedrock:InvokeModelWithResponseStream", invoke_stmt["Action"])
        resources = invoke_stmt["Resource"]
        if isinstance(resources, str):
            resources = [resources]
        for res in resources:
            self.assertTrue(
                "foundation-model/anthropic.claude" in res,
                f"Resource {res} not scoped to approved Claude foundation models",
            )

        # 2. Model details inspection scoped to Claude models
        self.assertIn("BedrockGetFoundationModelDetails", statements)
        get_stmt = statements["BedrockGetFoundationModelDetails"]
        self.assertIn("bedrock:GetFoundationModel", get_stmt["Action"])
        self.assertEqual(
            get_stmt["Resource"],
            ["arn:aws:bedrock:<AWS_REGION>::foundation-model/anthropic.claude-*"],
        )

        # 3. Model listing has legitimate AWS-required wildcard
        self.assertIn(
            "BedrockListFoundationModelsNoResourceLevelSupport", statements
        )
        list_stmt = statements[
            "BedrockListFoundationModelsNoResourceLevelSupport"
        ]
        self.assertEqual(list_stmt["Action"], ["bedrock:ListFoundationModels"])
        self.assertEqual(list_stmt["Resource"], "*")

    def test_secrets_manager_policy_least_privilege(self):
        """Verify Secrets Manager read policy is scoped to gitlexa/* namespace."""
        policy_path = self.policies_dir / "secrets-manager-read-policy.json"
        data = self._load_json(policy_path)
        statements = {s.get("Sid"): s for s in data.get("Statement", [])}

        self.assertIn("SecretsManagerGitlexaReadAccess", statements)
        sec_stmt = statements["SecretsManagerGitlexaReadAccess"]
        self.assertIn("secretsmanager:GetSecretValue", sec_stmt["Action"])
        self.assertEqual(
            sec_stmt["Resource"],
            "arn:aws:secretsmanager:<AWS_REGION>:<AWS_ACCOUNT_ID>:secret:gitlexa/*",
        )

        # KMS Decrypt must have secretsmanager ViaService condition
        self.assertIn("KMSDecryptForSecretsManager", statements)
        kms_stmt = statements["KMSDecryptForSecretsManager"]
        self.assertEqual(kms_stmt["Action"], ["kms:Decrypt"])
        self.assertEqual(
            kms_stmt["Condition"],
            {
                "StringEquals": {
                    "kms:ViaService": "secretsmanager.<AWS_REGION>.amazonaws.com"
                }
            },
        )

    def test_cloudwatch_logging_policy_least_privilege(self):
        """Verify CloudWatch logging is scoped to /gitlexa/* log groups."""
        policy_path = self.policies_dir / "cloudwatch-logging-policy.json"
        data = self._load_json(policy_path)
        statements = {s.get("Sid"): s for s in data.get("Statement", [])}

        self.assertIn("CloudWatchLogGroupManagement", statements)
        group_stmt = statements["CloudWatchLogGroupManagement"]
        self.assertEqual(
            group_stmt["Resource"],
            "arn:aws:logs:<AWS_REGION>:<AWS_ACCOUNT_ID>:log-group:/gitlexa/*",
        )


if __name__ == "__main__":
    unittest.main()
