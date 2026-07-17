import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    content = f.read()

# Delete the weight subheader (with emoji)
content = content.replace('    st.subheader("\u2696\ufe0f \u9ad4\u91cd")\n', '')

# Delete the summary header (with emoji)
content = content.replace('    st.header("\U0001f4ca \u4eca\u65e5\u6458\u8981")\n', '')

with codecs.open('app.py', 'w', 'utf-8') as f:
    f.write(content)

print('Done - headers deleted')
