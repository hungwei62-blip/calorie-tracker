with open("D:/projects/Calories/app.py", "r", encoding="utf-8-sig") as f:
    content = f.read()

# 1. Add plotly import
if "import plotly.graph_objects as go" not in content:
    content = content.replace(
        "import matplotlib.pyplot as _plt",
        "import matplotlib.pyplot as _plt\nimport plotly.graph_objects as go"
    )

# 2. Remove altair import
if "import altair as alt" in content:
    content = content.replace("import altair as alt\n", "")

# 3. Read new chart code
with open("D:/projects/Calories/plotly_simple.txt", "r", encoding="utf-8") as f:
    new_code = f.read()

# 4. Find and replace chart section
chart_idx = content.find("每日攝取趨勢")
if_daily_idx = content.find("if daily:", chart_idx)
water_idx = content.find("st.subheader(\"💧 水量趨勢\")", if_daily_idx)

print(f"Chart section: if_daily={if_daily_idx}, water={water_idx}")

# 5. Replace
content = content[:if_daily_idx] + new_code + content[water_idx:]

# 6. Update CSS
old_css = ".chart-card { background: #1e1e38 !important; border-radius: 20px !important; padding: 24px !important; margin: 15px 0 !important; box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important; display: block !important; width: 100% !important; box-sizing: border-box !important; }"
new_css = ".chart-card { background: #1e1e38 !important; border-radius: 20px !important; padding: 20px 20px 5px 20px !important; margin: 15px 0 !important; box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important; box-sizing: border-box !important; }"
content = content.replace(old_css, new_css)

with open("D:/projects/Calories/app.py", "w", encoding="utf-8-sig", newline="") as f:
    f.write(content)

print("Done")
