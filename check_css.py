with open('D:/projects/Calories/app.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Find the CSS section
idx = content.find('.chart-card {')
if idx != -1:
    print('Found chart-card at:', idx)
    print('Content:', repr(content[idx:idx+200]))
