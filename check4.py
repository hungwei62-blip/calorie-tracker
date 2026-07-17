import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'def page_personal()' in l:
        print(f'page_personal at line {i+1}')
    if 'def page_weight()' in l:
        print(f'page_weight at line {i+1}')
