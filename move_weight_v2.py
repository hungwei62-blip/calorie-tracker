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

# Find uid line within page_personal
uid_line = None
for i in range(page_start, page_weight_start):
    if 'uid = st.session_state.user_id' in lines[i] and i > page_start + 10:
        uid_line = i
        break

# Find divider before weight section
divider_line = None
for i in range(page_start, page_weight_start):
    if 'st.divider()' in lines[i] and i > 1800:
        divider_line = i
        break

print(f'uid at line {uid_line + 1}')
print(f'divider at line {divider_line + 1}')
print(f'page_weight at line {page_weight_start + 1}')

# Extract weight section (from divider to page_weight - 1)
weight_section = lines[divider_line:page_weight_start]
print(f'Weight section has {len(weight_section)} lines')

# Build new content
new_lines = []
new_lines.extend(lines[:uid_line + 1])  # up to and including uid
new_lines.append('\n')  # add newline
new_lines.extend(weight_section)  # weight section
new_lines.extend(lines[page_weight_start:])  # rest of file

with codecs.open('app.py', 'w', 'utf-8') as f:
    f.writelines(new_lines)

print(f'Done! New file has {len(new_lines)} lines')
