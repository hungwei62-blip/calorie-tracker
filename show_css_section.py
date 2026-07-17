with open('D:/projects/Calories/app.py', 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()

# Show lines 1000-1050 to see the CSS section
with open('D:/projects/Calories/css_section.txt', 'w', encoding='utf-8') as out:
    for i in range(998, 1055):
        out.write(f'{i+1}: {lines[i]}')
print('Done')
