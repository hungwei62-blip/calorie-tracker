import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    lines = f.readlines()

# Find key lines
greeting_end = None
summary_header = None
weight_start = None
weight_subheader = None

for i, l in enumerate(lines):
    if 'st.markdown(welcome_html, unsafe_allow_html=True)' in l:
        greeting_end = i
    if 'st.header(\"\U0001f4ca \u4eca\u65e5\u6458\u8981\")' in l:
        summary_header = i
    if '# ============================================================' in l:
        if i + 1 < len(lines) and 'st.subheader' in lines[i+1] and '\u9ad4\u91cd' in lines[i+1]:
            weight_start = i
    if 'st.subheader' in l and '\u2696\ufe0f' in l and '\u9ad4\u91cd' in l:
        weight_subheader = i

# Find weight end (before def page_weight)
weight_end = None
for i in range(weight_start + 1, len(lines)):
    if 'def page_weight' in lines[i]:
        weight_end = i - 1
        break

print(f'Deleting summary header at line {summary_header + 1}')
print(f'Deleting weight subheader at line {weight_subheader + 1}')
print(f'Moving weight section from lines {weight_start + 1}-{weight_end + 1} to after line {greeting_end + 1}')

# Step 1: Extract weight section (from weight_start to weight_end inclusive)
weight_section = lines[weight_start:weight_end + 1]

# Step 2: Build new content
# - Keep lines before greeting_end + 1 (st.markdown call)
# - Add weight section
# - Skip lines from greeting_end + 2 (after greeting) to weight_end
# - Keep lines from weight_end + 1 onwards

# First, let's find where greeting section ends (after uid = st.session_state.user_id)
uid_line = None
for i in range(greeting_end + 1, len(lines)):
    if 'uid = st.session_state.user_id' in lines[i]:
        uid_line = i
        break

print(f'UID line at: {uid_line + 1}')

# New logic:
# Keep lines 0 to greeting_end (greeting st.markdown)
# Add uid line
# Skip lines from greeting_end + 1 to weight_end (old location)
# Add weight section (without the subheader)
# Keep lines from weight_end + 1 onwards

new_lines = []
# Keep everything before greeting_end + 1
new_lines.extend(lines[:greeting_end + 1])

# Add uid line if it exists (it's at greeting_end + 2)
if uid_line:
    new_lines.append(lines[uid_line])  # uid line

# Skip summary header line (greeting_end + 3)
# Skip everything until weight_start
skip_until = uid_line + 1 if uid_line else greeting_end + 1

# Add weight section without the subheader (skip the first line which has the subheader)
# Actually keep the whole section, but skip the subheader line
for line in weight_section:
    if 'st.subheader' in line and '\u2696\ufe0f' in line:
        continue  # Skip the weight subheader
    new_lines.append(line)

# Skip lines from skip_until to weight_end (inclusive)
# Add everything from weight_end + 1 onwards
new_lines.extend(lines[weight_end + 1:])

with codecs.open('app.py', 'w', 'utf-8') as f:
    f.writelines(new_lines)

print('Done')
