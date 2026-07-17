import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    lines = f.readlines()

# Find key positions
page_start = None
page_weight_start = None
greeting_end = None
uid_line = None
weight_start = None

for i, l in enumerate(lines):
    if 'def page_personal()' in l:
        page_start = i
    if 'def page_weight()' in l:
        page_weight_start = i
    if 'st.markdown(welcome_html' in l:
        greeting_end = i
    if greeting_end is not None and 'uid = st.session_state.user_id' in l:
        uid_line = i
    # Find weight section start (st.markdown with weight CSS)
    if weight_start is None and 'weight-card-container' in l:
        # Go back to find the st.markdown line
        for j in range(i-1, page_start, -1):
            if 'st.markdown("""' in lines[j] or "st.markdown(\"\"\"" in lines[j]:
                weight_start = j
                break
        if weight_start is None:
            weight_start = i

print(f'Greeting end: {greeting_end + 1}')
print(f'UID line: {uid_line + 1}')
print(f'Weight start: {weight_start + 1}')
print(f'Weight end before: {page_weight_start}')
