with open("D:/projects/Calories/app.py", "r", encoding="utf-8-sig") as f:
    lines = f.readlines()

with open("D:/projects/Calories/more_structure.txt", "w", encoding="utf-8") as out:
    for i in range(1038, 1065):
        indent = len(lines[i]) - len(lines[i].lstrip())
        out.write(f"{i+1} (indent={indent}): {lines[i].rstrip()[:80]}\n")
print("Done")
