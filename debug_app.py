with open("D:/projects/Calories/app.py", "r", encoding="utf-8-sig") as f:
    lines = f.readlines()

# Find the Plotly section
for i, line in enumerate(lines):
    if "import plotly.graph_objects" in line:
        print(f"Line {i+1}: {line.strip()}")
    if "if daily:" in line and i > 1000:
        print(f"Line {i+1}: {line.strip()}")
        # Show next 30 lines
        with open("D:/projects/Calories/debug.txt", "w", encoding="utf-8") as out:
            for j in range(i, min(i+40, len(lines))):
                indent = len(lines[j]) - len(lines[j].lstrip())
                out.write(f"{j+1} (indent={indent}): {lines[j].rstrip()[:100]}\n")
        break
