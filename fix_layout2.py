import codecs
import re

with codecs.open('app.py', 'r', 'utf-8') as f:
    content = f.read()

# Step 1: Delete the "⚖️ 體重" subheader line
content = re.sub(r'\n    st\.subheader\("\u2696\ufe0f \u9ad4\u91cd"\)\n', '\n', content)

# Step 2: Delete the "📊 今日摘要" header line
content = re.sub(r'\n    st\.header\("\U0001f4ca \u4eca\u65e5\u6458\u8981"\)\n', '\n', content)

# Step 3: Find and extract the entire weight section (from the comment to closing div)
# Pattern to match the weight section
weight_pattern = r'(    # ============================================================\n    st\.subheader\("[^"]*"\).*?<div class="weight-card-container">.*?</div>\n\n    st\.write\("<div style=\'height: 40px;\'></div>", unsafe_allow_html=True\)\n\n\n    st\.markdown\(\'</div>\', unsafe_allow_html=True\)\n)'

weight_match = re.search(weight_pattern, content, re.DOTALL)
if weight_match:
    weight_section = weight_match.group(1)
    print(f'Found weight section, length: {len(weight_section)} chars')
    
    # Remove weight section from original location
    content = content[:weight_match.start()] + content[weight_match.end():]
    
    # Find greeting section end
    greeting_pattern = r'(st\.markdown\(welcome_html, unsafe_allow_html=True\))'
    greeting_match = re.search(greeting_pattern, content)
    
    if greeting_match:
        insert_pos = greeting_match.end()
        content = content[:insert_pos] + '\n\n' + weight_section + content[insert_pos:]
        print('Inserted weight section after greeting')
else:
    print('Weight section not found')

with codecs.open('app.py', 'w', 'utf-8') as f:
    f.write(content)

print('Done')
