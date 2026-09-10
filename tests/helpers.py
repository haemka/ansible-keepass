import json
import os
import subprocess
import sys
import tempfile

MODULES_DIR = os.path.join(os.path.dirname(__file__), "..", "plugins", "modules")

# Set by `KEEPASS_TEST_COVERAGE=1` so module subprocesses report coverage too; see
# the "Testing" section in README.md for the full coverage workflow. Deliberately not
# named COVERAGE_RUN - coverage.py itself sets that env var (to "true") on every
# process it runs, so reusing the name would silently collide with its own signal.
COVERAGE_ENABLED = os.environ.get("KEEPASS_TEST_COVERAGE") == "1"


def run_module(module_name: str, args: dict) -> dict:
    """
    Invoke a module script the same way Ansible would: as a subprocess fed a
    JSON args file, exercising the real AnsibleModule argument validation and
    check-mode handling instead of just the inner conversion functions.
    """
    script = os.path.join(MODULES_DIR, f"{module_name}.py")
    if COVERAGE_ENABLED:
        cmd = [sys.executable, "-m", "coverage", "run", "--parallel-mode", script]
    else:
        cmd = [sys.executable, script]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"ANSIBLE_MODULE_ARGS": args}, f)
        argfile = f.name
    try:
        result = subprocess.run(cmd + [argfile], capture_output=True, text=True, timeout=30)
    finally:
        os.unlink(argfile)
    assert result.stdout, f"module produced no output; stderr was: {result.stderr}"
    return json.loads(result.stdout)
