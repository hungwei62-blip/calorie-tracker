with open('D:/projects/Calories/app.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Find .chart-header
idx = content.find('.chart-header')
if idx != -1:
    print('Found .chart-header at:', idx)
    print('Content:', repr(content[idx:idx+200]))
