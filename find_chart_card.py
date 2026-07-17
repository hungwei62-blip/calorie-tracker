with open('D:/projects/Calories/app.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Find the chart-card CSS
idx = content.find('.chart-card {')
if idx != -1:
    print('Found chart-card at:', idx)
    # Show next 500 chars
    print(content[idx:idx+500])
