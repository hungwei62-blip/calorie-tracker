with open('D:/projects/Calories/app.py', 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()

with open('D:/projects/Calories/error_area.txt', 'w', encoding='utf-8') as out:
    for i in range(1020, 1040):
        out.write(f'{i+1}: {repr(lines[i])}\n')
print('Done')
