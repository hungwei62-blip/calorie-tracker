with open('D:/projects/Calories/app.py', 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()

# Find and show the chart-card CSS
for i, line in enumerate(lines):
    if '.chart-card' in line and '{' in line:
        print(f'Line {i+1}: {line.rstrip()}')
        # Show next few lines
        for j in range(i, min(i+3, len(lines))):
            print(f'{j+1}: {lines[j].rstrip()}')
        break
