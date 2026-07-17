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

print(f'page_personal: {page_start+1} to {page_weight_start}')

# Find key lines
for i in range(page_start, page_weight_start):
    l = lines[i]
    if 'st.header("\U0001f4ca \u4eca\u65e5\u6458\u8981")' in l:
        print(f'Summary header at line {i+1}: {repr(l)}')
    if 'st.subheader("\u2696\ufe0f \u9ad4\u91cd")' in l:
        print(f'Weight subheader at line {i+1}: {repr(l)}')
    if 'st.markdown(welcome_html' in l:
        print(f'Greeting at line {i+1}')
    if 'uid = st.session_state.user_id' in l and i > page_start + 10:
        print(f'UID in page_personal at line {i+1}')
    if 'st.divider()' in l and i > 1800:
        print(f'Divider before weight at line {i+1}')
    if 'weight-card-container' in l:
        print(f'Weight CSS at line {i+1}')
