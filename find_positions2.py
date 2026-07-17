import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    lines = f.readlines()

# Find page_personal and page_weight bounds
page_start = None
page_weight_start = None

for i, l in enumerate(lines):
    if 'def page_personal()' in l:
        page_start = i
    if 'def page_weight()' in l:
        page_weight_start = i
        break

print(f'page_personal: {page_start+1} to {page_weight_start}')
print(f'page_weight: {page_weight_start+1}')

# Find key positions
greeting_end = None
uid_line = None
weight_section_start = None  # The CSS st.markdown line

for i in range(page_start, page_weight_start):
    if 'st.markdown(welcome_html' in lines[i]:
        greeting_end = i
    if greeting_end is not None and 'uid = st.session_state.user_id' in lines[i]:
        uid_line = i
    # Find the weight CSS st.markdown line
    if weight_section_start is None and 'st.markdown("""' in lines[i] and i > 1700:
        # Check if this is the weight card CSS by looking at the next line
        if i + 1 < len(lines) and 'weight-card-container' in lines[i+1]:
            weight_section_start = i
            print(f'Found weight CSS at line {i+1}')

print(f'Greeting end: {greeting_end + 1}')
print(f'UID line: {uid_line + 1}')
print(f'Weight section start: {weight_section_start + 1 if weight_section_start else None}')
print(f'Weight section ends before line: {page_weight_start + 1}')
