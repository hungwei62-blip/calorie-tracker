import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Step 1: Remove emoji from header
content = content.replace('st.header("\U0001f4ca 今日摘要")', 'st.header("今日摘要")')

# Step 2: Find and extract weight section
# Find the weight section pattern
weight_pattern = r'(    # ============================================================\n    st\.subheader\("\u2696\ufe0f 體重"\).*?st\.write\("<div style=\'height: 40px;\'></div>", unsafe_allow_html=True\)\n\n\n    st\.markdown\(\'</div>\', unsafe_allow_html=True\)\n)'
weight_match = re.search(weight_pattern, content, re.DOTALL)

if weight_match:
    weight_section = weight_match.group(1)
    print(f'Found weight section')
    
    # Remove weight section from original location
    content = content[:weight_match.start()] + content[weight_match.end():]
    
    # Find greeting section end (after st.markdown(welcome_html...))
    greeting_pattern = r'(st\.markdown\(welcome_html, unsafe_allow_html=True\))'
    greeting_match = re.search(greeting_pattern, content)
    
    if greeting_match:
        insert_pos = greeting_match.end()
        # Insert weight section after greeting
        content = content[:insert_pos] + '\n\n' + weight_section + content[insert_pos:]
        
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print('Done! Weight section moved successfully.')
    else:
        print('Could not find greeting section.')
else:
    print('Could not find weight section.')
