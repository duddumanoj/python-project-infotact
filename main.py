from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import uuid
import shutil
import json

from agent.code_generator import generate_analysis_code
from agent.sandbox_executor import execute_python


# ====================
# App Initialization
# ====================
app = FastAPI(title="StatBot Pro API")

UPLOAD_DIR = "uploads"
STATIC_DIR = "static"
CHART_DIR = os.path.join(STATIC_DIR, "charts")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHART_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ====================
# Request Models
# ====================
class AnalyzeRequest(BaseModel):
    file_id: str
    question: str


# ====================
# Helpers
# ====================
def clean_llm_code(code: str) -> str:
    """Remove markdown fences if LLM adds them."""
    code = code.strip()
    if code.startswith("```"):
        code = code.replace("```python", "").replace("```", "")
    return code.strip()


def sanitize_llm_code(code: str) -> str:
    """
    Strip anything the LLM must not control.
    """
    sanitized_lines = []
    for line in code.splitlines():
        stripped = line.strip()
        if stripped.startswith("import "):
            continue
        if "CHART_PATH" in stripped:
            continue
        sanitized_lines.append(line)
    return "\n".join(sanitized_lines).strip()


def validate_generated_code(code: str):
    """
    Validate only data logic — environment is controlled by backend.
    """
    forbidden_patterns = [
        "pd.DataFrame",
        "data =",
        "read_csv",
        "open(",
        "os.",
        "sys.",
        "subprocess",
    ]

    for pattern in forbidden_patterns:
        if pattern in code:
            raise HTTPException(
                status_code=400,
                detail=f"Unsafe generated code detected: '{pattern}'"
            )


# ====================
# Routes
# ====================
@app.get("/")
def health_check():
    return {"status": "StatBot Pro is running"}


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported"
        )

    file_id = f"{uuid.uuid4().hex}.csv"
    file_path = os.path.join(UPLOAD_DIR, file_id)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to save file"
        )

    return {
        "file_id": file_id,
        "original_name": file.filename,
        "message": "File uploaded successfully"
    }


@app.post("/analyze")
def analyze_csv(request: AnalyzeRequest):
    csv_path = os.path.join(UPLOAD_DIR, request.file_id)

    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="File not found")

    # 1️⃣ Generate LLM code
    python_code = clean_llm_code(
        generate_analysis_code(csv_path, request.question)
    )

    # 2️⃣ Sanitize + validate
    python_code = sanitize_llm_code(python_code)
    validate_generated_code(python_code)

    # 3️⃣ Prepare chart path
    chart_filename = f"chart_{uuid.uuid4().hex}.png"
    chart_path = os.path.join(CHART_DIR, chart_filename)

    # 4️⃣ Controlled execution environment
    safe_code = f"""
import pandas as pd
import matplotlib.pyplot as plt

CHART_PATH = r"{chart_path}"

df = pd.read_csv(r"{csv_path}")

{python_code}

# Auto-save chart if any plotting occurred
if plt.get_fignums():
    plt.savefig(CHART_PATH)

plt.close('all')
"""

    # 5️⃣ Execute safely
    raw_output = execute_python(safe_code)

    # 6️⃣ Parse output
    try:
        structured_output = json.loads(raw_output)
    except Exception:
        structured_output = raw_output

    # 7️⃣ Detect chart
    chart_url = None
    if os.path.exists(chart_path):
        chart_url = f"/static/charts/{chart_filename}"

    return {
        "question": request.question,
        "generated_code": python_code,
        "result": structured_output,
        "chart_url": chart_url
    }
