import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    lines = f.readlines()

# Find weight-related divider (should be after calorie charts, before weight card)
for i in range(1800, 2072):
    if 'st.divider()' in lines[i]:
        print(f'Divider at line {i+1}')
        # Check next few lines
        for j in range(i, min(i+5, 2072)):
            print(f'  Line {j+1}: {repr(lines[j][:60])}')
        break
