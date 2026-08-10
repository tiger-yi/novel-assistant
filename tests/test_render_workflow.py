import unittest

from scripts.render_workflow import render_pipeline


class WorkflowRendererTest(unittest.TestCase):
    def test_renders_stages_in_manifest_order(self):
        manifest = {
            "pipelines": {
                "create-chapter": {
                    "stages": [
                        {
                            "name": "preflight",
                            "uses": "state-management",
                            "handler": "preflight",
                            "required": True,
                        },
                        {
                            "name": "conditional-archive",
                            "uses": "archiving-spec",
                            "handler": "transaction-archive",
                            "required": False,
                        },
                    ]
                }
            }
        }

        output = render_pipeline(manifest, "create-chapter")

        self.assertLess(output.index("preflight"), output.index("conditional-archive"))
        self.assertIn("state-management", output)
        self.assertIn("archiving-spec", output)
        self.assertIn("必需", output)
        self.assertIn("可选", output)
        self.assertIn("flowchart TD", output)

    def test_rejects_unknown_pipeline(self):
        with self.assertRaisesRegex(ValueError, "unknown pipeline"):
            render_pipeline({"pipelines": {}}, "missing")

    def test_renders_optimize_init_world_pipeline(self):
        manifest = {
            "pipelines": {
                "optimize-init-world": {
                    "stages": [
                        {
                            "name": "full-audit",
                            "uses": "originality-audit",
                            "handler": "semantic-gate",
                            "required": True,
                        },
                        {
                            "name": "full-reaudit",
                            "uses": "originality-audit",
                            "handler": "semantic-gate",
                            "required": False,
                        },
                    ]
                }
            }
        }

        output = render_pipeline(manifest, "optimize-init-world")

        self.assertLess(output.index("full-audit"), output.index("full-reaudit"))
        self.assertIn("originality-audit", output)


if __name__ == "__main__":
    unittest.main()
