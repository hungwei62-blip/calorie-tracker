with open('D:/projects/Calories/app.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Fix 1: Update CSS - add display: block and fix flex issue
old_css = '''        # 深色卡片趨勢圖 CSS
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
        """, unsafe_allow_html=True)'''

new_css = '''        # 深色卡片趨勢圖 CSS
        st.markdown("""
        <style>
            .chart-card {
                background: #1e1e38 !important;
                border-radius: 20px !important;
                padding: 24px !important;
                margin: 15px 0 !important;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
                display: block !important;
                width: 100% !important;
                box-sizing: border-box !important;
            }
            .chart-card h3 {
                color: #ffffff !important;
                margin-bottom: 8px !important;
            }
            .chart-value {
                font-size: 28px !important;
                font-weight: 700 !important;
                color: #ffffff !important;
                font-family: sans-serif !important;
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
                margin-bottom: 20px !important;
            }
        </style>
        """, unsafe_allow_html=True)'''

if old_css in content:
    content = content.replace(old_css, new_css)
    print('1. Fixed CSS')
else:
    print('WARNING: Old CSS not found')

# Fix 2: Replace alt.Gradient with simple RGBA
old_gradient_cal = 'alt.Gradient(gradient="linear", stops=[alt.GradientStop(color="rgba(255,165,0,0.25)", offset=0), alt.GradientStop(color="rgba(255,165,0,0)", offset=1)], x1=1, y1=0, x2=1, y2=1)'
new_gradient_cal = '"rgba(255, 165, 0, 0.15)"'

old_gradient_pro = 'alt.Gradient(gradient="linear", stops=[alt.GradientStop(color="rgba(56,182,255,0.25)", offset=0), alt.GradientStop(color="rgba(56,182,255,0)", offset=1)], x1=1, y1=0, x2=1, y2=1)'
new_gradient_pro = '"rgba(56, 182, 255, 0.15)"'

if old_gradient_cal in content:
    content = content.replace(old_gradient_cal, new_gradient_cal)
    print('2. Fixed calorie gradient')
else:
    print('WARNING: Calorie gradient not found')

if old_gradient_pro in content:
    content = content.replace(old_gradient_pro, new_gradient_pro)
    print('3. Fixed protein gradient')
else:
    print('WARNING: Protein gradient not found')

# Also need to remove the color= parameter from mark_area calls
old_area_cal = 'area_cal = base_cal.mark_area(color=alt.Gradient(gradient="linear", stops=[alt.GradientStop(color="rgba(255,165,0,0.25)", offset=0), alt.GradientStop(color="rgba(255,165,0,0)", offset=1)], x1=1, y1=0, x2=1, y2=1), interpolate="monotone")'
# This was already replaced, so let's check for the current pattern

# The mark_area should now have color="rgba(...)" directly
if 'color=alt.Gradient' in content:
    print('WARNING: alt.Gradient still in content')

open('D:/projects/Calories/app.py', 'w', encoding='utf-8-sig', newline='').write(content)
print('Saved')
