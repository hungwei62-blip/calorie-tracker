with open("D:/projects/Calories/app.py", "r", encoding="utf-8-sig") as f:
    lines = f.readlines()

with open("D:/projects/Calories/structure.txt", "w", encoding="utf-8") as out:
    # Find the chart section
    for i, line in enumerate(lines):
        if "每日攝取趨勢" in line and "subheader" in line:
            out.write(f"=== Found chart section at line {i+1} ===\n")
            # Show 30 lines after
            for j in range(i, min(i+40, len(lines))):
                indent = len(lines[j]) - len(lines[j].lstrip())
                out.write(f"{j+1} (indent={indent}): {lines[j].rstrip()[:80]}\n")
            break
print("Done")
