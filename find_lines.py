import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'st.subheader' in l and '\u9ad4\u91cd' in l:
        print(f'Weight subheader at line {i+1}')
    if 'st.header' in l and '\u4eca\u65e5\u6458\u8981' in l:
        print(f'Daily summary header at line {i+1}')
    if 'def page_personal' in l:
        print(f'page_personal at line {i+1}')
    if 'st.markdown(welcome_html' in l:
        print(f'Welcome HTML at line {i+1}')
    if 'st.subheader("\u2696\ufe0f \u9ad4\u91cd")' in l:
        print(f'Weight with emoji at line {i+1}')
