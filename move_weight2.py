import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    lines = f.readlines()

# Find key positions
greeting_end = None
uid_line = None
weight_start = None
weight_end = None

for i, l in enumerate(lines):
    if 'st.markdown(welcome_html, unsafe_allow_html=True)' in l:
        greeting_end = i
    if greeting_end and 'uid = st.session_state.user_id' in l:
        uid_line = i
    if '# ============================================================' in l:
        if i + 1 < len(lines) and '\u9ad4\u91cd' in lines[i+1]:
            weight_start = i
    if weight_start and 'def page_weight' in l:
        weight_end = i - 1
        break

print(f'Greeting end: {greeting_end + 1}')
print(f'UID line: {uid_line + 1}')
print(f'Weight start: {weight_start + 1}')
print(f'Weight end: {weight_end + 1}')

# Extract weight section
weight_section = lines[weight_start:weight_end + 1]

# Build new content
# Keep lines 0 to greeting_end (st.markdown)
# Add uid line
# Skip original uid (now at uid_line)
# Skip weight section (from weight_start)
# Add weight section after uid
# Add everything from weight_end + 1 onwards

new_lines = []
new_lines.extend(lines[:greeting_end + 1])  # up to and including greeting
new_lines.append(lines[uid_line])  # uid line

# Skip from greeting_end + 1 to weight_end (inclusive) - these are original uid section and weight
# Add weight section
for line in weight_section:
    new_lines.append(line)

# Add from weight_end + 1 onwards
new_lines.extend(lines[weight_end + 1:])

with codecs.open('app.py', 'w', 'utf-8') as f:
    f.writelines(new_lines)

print(f'New file has {len(new_lines)} lines')
print('Done')
