# 讀取檔案
with open(r'D:\projects\Calories\app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到 card_html 那行
for i, line in enumerate(lines):
    if 'member-card' in line and 'member-avatar' in line and 'surname' in line:
        # 新的 HTML 結構 - [圓形] 姓名 [訓練徽章]
        new_html = '''        card_html = "<div class=\\"member-card\\"><div class=\\"member-top-row\\"><div class=\\"training-badge " + training_class + "\\">" + training_html + "</div><div class=\\"member-avatar\\">" + surname + "</div><div class=\\"member-name\\">" + name + "</div></div><div class=\\"capsule-row\\"><div class=\\"capsule-container\\"><div class=\\"capsule-track\\"><div class=\\"capsule-fill cal\\" style=\\"height: " + str(cal_pct) + "%\\"></div><div class=\\"capsule-badge\\" style=\\"top: " + str(cal_top) + "%\\">" + str(calorie_actual) + "</div></div><div class=\\"capsule-label\\">CAL</div><div class=\\"capsule-value\\">" + str(calorie_actual) + "/" + str(int(calorie_goal)) + "</div></div><div class=\\"capsule-container\\"><div class=\\"capsule-track\\"><div class=\\"capsule-fill pro\\" style=\\"height: " + str(pro_pct) + "%\\"></div><div class=\\"capsule-badge\\" style=\\"top: " + str(pro_top) + "%\\">" + str(protein_actual) + "</div></div><div class=\\"capsule-label\\">PROT</div><div class=\\"capsule-value\\">" + str(protein_actual) + "/" + str(int(protein_goal)) + "g</div></div><div class=\\"capsule-container\\"><div class=\\"capsule-track\\"><div class=\\"capsule-fill water\\" style=\\"height: " + str(water_pct) + "%\\"></div><div class=\\"capsule-badge\\" style=\\"top: " + str(water_top) + "%\\">" + str(water_actual) + "</div></div><div class=\\"capsule-label\\">WATER</div><div class=\\"capsule-value\\">" + str(water_actual) + "/" + str(int(water_goal)) + "</div></div></div></div>"'''
        lines[i] = new_html + '\n'
        print(f"Updated line {i+1}")
        break

# 寫回檔案
with open(r'D:\projects\Calories\app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Done")
