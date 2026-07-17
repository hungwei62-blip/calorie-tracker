with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find page_personal start and the next function after it
page_personal_start = None
next_func_start = None

for i, line in enumerate(lines):
    if 'def page_personal()' in line:
        page_personal_start = i
    elif page_personal_start is not None and line.startswith('def '):
        next_func_start = i
        break

print(f'page_personal: lines {page_personal_start+1} to {next_func_start}')

# Remove st.header and st.subheader in page_personal
modified_lines = []
for i, line in enumerate(lines):
    if page_personal_start <= i < next_func_start:
        if 'st.header(' in line and '今日摘要' in line:
            continue
        if 'st.subheader(' in line and '今日完成率' in line:
            continue
    modified_lines.append(line)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(modified_lines)

print('Done! Removed headers in page_personal.')
