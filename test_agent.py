from agent.agent import run_csv_analysis

response = run_csv_analysis(
    "uploads/sample.csv",
    "Calculate total sales by region and show a bar chart"
)

print(response)
