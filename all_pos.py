import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'def page_personal' in l:
        print(f'page_personal at line {i+1}')
    if 'def page_weight' in l:
        print(f'page_weight at line {i+1}')
    if 'st.markdown(welcome_html' in l:
        print(f'greeting at line {i+1}')
    if 'uid = st.session_state.user_id' in l:
        print(f'uid at line {i+1}')
