import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    lines = f.readlines()

# Find page_personal bounds
page_start = None
page_end = None
for i, l in enumerate(lines):
    if 'def page_personal()' in l:
        page_start = i
        print(f'page_personal starts at line {i+1}')
    elif page_start is not None and l.startswith('def '):
        page_end = i
        print(f'page_personal ends at line {i+1}')
        break

# Within page_personal, find key positions
for i in range(page_start, page_end):
    l = lines[i]
    if 'st.markdown(welcome_html' in l:
        print(f'Greeting HTML at line {i+1}')
    if 'uid = st.session_state.user_id' in l:
        print(f'UID at line {i+1}')
    if '# ===' in l and i + 1 < page_end and '\u9ad4\u91cd' in lines[i+1]:
        print(f'Weight section starts at line {i+1}')
    if 'def page_weight' in l:
        print(f'page_weight found inside page_personal at line {i+1}')
