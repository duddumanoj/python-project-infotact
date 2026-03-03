import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

OPENAI_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """
You are a senior data analyst.

CRITICAL RULES:
1. You are given a pandas DataFrame named df
2. ALWAYS store the final numeric answer in a variable called result
3. result MUST be JSON-serializable
4. ALWAYS print(result)
5. If visualization is requested:
   - Use matplotlib
   - Save the chart using plt.savefig(CHART_PATH)
   - DO NOT call plt.show()
6. Output ONLY raw Python code
7. DO NOT use markdown or explanations
"""


def run_csv_analysis(csv_path: str, user_query: str) -> str:
    df = pd.read_csv(csv_path)

    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=0,
        max_tokens=500
    )

    preview = df.head(5).to_string()

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"""
Here is a preview of the CSV data:

{preview}

User question:
{user_query}

Respond with:
1. Explanation
2. Python pandas code (not executed)
"""
        )
    ]

    response = llm.invoke(messages)
    return response.content
