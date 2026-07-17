with open('D:/projects/Calories/app.py', 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()

# Find the if daily around chart section
for i, line in enumerate(lines):
    if 'if daily:' in line and i > 1000:
        with open('D:/projects/Calories/check_structure.txt', 'w', encoding='utf-8') as out:
            for j in range(i, min(i+55, len(lines))):
                leading = len(lines[j]) - len(lines[j].lstrip())
                out.write(f'{j+1} (indent={leading}): {lines[j]}')
        print(f'Found if daily at line {i+1}')
        break
