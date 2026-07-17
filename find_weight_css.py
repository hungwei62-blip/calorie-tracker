import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    lines = f.readlines()

# Search for weight-card-container
for i, l in enumerate(lines):
    if 'weight-card-container' in l:
        print(f'Found at line {i+1}')
        # Print context
        for j in range(max(0,i-2), min(len(lines), i+5)):
            print(f'  {j+1}: {repr(l[:40])}')
        break
