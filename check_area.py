with open('D:/projects/Calories/app.py', 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()

# Find and show the area chart lines
for i, line in enumerate(lines):
    if 'mark_area' in line:
        print(f'Line {i+1}: {line.rstrip()}')
    if '.chart-card {' in line:
        print(f'Line {i+1}: {line.rstrip()}')
