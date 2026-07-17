import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    lines = f.readlines()

new_lines = []
for l in lines:
    # Skip headers with specific patterns
    if 'st.header' in l and '\u4eca\u65e5\u6458\u8981' in l:
        continue
    if 'st.subheader' in l and '\u9ad4\u91cd' in l:
        continue
    new_lines.append(l)

with codecs.open('app.py', 'w', 'utf-8') as f:
    f.writelines(new_lines)

print(f'Done! {len(lines)} -> {len(new_lines)} lines')
