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
    if 'st.markdown(welcome_html' in l:
        lines_info['greeting'] = i
    if 'uid = st.session_state.user_id' in l and i > page_start + 10:
        lines_info['uid'] = i
    if 'st.divider()' in l and i > 1800:
        lines_info['divider'] = i
    if 'weight-card-container' in l:
        lines_info['weight_css'] = i

print(f'greeting: line {lines_info.get("greeting", "not found")+1 if lines_info.get("greeting") is not None else "N/A"}')
print(f'uid: line {lines_info.get("uid", "not found")+1 if lines_info.get("uid") is not None else "N/A"}')
print(f'divider: line {lines_info.get("divider", "not found")+1 if lines_info.get("divider") is not None else "N/A"}')
print(f'weight_css: line {lines_info.get("weight_css", "not found")+1 if lines_info.get("weight_css") is not None else "N/A"}')
print(f'page_weight: line {page_weight_start+1}')
