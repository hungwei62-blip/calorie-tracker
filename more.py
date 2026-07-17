with open('D:/projects/Calories/app.py', 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()

with open('D:/projects/Calories/more_lines.txt', 'w', encoding='utf-8') as out:
    for j in range(1038, 1100):
        out.write(f'{j+1}: {lines[j]}')
print('Done')
