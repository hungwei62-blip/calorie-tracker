import os

# Read the current file
with open('D:/projects/Calories/app.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 1. Add plotly import
if 'import plotly.graph_objects as go' not in content:
    content = content.replace(
        'import matplotlib.pyplot as _plt',
        'import matplotlib.pyplot as _plt\nimport plotly.graph_objects as go'
    )
    print('1. Added plotly import')

# 2. Remove altair import
if 'import altair as alt' in content:
    content = content.replace('import altair as alt\n', '')
    print('2. Removed altair import')

# 3. Find the chart section to replace
# Find "每日攝取趨勢" and then "if daily:"
chart_section_start = content.find('每日攝取趨勢')
if_daily_pos = content.find('if daily:', chart_section_start)
water_pos = content.find('st.subheader("💧 水量趨勢")', if_daily_pos)

print(f'3. Chart section: if_daily={if_daily_pos}, water={water_pos}')

# 4. Create the new Plotly code as a raw string
new_chart_code = """
    if daily:
        sorted_days = sorted(daily.keys())
        xs = [d.strftime("%m/%d") for d in sorted_days]

        # ----- 1. 準備數據 -----
        cals = [daily[d]["calorie"] for d in sorted_days]
        pros = [daily[d]["protein"] for d in sorted_days]

        total_cal = sum(cals)
        avg_cal = total_cal / len(sorted_days) if sorted_days else 0

        total_pro = sum(pros)
        avg_pro = total_pro / len(sorted_days) if sorted_days else 0

        # ----- 2. 熱量趨勢圖 (Plotly 版) -----
        st.markdown(f'"'"'''
            <div class="chart-card" style="margin-bottom: -10px;">
                <div class="chart-header">
                    <div>
                        <div class="chart-value">'"'"'{avg_cal:.0f}'"'"' <span class="chart-unit">kcal</span></div>
                        <div style="color:#a0a0a0;font-size:12px;font-family:sans-serif;">平均每日熱量</div>
                    </div>
                </div>
            </div>
        '''"'"', unsafe_allow_html=True)

        fig_cal = go.Figure()
        fig_cal.add_trace(go.Scatter(
            x=xs,
            y=cals,
            mode='"'"'lines+markers'"'"',
            line=dict(color='"'"'#FFA500'"'"', width=3, shape='"'"'spline'"'"'),
            marker=dict(size=8, color='"'"'#FFA500'"'"'),
            fill='"'"'tozeroy'"'"',
            fillcolor='"'"'rgba(255, 165, 0, 0.15)'"'"',
            hovertemplate='"'"'日期: %{x}<br>熱量: %{y:.0f} kcal<extra></extra>'"'"'
        ))
        
        fig_cal.update_layout(
            paper_bgcolor='"'"'rgba(0,0,0,0)'"'"',
            plot_bgcolor='"'"'rgba(0,0,0,0)'"'"',
            margin=dict(l=5, r=5, t=5, b=5),
            height=180,
            xaxis=dict(showgrid=False, tickfont=dict(color='"'"'#888888'"'"'), linecolor='"'"'#2a2a4a'"'"'),
            yaxis=dict(showgrid=True, gridcolor='"'"'#2a2a4a'"'"', tickfont=dict(color='"'"'#888888'"'"'), zeroline=False),
            showlegend=False
        )
        
        st.plotly_chart(fig_cal, use_container_width=True, config={"'"'"'displayModeBar'"'"': False})


        # ----- 3. 蛋白質趨勢圖 (Plotly 版) -----
        st.markdown(f'"'"'''
            <div class="chart-card" style="margin-top: 15px; margin-bottom: -10px;">
                <div class="chart-header">
                    <div>
                        <div class="chart-value">'"'"'{avg_pro:.0f}'"'"' <span class="chart-unit">g</span></div>
                        <div style="color:#a0a0a0;font-size:12px;font-family:sans-serif;">平均每日蛋白質</div>
                    </div>
                </div>
            </div>
        '''"'"', unsafe_allow_html=True)

        fig_pro = go.Figure()
        fig_pro.add_trace(go.Scatter(
            x=xs,
            y=pros,
            mode='"'"'lines+markers'"'"',
            line=dict(color='"'"'#38b6ff'"'"', width=3, shape='"'"'spline'"'"'),
            marker=dict(size=8, color='"'"'#38b6ff'"'"'),
            fill='"'"'tozeroy'"'"',
            fillcolor='"'"'rgba(56, 182, 255, 0.15)'"'"',
            hovertemplate='"'"'日期: %{x}<br>蛋白質: %{y:.0f} g<extra></extra>'"'"'
        ))
        
        fig_pro.update_layout(
            paper_bgcolor='"'"'rgba(0,0,0,0)'"'"',
            plot_bgcolor='"'"'rgba(0,0,0,0)'"'"',
            margin=dict(l=5, r=5, t=5, b=5),
            height=180,
            xaxis=dict(showgrid=False, tickfont=dict(color='"'"'#888888'"'"'), linecolor='"'"'#2a2a4a'"'"'),
            yaxis=dict(showgrid=True, gridcolor='"'"'#2a2a4a'"'"', tickfont=dict(color='"'"'#888888'"'"'), zeroline=False),
            showlegend=False
        )
        
        st.plotly_chart(fig_pro, use_container_width=True, config={"'"'"'displayModeBar'"'"': False})
"""

# Replace the section
if if_daily_pos != -1 and water_pos != -1:
    content = content[:if_daily_pos] + new_chart_code + content[water_pos:]
    print('4. Replaced chart code')
else:
    print('ERROR: Could not find section to replace')
    exit(1)

# 5. Update CSS
old_css = '.chart-card { background: #1e1e38 !important; border-radius: 20px !important; padding: 24px !important; margin: 15px 0 !important; box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important; display: block !important; width: 100% !important; box-sizing: border-box !important; }'
new_css = '.chart-card { background: #1e1e38 !important; border-radius: 20px !important; padding: 20px 20px 5px 20px !important; margin: 15px 0 !important; box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important; box-sizing: border-box !important; }'

if old_css in content:
    content = content.replace(old_css, new_css)
    print('5. Updated chart-card CSS')
else:
    print('WARNING: chart-card CSS not found')

# Save
with open('D:/projects/Calories/app.py', 'w', encoding='utf-8-sig', newline='') as f:
    f.write(content)

print('Saved')
