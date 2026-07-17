with open('D:/projects/Calories/app.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Remove the first (duplicate) multi-line CSS block
# It starts with "# 深色卡片趨勢圖 CSS\n# ===" and ends before the subheader

old_css_section = '''        # ============================================================
        # 深色卡片趨勢圖 CSS
        # ============================================================
        st.markdown("""
        <style>
            .chart-card {
                background: #1e1e38 !important;
                border-radius: 20px !important;
                padding: 20px !important;
                margin: 10px 0 !important;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
            }
            .chart-card h3 {
                color: #ffffff !important;
                margin-bottom: 8px !important;
            }
            .chart-value {
                font-size: 28px !important;
                font-weight: 700 !important;
                color: #ffffff !important;
            }
            .chart-unit {
                font-size: 14px !important;
                color: #a0a0a0 !important;
            }
            .chart-emoji {
                font-size: 32px !important;
            }
            .chart-header {
                display: flex !important;
                justify-content: space-between !important;
                align-items: center !important;
                margin-bottom: 16px !important;
            }
        </style>
        """, unsafe_allow_html=True)

        st.subheader'''

if old_css_section in content:
    new_css_section = '''        st.subheader'''
    content = content.replace(old_css_section, new_css_section)
    print('1. Removed duplicate CSS block')
else:
    print('WARNING: Old CSS section not found')

# Now fix the remaining CSS to add display: block
old_compact_css = '.chart-card { background: #1e1e38 !important; border-radius: 20px !important; padding: 20px !important; margin: 10px 0 !important; box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important; }'
new_compact_css = '.chart-card { background: #1e1e38 !important; border-radius: 20px !important; padding: 24px !important; margin: 15px 0 !important; box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important; display: block !important; width: 100% !important; box-sizing: border-box !important; }'

if old_compact_css in content:
    content = content.replace(old_compact_css, new_compact_css)
    print('2. Fixed CSS with display: block')
else:
    print('WARNING: Compact CSS not found')

open('D:/projects/Calories/app.py', 'w', encoding='utf-8-sig', newline='').write(content)
print('Saved')
