import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    lines = f.readlines()

# Find page_personal bounds
page_start = None
page_weight_start = None

for i, l in enumerate(lines):
    if 'def page_personal()' in l:
        page_start = i
    if 'def page_weight()' in l:
        page_weight_start = i
        break

print(f'page_personal: {page_start+1} to {page_weight_start}')

# Find the lines to delete within page_personal
lines_to_delete = []
for i in range(page_start, page_weight_start):
    l = lines[i]
    # Check for summary header
    if l.strip().startswith('st.header') and '\u4eca\u65e5\u6458\u8981' in l:
        lines_to_delete.append(i)
        print(f'Will delete summary header at line {i+1}')
    # Check for weight subheader
    if l.strip().startswith('st.subheader') and '\u9ad4\u91cd' in l:
        lines_to_delete.append(i)
        print(f'Will delete weight subheader at line {i+1}')

# Create new content
new_lines = []
for i, l in enumerate(lines):
    if i not in lines_to_delete:
        new_lines.append(l)

with codecs.open('app.py', 'w', 'utf-8') as f:
    f.writelines(new_lines)

print(f'Deleted {len(lines_to_delete)} lines. New file has {len(new_lines)} lines')
