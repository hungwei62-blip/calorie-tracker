# test_page_student_history.py - 獨立測試學員歷史頁面
# 不需要登入，直接模擬數據進行測試

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="學員歷史頁面測試", layout="wide")

# 模擬已登入為教練
st.session_state.page = "教練端"
st.session_state.auth_mode = "login"

# 假設已選定的學員 ID
st.session_state.view_student_id = "mock_student_001"

# 模擬學員名稱
student_name = "測試學員"

# 模擬時間範圍
today = datetime.now()
start_date = today - timedelta(days=7)
end_date = today

# 模擬每日數據（8天）
daily = {}
for i in range(8):
    d = today - timedelta(days=7-i)
    daily[d] = {
        "calorie": 1800 + (i * 50) + (i % 3) * 100,
        "protein": 110 + (i * 8) + (i % 2) * 15,
        "water": 2000 + (i * 150)
    }

st.header(f"📊 {student_name} 的歷史記錄")
st.caption(f"顯示區間：{start_date.strftime('%Y/%m/%d')} ~ {end_date.strftime('%Y/%m/%d')}（共 8 天）")

# ====== 測試方案選擇 ======
test_option = st.radio("選擇測試方案", [
    "方案1: 透明背景（原始問題）",
    "方案2: 深色背景 #1e1e38", 
    "方案3: 深色背景 + 調整間距",
    "方案4: 最小化邊距"
], horizontal=True)

# ====== 圖表區 ======
st.divider()
st.subheader("📈 每日攝取趨勢")

sorted_days = sorted(daily.keys())
xs = [d.strftime("%m/%d") for d in sorted_days]
cals = [daily[d]['"'"'calorie'"'"'] for d in sorted_days]
pros = [daily[d]['"'"'protein'"'"'] for d in sorted_days]

avg_cal = sum(cals) / len(cals)
avg_pro = sum(pros) / len(pros)

if "方案1" in test_option:
    # ====== 方案1: 透明背景（原始問題） ======
    st.markdown("""<style>
        .chart-card { 
            background: #1e1e38 !important; 
            border-radius: 20px !important; 
            padding: 20px 20px 5px 20px !important; 
            margin: 15px 0 !important; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
        }
        .chart-value { font-size: 28px !important; font-weight: 700 !important; color: #ffffff !important; }
        .chart-unit { font-size: 14px !important; color: #a0a0a0 !important; }
    </style>""", unsafe_allow_html=True)
    
    st.markdown(f"""<div class="chart-card" style="margin-bottom: -10px;">
        <div class="chart-value">{avg_cal:.0f} <span class="chart-unit">kcal</span></div>
        <div style="color:#a0a0a0;font-size:12px;">平均每日熱量</div>
    </div>""", unsafe_allow_html=True)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=cals, mode="lines+markers", 
        line=dict(color="#FFA500", width=3, shape="spline"),
        marker=dict(size=8, color="#FFA500"),
        fill="tozeroy", fillcolor="rgba(255, 165, 0, 0.15)"))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=5, r=5, t=5, b=5), height=180,
        xaxis=dict(showgrid=False, tickfont=dict(color="#888888"), linecolor="#2a2a4a"),
        yaxis=dict(showgrid=True, gridcolor="#2a2a4a", tickfont=dict(color="#888888"), zeroline=False),
        showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    st.markdown(f"""<div class="chart-card" style="margin-top: 15px; margin-bottom: -10px;">
        <div class="chart-value">{avg_pro:.0f} <span class="chart-unit">g</span></div>
        <div style="color:#a0a0a0;font-size:12px;">平均每日蛋白質</div>
    </div>""", unsafe_allow_html=True)
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=xs, y=pros, mode="lines+markers",
        line=dict(color="#38b6ff", width=3, shape="spline"),
        marker=dict(size=8, color="#38b6ff"),
        fill="tozeroy", fillcolor="rgba(56, 182, 255, 0.15)"))
    fig2.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=5, r=5, t=5, b=5), height=180,
        xaxis=dict(showgrid=False, tickfont=dict(color="#888888"), linecolor="#2a2a4a"),
        yaxis=dict(showgrid=True, gridcolor="#2a2a4a", tickfont=dict(color="#888888"), zeroline=False),
        showlegend=False)
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

elif "方案2" in test_option:
    # ====== 方案2: 深色背景 ======
    st.markdown("""<style>
        .chart-card { 
            background: #1e1e38 !important; 
            border-radius: 20px !important; 
            padding: 20px 20px 10px 20px !important; 
            margin: 15px 0 !important; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
        }
        .chart-value { font-size: 28px !important; font-weight: 700 !important; color: #ffffff !important; }
        .chart-unit { font-size: 14px !important; color: #a0a0a0 !important; }
    </style>""", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""<div class="chart-card">
            <div class="chart-value">{avg_cal:.0f} <span class="chart-unit">kcal</span></div>
            <div style="color:#a0a0a0;font-size:12px;">平均每日熱量</div>
        </div>""", unsafe_allow_html=True)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=xs, y=cals, mode="lines+markers",
            line=dict(color="#FFA500", width=3, shape="spline"),
            marker=dict(size=8, color="#FFA500"),
            fill="tozeroy", fillcolor="rgba(255, 165, 0, 0.15)"))
        fig.update_layout(
            paper_bgcolor="#1e1e38", plot_bgcolor="#1e1e38",
            margin=dict(l=20, r=20, t=10, b=25), height=180,
            xaxis=dict(showgrid=False, tickfont=dict(color="#888888", size=11), linecolor="#2a2a4a"),
            yaxis=dict(showgrid=True, gridcolor="#2a2a4a", tickfont=dict(color="#888888", size=11), zeroline=False),
            showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    with col2:
        st.markdown(f"""<div class="chart-card">
            <div class="chart-value">{avg_pro:.0f} <span class="chart-unit">g</span></div>
            <div style="color:#a0a0a0;font-size:12px;">平均每日蛋白質</div>
        </div>""", unsafe_allow_html=True)
        
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=xs, y=pros, mode="lines+markers",
            line=dict(color="#38b6ff", width=3, shape="spline"),
            marker=dict(size=8, color="#38b6ff"),
            fill="tozeroy", fillcolor="rgba(56, 182, 255, 0.15)"))
        fig2.update_layout(
            paper_bgcolor="#1e1e38", plot_bgcolor="#1e1e38",
            margin=dict(l=20, r=20, t=10, b=25), height=180,
            xaxis=dict(showgrid=False, tickfont=dict(color="#888888", size=11), linecolor="#2a2a4a"),
            yaxis=dict(showgrid=True, gridcolor="#2a2a4a", tickfont=dict(color="#888888", size=11), zeroline=False),
            showlegend=False)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

elif "方案3" in test_option:
    # ====== 方案3: 深色背景 + 調整間距 ======
    st.markdown("""<style>
        .chart-card { 
            background: #1e1e38 !important; 
            border-radius: 16px !important; 
            padding: 16px 16px 12px 16px !important; 
            margin: 12px 0 !important; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
        }
        .chart-value { font-size: 24px !important; font-weight: 700 !important; color: #ffffff !important; }
        .chart-unit { font-size: 13px !important; color: #a0a0a0 !important; }
    </style>""", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""<div class="chart-card">
            <div class="chart-value">{avg_cal:.0f} <span class="chart-unit">kcal</span></div>
            <div style="color:#a0a0a0;font-size:11px;">平均每日熱量</div>
        </div>""", unsafe_allow_html=True)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=xs, y=cals, mode="lines+markers",
            line=dict(color="#FFA500", width=3, shape="spline"),
            marker=dict(size=8, color="#FFA500"),
            fill="tozeroy", fillcolor="rgba(255, 165, 0, 0.2)"))
        fig.update_layout(
            paper_bgcolor="#1e1e38", plot_bgcolor="#1e1e38",
            margin=dict(l=15, r=15, t=5, b=20), height=160,
            xaxis=dict(showgrid=False, tickfont=dict(color="#888888", size=10), linecolor="#2a2a4a"),
            yaxis=dict(showgrid=True, gridcolor="#2a2a4a", tickfont=dict(color="#888888", size=10), zeroline=False),
            showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    with col2:
        st.markdown(f"""<div class="chart-card">
            <div class="chart-value">{avg_pro:.0f} <span class="chart-unit">g</span></div>
            <div style="color:#a0a0a0;font-size:11px;">平均每日蛋白質</div>
        </div>""", unsafe_allow_html=True)
        
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=xs, y=pros, mode="lines+markers",
            line=dict(color="#38b6ff", width=3, shape="spline"),
            marker=dict(size=8, color="#38b6ff"),
            fill="tozeroy", fillcolor="rgba(56, 182, 255, 0.2)"))
        fig2.update_layout(
            paper_bgcolor="#1e1e38", plot_bgcolor="#1e1e38",
            margin=dict(l=15, r=15, t=5, b=20), height=160,
            xaxis=dict(showgrid=False, tickfont=dict(color="#888888", size=10), linecolor="#2a2a4a"),
            yaxis=dict(showgrid=True, gridcolor="#2a2a4a", tickfont=dict(color="#888888", size=10), zeroline=False),
            showlegend=False)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

else:
    # ====== 方案4: 最小化邊距 ======
    st.markdown("""<style>
        .chart-card { 
            background: #1e1e38 !important; 
            border-radius: 16px !important; 
            padding: 12px 12px 8px 12px !important; 
            margin: 10px 0 !important; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
        }
        .chart-value { font-size: 22px !important; font-weight: 700 !important; color: #ffffff !important; }
        .chart-unit { font-size: 12px !important; color: #a0a0a0 !important; }
    </style>""", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""<div class="chart-card">
            <div class="chart-value">{avg_cal:.0f} <span class="chart-unit">kcal</span></div>
        </div>""", unsafe_allow_html=True)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=xs, y=cals, mode="lines+markers",
            line=dict(color="#FFA500", width=3, shape="spline"),
            marker=dict(size=8, color="#FFA500"),
            fill="tozeroy", fillcolor="rgba(255, 165, 0, 0.25)"))
        fig.update_layout(
            paper_bgcolor="#1e1e38", plot_bgcolor="#1e1e38",
            margin=dict(l=0, r=0, t=0, b=0), height=150,
            xaxis=dict(showgrid=False, tickfont=dict(color="#888888", size=10), linecolor="#2a2a4a"),
            yaxis=dict(showgrid=True, gridcolor="#2a2a4a", tickfont=dict(color="#888888", size=10), zeroline=False),
            showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    with col2:
        st.markdown(f"""<div class="chart-card">
            <div class="chart-value">{avg_pro:.0f} <span class="chart-unit">g</span></div>
        </div>""", unsafe_allow_html=True)
        
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=xs, y=pros, mode="lines+markers",
            line=dict(color="#38b6ff", width=3, shape="spline"),
            marker=dict(size=8, color="#38b6ff"),
            fill="tozeroy", fillcolor="rgba(56, 182, 255, 0.25)"))
        fig2.update_layout(
            paper_bgcolor="#1e1e38", plot_bgcolor="#1e1e38",
            margin=dict(l=0, r=0, t=0, b=0), height=150,
            xaxis=dict(showgrid=False, tickfont=dict(color="#888888", size=10), linecolor="#2a2a4a"),
            yaxis=dict(showgrid=True, gridcolor="#2a2a4a", tickfont=dict(color="#888888", size=10), zeroline=False),
            showlegend=False)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

# 水量長條圖
st.divider()
st.subheader("💧 水量趨勢")
st.bar_chart({"日期": xs, "水量": [daily[d]['"'"'water'"'"'] for d in sorted_days]}, x="日期", y="水量")
