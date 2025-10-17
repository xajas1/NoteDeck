import pandas as pd

df = pd.read_excel("../Stud-Monitoring-neu.xlsm", sheet_name="CONTENT", header=3)
print(df.columns)
