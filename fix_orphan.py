import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    lines = f.readlines()

# Find and remove orphaned lines after button removal (lines 2051-2052 in original, now empty line at 2050)
for i, l in enumerate(lines):
    stripped = l.strip()
    if stripped == 'st.session_state.page = "體重記錄"' or stripped == 'st.rerun()':
        print(f'Removing orphaned line at line {i+1}')
        lines[i] = ''

with codecs.open('app.py', 'w', 'utf-8') as f:
    f.writelines(lines)
print('Done')
