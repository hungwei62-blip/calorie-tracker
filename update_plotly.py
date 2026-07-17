# Read the file
with open(r'D:\projects\Calories\app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_code = '''
        # ==========================================
        # CSS：Plotly 容器圓角與陰影
        # ==========================================
        st.markdown("""
        <style>
            div[data-testid="stPlotlyChart"] {
                border-radius: 24px !important;
                overflow: hidden !important;
                box-shadow: 0 12px 40px rgba(0,0,0,0.3) !important;
                margin: 15px 0 !important;
                background-color: #16152b !important;
            }
        </style>
        """, unsafe_allow_html=True)

        # 統一的高質感深夜底色
        CARD_BG = '#2a2850'
        # 統一強制套用系統原生高質感字型
        FONT_SETTING = dict(family="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif")

        # ==========================================
        # 1. 一體化熱量趨勢圖
        # ==========================================
        max_cal = max(cals) if cals else 0
        cal_ticks = []
        if max_cal > 0:
            cal_ticks = [v for v in [1000, 1500, 2000, 2500, 3000, 3500, 4000] if v <= max_cal * 1.2]
            if not cal_ticks or cal_ticks[-1] < max_cal:
                cal_ticks.append(((max_cal // 500) + 1) * 500)

        fig_cal = go.Figure()

        fig_cal.add_trace(go.Scatter(
            x=xs,
            y=cals,
            mode='lines+markers',
            line=dict(color='#ffffff', width=3, shape='spline'),
            marker=dict(size=6, color='#16152b', line=dict(color='#ffffff', width=2)),
            fill='tozeroy',
            fillcolor='rgba(255, 255, 255, 0.04)',
            hovertemplate='日期: %{x}<br>熱量: %{y:.0f} kcal<extra></extra>'
        ))

        fig_cal.update_layout(
            paper_bgcolor=CARD_BG,
            plot_bgcolor=CARD_BG,
            margin=dict(l=40, r=25, t=90, b=25),
            height=260,
            font=FONT_SETTING,
            annotations=[
                dict(x=0.01, y=1.40, xref="paper", yref="paper",
                    text=f"<b style='font-size:32px; color:#ffffff;'>" + str(avg_cal) + "</b> <span style='font-size:14px; color:#a0a0a0; font-weight:normal;'>kcal</span>",
                    showarrow=False, align="left"),
                dict(x=0.01, y=1.12, xref="paper", yref="paper",
                    text="<span style='font-size:12px; color:#a0a0a0; font-weight:normal;'>平均每日熱量</span>",
                    showarrow=False, align="left")
            ],
            xaxis=dict(showgrid=False, tickfont=dict(color='#888888', size=12), showline=False, ticks=""),
            yaxis=dict(showgrid=True, gridcolor='rgba(255, 255, 255, 0.05)', tickfont=dict(color='#888888', size=11), zeroline=False, showline=False, ticks="", tickvals=cal_ticks if cal_ticks else None),
            showlegend=False
        )

        st.plotly_chart(fig_cal, use_container_width=True, config={'displayModeBar': False})

        # ==========================================
        # 2. 一體化蛋白質趨勢圖
        # ==========================================
        max_pro = max(pros) if pros else 0
        pro_ticks = []
        if max_pro > 0:
            pro_ticks = [v for v in [50, 100, 150, 200, 250] if v <= max_pro * 1.2]
            if not pro_ticks or pro_ticks[-1] < max_pro:
                pro_ticks.append(((max_pro // 25) + 1) * 25)

        fig_pro = go.Figure()

        fig_pro.add_trace(go.Scatter(
            x=xs,
            y=pros,
            mode='lines+markers',
            line=dict(color='#ffffff', width=3, shape='spline'),
            marker=dict(size=6, color='#16152b', line=dict(color='#ffffff', width=2)),
            fill='tozeroy',
            fillcolor='rgba(255, 255, 255, 0.04)',
            hovertemplate='日期: %{x}<br>蛋白質: %{y:.0f} g<extra></extra>'
        ))

        fig_pro.update_layout(
            paper_bgcolor=CARD_BG,
            plot_bgcolor=CARD_BG,
            margin=dict(l=40, r=25, t=90, b=25),
            height=260,
            font=FONT_SETTING,
            annotations=[
                dict(x=0.01, y=1.40, xref="paper", yref="paper",
                    text=f"<b style='font-size:32px; color:#ffffff;'>" + str(avg_pro) + "</b> <span style='font-size:14px; color:#a0a0a0; font-weight:normal;'>g</span>",
                    showarrow=False, align="left"),
                dict(x=0.01, y=1.12, xref="paper", yref="paper",
                    text="<span style='font-size:12px; color:#a0a0a0; font-weight:normal;'>平均每日蛋白質</span>",
                    showarrow=False, align="left")
            ],
            xaxis=dict(showgrid=False, tickfont=dict(color='#888888', size=12), showline=False, ticks=""),
            yaxis=dict(showgrid=True, gridcolor='rgba(255, 255, 255, 0.05)', tickfont=dict(color='#888888', size=11), zeroline=False, showline=False, ticks="", tickvals=pro_ticks if pro_ticks else None),
            showlegend=False
        )

        st.plotly_chart(fig_pro, use_container_width=True, config={'displayModeBar': False})

'''

# Keep lines 0-1024 (before the Plotly code)
# Replace lines 1025-1135 with new code
# Keep lines 1136+ (after the Plotly code - water chart onwards)

result = lines[:1025] + [new_code] + lines[1136:]

with open(r'D:\projects\Calories\app.py', 'w', encoding='utf-8') as f:
    f.writelines(result)

print("Done")
