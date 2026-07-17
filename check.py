import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'def page_weight' in l:
        print(f'page_weight at line {i+1}')
        print(f'Line before: {repr(lines[i-2][:80])}')
        print(f'Line: {repr(lines[i-1][:80])}')
        break
