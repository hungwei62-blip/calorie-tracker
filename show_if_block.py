with open('D:/projects/Calories/app.py', 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()

# Find the if daily in chart section
for i, line in enumerate(lines):
    if 'if daily:' in line and i > 1000:
        print(f'if daily: at line {i+1}')
        # Show 50 lines
        with open('D:/projects/Calories/if_daily_block.txt', 'w', encoding='utf-8') as out:
            for j in range(i, min(i+60, len(lines))):
                out.write(f'{j+1}: {lines[j]}')
        break
