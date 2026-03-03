import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

OPENAI_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """
You are a senior data analyst.

ABSOLUTE RULES (DO NOT BREAK):
1. A pandas DataFrame named df ALREADY EXISTS
2. NEVER create df or sample data
3. NEVER import any libraries
4. NEVER load files or paths
5. NEVER define CHART_PATH
6. ALWAYS store the final numeric answer in a variable called result
7. result MUST be JSON-serializable
8. ALWAYS print(result)
9. If visualization is requested:
   - Use matplotlib
   - You MUST call plt.savefig(CHART_PATH)
   - DO NOT call plt.show()
10. Output ONLY raw Python code
11. DO NOT use markdown, ``` or explanations
"""

def generate_analysis_code(csv_path: str, question: str) -> str:
    df = pd.read_csv(csv_path)
    preview = df.head(5).to_string()

    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=0,
        max_tokens=400
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"""
Here is a preview of the CSV data:

{preview}

User question:
{question}

Return ONLY executable Python code.
"""
        )
    ]

    response = llm.invoke(messages)
    return response.content.strip()
