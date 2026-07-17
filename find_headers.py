import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'st.header' in l and '今日摘要' in l:
        print(f'Summary header at line {i+1}: {repr(l)}')
    if 'st.subheader' in l and '\u9ad4\u91cd' in l:
        print(f'Weight subheader at line {i+1}: {repr(l)}')
