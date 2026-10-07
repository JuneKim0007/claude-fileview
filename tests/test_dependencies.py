"""The axis rules, enforced: each axis may import only the axes listed for it, and only config may
import yaml. A violation fails the suite instead of waiting for a review to notice it."""
import ast
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "fileview"
SHARED = {"locations"}                                   # plain constants every axis may read
ALLOWED = {
    "model": set(),
    "capture": {"model", "store"},
    "store": {"model"},
    "transcript": set(),
    "rules": {"model"},
    "config": {"rules", "model"},
    "render": {"rules", "model"},
    "control": set(),
    "lifecycle": {"control"},
    "supervisor": {"lifecycle", "control", "config"},    # config: keeps captures.json in step
    "app": {"*"},                                        # composition roots wire everything together
}
YAML_ALLOWED = {"config"}


def imports_of(path: Path) -> set[str]:
    found = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
            found.update(f"{node.module}.{alias.name}" for alias in node.names)
        elif isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
    return found


class AxisRules(unittest.TestCase):
    def test_every_axis_is_declared(self):
        axes = {p.name for p in PACKAGE.iterdir() if p.is_dir() and p.name != "__pycache__"}
        self.assertEqual(axes, set(ALLOWED), "a new axis needs its allowed imports declared here")

    def test_axes_import_only_what_they_are_allowed(self):
        problems = []
        for axis, allowed in ALLOWED.items():
            if "*" in allowed:
                continue
            for path in (PACKAGE / axis).rglob("*.py"):
                for module in imports_of(path):
                    parts = module.split(".")
                    if parts[0] != "fileview" or len(parts) < 2:
                        continue
                    target = parts[1]
                    if target in (axis, *SHARED) or target in allowed or target not in ALLOWED:
                        continue
                    problems.append(f"{path.relative_to(PACKAGE)} imports {module}")
        self.assertEqual(problems, [])

    def test_only_config_imports_yaml(self):
        offenders = [str(p.relative_to(PACKAGE)) for p in PACKAGE.rglob("*.py")
                     if p.relative_to(PACKAGE).parts[0] not in YAML_ALLOWED
                     and any(m == "yaml" or m.startswith("yaml.") for m in imports_of(p))]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
