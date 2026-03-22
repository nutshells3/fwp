from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.dev.path_setup import activate, repo_root

activate()

from formal_protocol import MiniJsonSchemaValidator, generate_assets, load_schema, validate_exchange


class ProtocolContractsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = repo_root()

    def test_generated_assets_are_current(self) -> None:
        generate_assets(check=True)

    def test_schema_headers_exist(self) -> None:
        schemas = sorted((self.root / "packages" / "formal-protocol" / "schemas").glob("*.json"))
        self.assertGreaterEqual(len(schemas), 7)
        for path in schemas:
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertIn("$defs", data)

    def test_descriptors_validate(self) -> None:
        validator = MiniJsonSchemaValidator()
        descriptor_schema = load_schema("descriptor.schema.json")["$defs"]["Descriptor"]
        for path in sorted((self.root / "packages" / "formal-protocol" / "examples" / "descriptors").glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            validator.validate(payload, descriptor_schema)

    def test_schema_fixtures_validate(self) -> None:
        validator = MiniJsonSchemaValidator()
        fixtures = json.loads(
            (self.root / "packages" / "formal-protocol" / "examples" / "schema-fixtures.json").read_text(encoding="utf-8")
        )
        fixture_schemas = {
            "backendDescriptor": load_schema("entities.schema.json")["$defs"]["BackendDescriptor"],
            "workspaceHandle": load_schema("entities.schema.json")["$defs"]["WorkspaceHandle"],
            "documentHandle": load_schema("entities.schema.json")["$defs"]["DocumentHandle"],
            "targetRef": load_schema("entities.schema.json")["$defs"]["TargetRef"],
            "snapshotRef": load_schema("entities.schema.json")["$defs"]["SnapshotRef"],
            "goalState": load_schema("results.schema.json")["$defs"]["GoalState"],
            "diagnostic": load_schema("results.schema.json")["$defs"]["Diagnostic"],
            "dependencySlice": load_schema("results.schema.json")["$defs"]["DependencySlice"],
            "protocolError": load_schema("results.schema.json")["$defs"]["ProtocolError"],
            "buildUpdate": load_schema("events.schema.json")["$defs"]["BuildUpdateParams"],
            "goalsUpdate": load_schema("events.schema.json")["$defs"]["GoalsUpdateParams"],
            "diagnosticsUpdate": load_schema("events.schema.json")["$defs"]["DiagnosticsUpdateParams"],
            "probeUpdate": load_schema("events.schema.json")["$defs"]["ProbeUpdateParams"],
            "auditUpdate": load_schema("events.schema.json")["$defs"]["AuditUpdateParams"],
        }
        for fixture_name, schema in fixture_schemas.items():
            validator.validate(fixtures[fixture_name], schema)

    def test_transcripts_validate(self) -> None:
        transcripts = sorted((self.root / "packages" / "formal-protocol" / "examples" / "transcripts").glob("*.json"))
        self.assertGreaterEqual(len(transcripts), 19)
        for path in transcripts:
            validate_exchange(json.loads(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
