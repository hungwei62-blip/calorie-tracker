with open('D:/projects/Calories/app.py', 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()

# Find imports
for i, line in enumerate(lines[:20]):
    if 'import' in line and ('alt' in line or 'pandas' in line or 'matplotlib' in line):
        print(f'{i+1}: {line.rstrip()}')
