import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    lines = f.readlines()

# Step 1: Delete the "⚖️ 體重" subheader
for i, l in enumerate(lines):
    if 'st.subheader("\u2696\ufe0f \u9ad4\u91cd")' in l:
        print(f'Deleting weight subheader at line {i+1}')
        lines[i] = ''
        break

# Step 2: Delete the "📊 今日摘要" header
for i, l in enumerate(lines):
    if 'st.header("\U0001f4ca \u4eca\u65e5\u6458\u8981")' in l:
        print(f'Deleting summary header at line {i+1}')
        lines[i] = ''
        break

with codecs.open('app.py', 'w', 'utf-8') as f:
    f.writelines(lines)

print('Done - headers deleted')
