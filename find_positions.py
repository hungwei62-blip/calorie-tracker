import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    lines = f.readlines()

# Step 1: Find page_personal bounds
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

# Step 2: Find key positions within page_personal
# - greeting end (st.markdown call)
# - uid line
# - weight section start (after divider, the CSS comment)
# - weight section end (before "# 學員端：體重記錄")

greeting_end = None
uid_line = None
weight_start = None
weight_end = None

for i in range(page_start, page_weight_start):
    if 'st.markdown(welcome_html' in lines[i]:
        greeting_end = i
    if greeting_end is not None and 'uid = st.session_state.user_id' in lines[i]:
        uid_line = i
    # Weight section starts with the CSS comment after divider
    if 'st.divider()' in lines[i]:
        # Check if next line has weight CSS
        if i + 2 < page_weight_start and ('\u6e4d\u6ce2' in lines[i+2] or 'weight-card-container' in lines[i+2]):
            weight_start = i + 1  # Start from the comment line

# Find weight end - before "# 學員端：體重記錄"
for i in range(weight_start if weight_start else page_start, page_weight_start):
    if '\u5b78\u54e1\u7aef\uff1a\u9ad4\u91cd\u8a18\u9304' in lines[i]:
        weight_end = i - 1
        break

print(f'Greeting end: {greeting_end + 1}')
print(f'UID line: {uid_line + 1}')
print(f'Weight start: {weight_start + 1 if weight_start else None}')
print(f'Weight end: {weight_end + 1 if weight_end else None}')
