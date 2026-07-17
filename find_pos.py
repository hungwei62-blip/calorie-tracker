import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    lines = f.readlines()

# Find key positions
page_start = None
page_end = None
for i, l in enumerate(lines):
    if 'def page_personal()' in l:
        page_start = i
    elif page_start is not None and l.startswith('def '):
        page_end = i
        break

print(f'page_personal: {page_start+1} to {page_end}')

# Find greeting end (st.markdown(welcome_html...))
greeting_end = None
uid_line = None
weight_comment_start = None
for i in range(page_start, page_end):
    if 'st.markdown(welcome_html, unsafe_allow_html=True)' in lines[i]:
        greeting_end = i
    if greeting_end is not None and 'uid = st.session_state.user_id' in lines[i]:
        uid_line = i
        break

# Find weight section start (after divider, the comment about CSS)
for i in range(uid_line + 1, page_end):
    if '# \u6e4d\u6ce2\u7c21\u78ba\u5b9a\u4f4d\u8207\u6392\u7248\u7684 CSS' in lines[i] or 'weight-card-container' in lines[i]:
        weight_comment_start = i - 1  # Start from the comment or style block
        break

print(f'Greeting end: {greeting_end + 1 if greeting_end else None}')
print(f'UID line: {uid_line + 1 if uid_line else None}')
print(f'Weight start: {weight_comment_start + 1 if weight_comment_start else None}')
print(f'Page end: {page_end}')
