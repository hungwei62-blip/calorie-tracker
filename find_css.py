with open('D:/projects/Calories/app.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Find the CSS block and show it
start = content.find('<style>')
end = content.find('</style>', start)
if start != -1 and end != -1:
    css = content[start:end+8]
    with open('D:/projects/Calories/current_css.txt', 'w', encoding='utf-8') as f:
        f.write(css)
    print(f'CSS from {start} to {end}')
