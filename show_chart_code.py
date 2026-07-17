with open('D:/projects/Calories/app.py', 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()

# Find the chart section
for i, line in enumerate(lines):
    if '深色卡片趨勢圖' in line:
        with open('D:/projects/Calories/chart_code.txt', 'w', encoding='utf-8') as out:
            for j in range(i, min(i+80, len(lines))):
                out.write(f'{j+1}: {lines[j]}')
        print(f'Found at line {i+1}')
        break
