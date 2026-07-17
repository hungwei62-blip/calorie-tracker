import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    lines = f.readlines()

# Find page_personal bounds
page_start = None
page_end = None
for i, l in enumerate(lines):
    if 'def page_personal()' in l:
        page_start = i
    elif page_start is not None and l.startswith('def '):
        page_end = i
        break

print(f'page_personal: {page_start+1} to {page_end}')

# Find key positions within page_personal
greeting_end = None
uid_line = None
weight_start = None
weight_end = None

for i in range(page_start, page_end):
    l = lines[i]
    if 'st.markdown(welcome_html, unsafe_allow_html=True)' in l:
        greeting_end = i
    if greeting_end is not None and 'uid = st.session_state.user_id' in l and uid_line is None:
        uid_line = i
    # Weight section starts after divider and comment
    if 'st.divider()' in l and i + 3 < page_end:
        # Check if next lines contain weight CSS
        if '\u6e4d\u6ce2' in lines[i+2] or 'weight-card-container' in lines[i+2]:
            weight_start = i + 1  # Start from the comment line
            print(f'Found potential weight start at line {i+2}')
    if weight_start and 'def page_weight' in l:
        weight_end = i - 1
        break

# If we did not find weight_start via divider, search for weight-card-container
if not weight_start:
    for i in range(page_start, page_end):
        if 'weight-card-container' in lines[i]:
            # Go back to find the comment
            for j in range(i-1, page_start, -1):
                if '# ===' in lines[j] or 'st.divider()' in lines[j]:
                    weight_start = j + 1
                    break
            if not weight_start:
                weight_start = i - 1
            break

print(f'Greeting end: {greeting_end + 1 if greeting_end else None}')
print(f'UID line: {uid_line + 1 if uid_line else None}')
print(f'Weight start: {weight_start + 1 if weight_start else None}')
print(f'Weight end: {weight_end + 1 if weight_end else None}')

if weight_start and weight_end and greeting_end:
    # Extract weight section
    weight_section = lines[weight_start:weight_end + 1]
    print(f'Weight section has {len(weight_section)} lines')
    
    # Build new content
    new_lines = []
    new_lines.extend(lines[:greeting_end + 1])  # up to and including greeting st.markdown
    new_lines.append('\n')
    new_lines.append(lines[uid_line])  # uid line
    new_lines.append('\n')
    new_lines.extend(weight_section)  # weight section
    new_lines.extend(lines[weight_end + 1:page_end])  # rest of page_personal (excluding weight)
    new_lines.extend(lines[page_end:])  # rest of file
    
    with codecs.open('app.py', 'w', 'utf-8') as f:
        f.writelines(new_lines)
    
    print(f'Done! New file has {len(new_lines)} lines')
else:
    print('Could not find all positions')
