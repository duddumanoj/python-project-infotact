import os
import subprocess
import uuid
import sys

SANDBOX_DIR = "sandbox"

def execute_python(code: str) -> str:
    """
    Executes Python code in a restricted subprocess
    using the SAME Python interpreter as FastAPI.
    """

    os.makedirs(SANDBOX_DIR, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.py"
    filepath = os.path.join(SANDBOX_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(code)

    try:
        result = subprocess.run(
            [sys.executable, filepath],
            capture_output=True,
            text=True,
            timeout=20
        )

        if result.returncode != 0:
            return f"❌ Python Error:\n{result.stderr}"

        return result.stdout.strip()

    except subprocess.TimeoutExpired:
        return "⏱️ Execution timed out."

    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
