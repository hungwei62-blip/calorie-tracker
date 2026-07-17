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

# Find key lines
lines_info = {}
for i in range(page_start, page_weight_start):
    l = lines[i]
    if 'st.header' in l and '今日摘要' in l:
        lines_info['summary'] = i
    if 'st.subheader' in l and '體重' in l:
        lines_info['weight_sub'] = i
    if 'st.markdown(welcome_html' in l:
        lines_info['greeting'] = i
    if 'uid = st.session_state.user_id' in l and i > page_start + 10:
        lines_info['uid'] = i
    if 'st.divider()' in l and i > 1800:
        lines_info['divider'] = i
    if 'weight-card-container' in l:
        lines_info['weight_css'] = i

for k, v in lines_info.items():
    print(f'{k}: line {v+1}')

# Delete headers
new_lines = []
for i, l in enumerate(lines):
    if i == lines_info.get('summary'):
        continue
    if i == lines_info.get('weight_sub'):
        continue
    new_lines.append(l)

with codecs.open('app.py', 'w', 'utf-8') as f:
    f.writelines(new_lines)

print('Headers deleted')
