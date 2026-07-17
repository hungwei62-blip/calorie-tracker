import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'subheader' in l and '\u9ad4\u91cd' in l:
        print(f'Found at line {i}')
        lines[i] = ''
        break

with codecs.open('app.py', 'w', 'utf-8') as f:
    f.writelines(lines)
print('Done')
