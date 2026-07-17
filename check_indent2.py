with open("D:/projects/Calories/app.py", "r", encoding="utf-8-sig") as f:
    lines = f.readlines()

with open("D:/projects/Calories/check.txt", "w", encoding="utf-8") as out:
    for i in range(1035, 1055):
        out.write(f"{i+1}: {repr(lines[i])}\n")
print("Done")
