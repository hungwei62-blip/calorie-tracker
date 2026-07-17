with open('D:/projects/Calories/app.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 1. Add plotly import if not present
if 'import plotly.graph_objects as go' not in content:
    content = content.replace(
        'import matplotlib.pyplot as _plt',
        'import matplotlib.pyplot as _plt\nimport plotly.graph_objects as go'
    )
    print('1. Added plotly import')

# 2. Remove altair import
if 'import altair as alt' in content:
    content = content.replace('import altair as alt\n', '')
    print('2. Removed altair import')

# Read the new chart code
with open('D:/projects/Calories/plotly_final.txt', 'r', encoding='utf-8') as f:
    new_chart_code = f.read()

# 3. Find and replace the chart section
# Find "if daily:" in the chart section (around line 1048)
if_daily_pos = content.find('if daily:', content.find('每日攝取趨勢'))
if if_daily_pos == -1:
    print('ERROR: Could not find chart section')
    exit(1)

# Find where to stop (before water bar chart)
water_pos = content.find('st.subheader("💧 水量趨勢")', if_daily_pos)
if water_pos == -1:
    print('ERROR: Could not find water section')
    exit(1)

# Replace the old code
content = content[:if_daily_pos] + new_chart_code + content[water_pos:]
print(f'3. Replaced chart code ({if_daily_pos} to {water_pos})')

# 4. Update CSS
old_css = '.chart-card { background: #1e1e38 !important; border-radius: 20px !important; padding: 20px !important; margin: 10px 0 !important; box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important; }'
new_css = '.chart-card { background: #1e1e38 !important; border-radius: 20px !important; padding: 20px 20px 5px 20px !important; margin: 15px 0 !important; box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important; box-sizing: border-box !important; }'

if old_css in content:
    content = content.replace(old_css, new_css)
    print('4. Updated chart-card CSS')
else:
    print('WARNING: Old CSS not found')

# Update .chart-header margin
old_header = '.chart-header { display: flex !important; justify-content: space-between !important; align-items: center !important; margin-bottom: 16px !important; }'
new_header = '.chart-header { display: flex !important; justify-content: space-between !important; align-items: center !important; margin-bottom: 5px !important; }'

if old_header in content:
    content = content.replace(old_header, new_header)
    print('5. Updated chart-header margin')
else:
    print('WARNING: Old header CSS not found')

with open('D:/projects/Calories/app.py', 'w', encoding='utf-8-sig', newline='') as f:
    f.write(content)

print('Saved')
