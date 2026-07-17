import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    lines = f.readlines()

# Find page_personal and page_weight
page_start = None
page_weight_start = None

for i, l in enumerate(lines):
    if 'def page_personal()' in l:
        page_start = i
    if 'def page_weight()' in l:
        page_weight_start = i
        break

print(f'page_personal starts at {page_start + 1}')
print(f'page_weight starts at {page_weight_start + 1}')
print(f'Weight section is from line {1912} to {page_weight_start}')

# Extract weight section (lines 1911 to page_weight_start - 1)
weight_section = lines[1911:page_weight_start]
print(f'Weight section has {len(weight_section)} lines')

# Build new content
# Keep lines 0 to 1551 (greeting end)
# Add weight section
# Skip lines 1552 to page_weight_start - 1 (original uid and weight section)
# Keep lines from page_weight_start onwards

new_lines = []
new_lines.extend(lines[:1552])  # up to and including greeting st.markdown
new_lines.append('\n')  # add a newline
new_lines.extend(weight_section)  # weight section
new_lines.extend(lines[page_weight_start:])  # rest of file (from page_weight onwards)

with codecs.open('app.py', 'w', 'utf-8') as f:
    f.writelines(new_lines)

print(f'Done! New file has {len(new_lines)} lines')
