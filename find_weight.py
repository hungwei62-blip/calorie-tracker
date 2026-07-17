import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    lines = f.readlines()

# Find key lines
greeting_end = None
weight_start = None
weight_end = None
summary_header = None
weight_subheader = None

for i, l in enumerate(lines):
    if 'st.markdown(welcome_html, unsafe_allow_html=True)' in l:
        greeting_end = i
    if 'st.header(\"\U0001f4ca \u4eca\u65e5\u6458\u8981\")' in l:
        summary_header = i
    if '# ============================================================' in l:
        # Check if this is the start of weight section
        if i + 1 < len(lines) and 'st.subheader' in lines[i+1] and '\u9ad4\u91cd' in lines[i+1]:
            weight_start = i
    if 'st.subheader' in l and '\u2696\ufe0f' in l and '\u9ad4\u91cd' in l:
        weight_subheader = i
    if weight_start and i > weight_start and 'def page_weight' in l:
        weight_end = i - 1
        break

print(f'Greeting end: {greeting_end + 1}')
print(f'Summary header: {summary_header + 1 if summary_header else None}')
print(f'Weight subheader: {weight_subheader + 1 if weight_subheader else None}')
print(f'Weight start: {weight_start + 1 if weight_start else None}')
print(f'Weight end: {weight_end + 1 if weight_end else None}')
