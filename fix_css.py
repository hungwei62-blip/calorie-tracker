# 讀取檔案
with open(r'D:\projects\Calories\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 更新 CSS - member-card
old_card = '.member-card { padding: 16px 0; margin-bottom: 16px; display: flex; align-items: center; }'
new_card = '''.member-card { display: flex; flex-direction: column; gap: 16px; padding: 16px; background: #fff; border-radius: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 16px; }
    .member-top-row { display: flex; align-items: center; gap: 12px; }
    .member-avatar { width: 48px; height: 48px; border-radius: 50%; background: #BBE8EE; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }
    .member-name { font-size: 18px; font-weight: 500; color: #1F2937; }'''

content = content.replace(old_card, new_card)

# 移除不需要的 CSS
content = content.replace('.member-info { flex: 1; }\n', '')
content = content.replace('.member-name-row { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }\n', '')

# 寫回檔案
with open(r'D:\projects\Calories\app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("CSS updated")
