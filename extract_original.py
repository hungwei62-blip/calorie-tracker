import subprocess
result = subprocess.run(['git', 'show', 'HEAD:app.py'], capture_output=True, text=True, cwd='D:/projects/Calories')
lines = result.stdout.split('\n')

# Find the line numbers
for i, line in enumerate(lines):
    if '每日攝取趨勢' in line:
        print(f'Chart header at line {i+1}')
        # Show context
        with open('D:/projects/Calories/original_chart.txt', 'w', encoding='utf-8') as out:
            for j in range(i, min(i+100, len(lines))):
                out.write(f'{j+1}: {repr(lines[j])}\n')
        break
