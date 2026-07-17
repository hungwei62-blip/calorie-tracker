with open('D:/projects/Calories/app.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Check imports
print("=== IMPORTS ===")
if 'import altair as alt' in content:
    print("HAS: import altair as alt")
else:
    print("NO: import altair as alt")

if 'import pandas as pd' in content:
    print("HAS: import pandas as pd")
else:
    print("NO: import pandas as pd")

if 'import plotly' in content:
    print("HAS: import plotly")
else:
    print("NO: import plotly")

# Show chart section
print("\n=== CHART SECTION ===")
idx = content.find('# ----- 1. 準備數據 -----')
if idx == -1:
    idx = content.find('sorted_days = sorted')
if idx != -1:
    with open('D:/projects/Calories/chart_section.txt', 'w', encoding='utf-8') as f:
        f.write(content[idx:idx+5000])
    print("Chart section saved to chart_section.txt")
