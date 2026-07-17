import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    content = f.read()

# Delete the weight subheader (with emoji)
content = content.replace('    st.subheader("\u2696\ufe0f \u9ad4\u91cd")\n', '')

with codecs.open('app.py', 'w', 'utf-8') as f:
    f.write(content)

print('Done')
