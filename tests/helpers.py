import json
import os
import subprocess
import sys
import tempfile

MODULES_DIR = os.path.join(os.path.dirname(__file__), "..", "plugins", "modules")


def run_module(module_name: str, args: dict) -> dict:
    """
    Invoke a module script the same way Ansible would: as a subprocess fed a
    JSON args file, exercising the real AnsibleModule argument validation and
    check-mode handling instead of just the inner conversion functions.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"ANSIBLE_MODULE_ARGS": args}, f)
        argfile = f.name
    try:
        result = subprocess.run(
            [sys.executable, os.path.join(MODULES_DIR, f"{module_name}.py"), argfile],
            capture_output=True, text=True, timeout=30,
        )
    finally:
        os.unlink(argfile)
    assert result.stdout, f"module produced no output; stderr was: {result.stderr}"
    return json.loads(result.stdout)
