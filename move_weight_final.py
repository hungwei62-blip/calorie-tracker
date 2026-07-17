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

# Find uid line within page_personal (first occurrence after greeting)
greeting_end = None
uid_line = None
for i in range(page_start, page_weight_start):
    if 'st.markdown(welcome_html' in lines[i]:
        greeting_end = i
    if greeting_end is not None and 'uid = st.session_state.user_id' in lines[i]:
        uid_line = i
        break

# Find weight section start (the st.markdown line with CSS)
weight_start = None
for i in range(page_start, page_weight_start):
    if 'st.markdown("""' in lines[i]:
        # Check if this is the weight CSS by looking at content
        if i + 1 < len(lines) and 'weight-card-container' in lines[i+1]:
            weight_start = i
            break

print(f'page_personal: {page_start+1} to {page_weight_start}')
print(f'Greeting end: {greeting_end + 1}')
print(f'UID line: {uid_line + 1}')
print(f'Weight section start: {weight_start + 1 if weight_start else None}')
print(f'Weight section end: {page_weight_start}')

# Extract weight section
weight_section = lines[weight_start:page_weight_start]
print(f'Weight section has {len(weight_section)} lines')

# Build new content
# Keep lines 0 to uid_line (inclusive)
# Add weight section
# Skip old weight section (from weight_start to page_weight_start - 1)
# Add rest of file from page_weight_start onwards

new_lines = []
new_lines.extend(lines[:uid_line + 1])  # up to and including uid line
new_lines.append('\n')  # add newline
new_lines.extend(weight_section)  # weight section
new_lines.extend(lines[page_weight_start:])  # rest of file

with codecs.open('app.py', 'w', 'utf-8') as f:
    f.writelines(new_lines)

print(f'Done! New file has {len(new_lines)} lines')
