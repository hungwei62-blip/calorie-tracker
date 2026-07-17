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
print(f'Weight section: lines 1912 to {page_weight_start-1}')

# Extract weight section (lines 1911 to page_weight_start - 1, inclusive)
# But we need to skip the divider and subheader, so start from 1913
weight_section = lines[1913:page_weight_start]  # 1913 is after divider, comment, and subheader
print(f'Weight section has {len(weight_section)} lines')

# Build new content
# Lines 0 to 1555 (up to uid line, inclusive)
# Add weight section
# Lines 1556 to 2071 (everything else in page_personal except weight)
# Lines 2071 onwards (page_weight and rest)

new_lines = []
new_lines.extend(lines[:1556])  # up to and including uid line (line 1556)
new_lines.append('\n')  # add newline
new_lines.extend(weight_section)  # weight section
new_lines.extend(lines[1911:page_weight_start])  # divider, comment, subheader (old weight location)
new_lines.extend(lines[page_weight_start:])  # page_weight and rest

with codecs.open('app.py', 'w', 'utf-8') as f:
    f.writelines(new_lines)

print(f'Done! New file has {len(new_lines)} lines')
