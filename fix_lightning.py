import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    lines = f.readlines()

# Find page_personal start and end
page_start = None
page_end = None
for i, l in enumerate(lines):
    if 'def page_personal()' in l:
        page_start = i
    elif page_start is not None and l.startswith('def '):
        page_end = i
        break

print(f'page_personal: {page_start+1} to {page_end}')

# Find the weight button and its context within page_personal
in_weight_section = False
button_line = None
for i in range(page_start, page_end if page_end else len(lines)):
    l = lines[i]
    if 'st.button' in l and 'weight_lightning_btn' in l:
        button_line = i
        print(f'Found button at line {i+1}')
        break

if button_line:
    # Remove the button line and the two lines after it (if they are the orphaned st.session_state and st.rerun)
    lines[button_line] = ''
    # Check if next lines need removal
    if button_line + 1 < len(lines) and 'st.session_state' in lines[button_line + 1]:
        lines[button_line + 1] = ''
    if button_line + 2 < len(lines) and 'st.rerun()' in lines[button_line + 2]:
        lines[button_line + 2] = ''
    
    with codecs.open('app.py', 'w', 'utf-8') as f:
        f.writelines(lines)
    print('Done')
