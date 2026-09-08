"""Check Python, XML, manifest references and the ACL header without installing Odoo."""

import ast
import csv
from pathlib import Path
import xml.etree.ElementTree as ET


root = Path(__file__).resolve().parents[1]
module = root / "sale_mrp_attachment_address"
python_files = sorted(module.rglob("*.py")) + sorted((root / "scripts").glob("*.py"))
for filename in python_files:
    compile(filename.read_bytes(), str(filename), "exec")
xml_files = sorted(module.rglob("*.xml"))
for filename in xml_files:
    ET.parse(filename)
manifest = ast.literal_eval((module / "__manifest__.py").read_text())
assert manifest["version"].startswith("19.0.")
assert "sale_mrp" in manifest["depends"]
for filename in manifest["data"]:
    assert (module / filename).is_file(), filename
with (module / "security/ir.model.access.csv").open(newline="") as stream:
    rows = list(csv.reader(stream))
assert rows == [["id", "name", "model_id:id", "group_id:id", "perm_read", "perm_write", "perm_create", "perm_unlink"]]
print(f"PASS: {len(python_files)} Python files, {len(xml_files)} XML files, manifest paths and ACL header.")
