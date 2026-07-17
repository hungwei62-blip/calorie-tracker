import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    lines = f.readlines()

# Find key positions more carefully
for i, l in enumerate(lines):
    if 'st.markdown(welcome_html' in l:
        print(f'Greeting HTML at line {i+1}')
    if 'st.header(' in l and '今日摘要' in l:
        print(f'Summary header at line {i+1}: {repr(l[:60])}')
    if 'uid = st.session_state.user_id' in l:
        print(f'UID line at line {i+1}')
    if '# ===' in l and i + 1 < len(lines) and '\u9ad4\u91cd' in lines[i+1]:
        print(f'Weight section start at line {i+1}')
    if 'def page_weight' in l:
        print(f'page_weight at line {i+1}')
