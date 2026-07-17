# test_plotly_fix.py - 本地測試用腳本
# 測試 Plotly 圖表格式修正方案

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Plotly 圖表測試", layout="wide")

# 測試數據
today = datetime.now()
dates = [(today - timedelta(days=i)).strftime("%m/%d") for i in range(7, -1, -1)]
cals = [1850, 2100, 1950, 2200, 1800, 2050, 1900, 2000]
pros = [120, 135, 110, 145, 115, 130, 105, 125]
waters = [2000, 2500, 2200, 2800, 2100, 2400, 1900, 2300]

st.header("📊 Plotly 圖表格式測試")

# 方案選擇
option = st.radio("選擇測試方案", [
    "A: 原始設定（透明背景）",
    "B: 深色背景（#1e1e38）",
    "C: 自定義 HTML + 深色背景",
    "D: 隱藏軸線 + 深色背景"
], horizontal=True)

# 深色卡片 CSS（通用）
st.markdown("""<style>
    .test-card { 
        background: #1e1e38 !important; 
        border-radius: 16px !important; 
        padding: 16px 16px 8px 16px !important; 
        margin: 12px 0 !important; 
        box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
    }
    .test-value { font-size: 24px !important; font-weight: 700 !important; color: #ffffff !important; }
    .test-unit { font-size: 14px !important; color: #a0a0a0 !important; }
    .test-label { color:#a0a0a0 !important; font-size:12px !important; }
</style>""", unsafe_allow_html=True)

avg_cal = sum(cals) / len(cals)
avg_pro = sum(pros) / len(pros)

if "A" in option:
    st.subheader("A: 原始設定（透明背景）")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""<div class="test-card"><div class="test-value">{avg_cal:.0f} <span class="test-unit">kcal</span></div><div class="test-label">平均每日熱量</div></div>""", unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=cals, mode="lines+markers", line=dict(color="#FFA500", width=3, shape="spline"), fill="tozeroy", fillcolor="rgba(255, 165, 0, 0.15)"))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=5, r=5, t=5, b=5), height=160, xaxis=dict(showgrid=False, tickfont=dict(color="#888888")), yaxis=dict(showgrid=True, gridcolor="#2a2a4a", tickfont=dict(color="#888888"), zeroline=False), showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with col2:
        st.markdown(f"""<div class="test-card"><div class="test-value">{avg_pro:.0f} <span class="test-unit">g</span></div><div class="test-label">平均每日蛋白質</div></div>""", unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=pros, mode="lines+markers", line=dict(color="#38b6ff", width=3, shape="spline"), fill="tozeroy", fillcolor="rgba(56, 182, 255, 0.15)"))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=5, r=5, t=5, b=5), height=160, xaxis=dict(showgrid=False, tickfont=dict(color="#888888")), yaxis=dict(showgrid=True, gridcolor="#2a2a4a", tickfont=dict(color="#888888"), zeroline=False), showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

elif "B" in option:
    st.subheader("B: 深色背景（#1e1e38）")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""<div class="test-card"><div class="test-value">{avg_cal:.0f} <span class="test-unit">kcal</span></div><div class="test-label">平均每日熱量</div></div>""", unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=cals, mode="lines+markers", line=dict(color="#FFA500", width=3, shape="spline"), fill="tozeroy", fillcolor="rgba(255, 165, 0, 0.15)"))
        fig.update_layout(paper_bgcolor="#1e1e38", plot_bgcolor="#1e1e38", margin=dict(l=5, r=5, t=5, b=5), height=160, xaxis=dict(showgrid=False, tickfont=dict(color="#888888"), linecolor="#2a2a4a"), yaxis=dict(showgrid=True, gridcolor="#2a2a4a", tickfont=dict(color="#888888"), zeroline=False), showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with col2:
        st.markdown(f"""<div class="test-card"><div class="test-value">{avg_pro:.0f} <span class="test-unit">g</span></div><div class="test-label">平均每日蛋白質</div></div>""", unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=pros, mode="lines+markers", line=dict(color="#38b6ff", width=3, shape="spline"), fill="tozeroy", fillcolor="rgba(56, 182, 255, 0.15)"))
        fig.update_layout(paper_bgcolor="#1e1e38", plot_bgcolor="#1e1e38", margin=dict(l=5, r=5, t=5, b=5), height=160, xaxis=dict(showgrid=False, tickfont=dict(color="#888888"), linecolor="#2a2a4a"), yaxis=dict(showgrid=True, gridcolor="#2a2a4a", tickfont=dict(color="#888888"), zeroline=False), showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

elif "C" in option:
    st.subheader("C: 自定義容器包裝")
    st.markdown("""<style>
        .chart-wrapper { 
            background: #1e1e38 !important; 
            border-radius: 16px !important; 
            padding: 12px !important; 
            margin: 12px 0 !important;
        }
        .chart-wrapper .stPlotlyChart { 
            margin-top: -8px !important;
        }
    </style>""", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""<div class="chart-wrapper"><div class="test-value">{avg_cal:.0f} <span class="test-unit">kcal</span></div><div class="test-label">平均每日熱量</div></div>""", unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=cals, mode="lines+markers", line=dict(color="#FFA500", width=3, shape="spline"), fill="tozeroy", fillcolor="rgba(255, 165, 0, 0.15)"))
        fig.update_layout(paper_bgcolor="#1e1e38", plot_bgcolor="#1e1e38", margin=dict(l=0, r=0, t=0, b=0), height=140, xaxis=dict(showgrid=False, tickfont=dict(color="#888888"), linecolor="#2a2a4a", showticklabels=False), yaxis=dict(showgrid=True, gridcolor="#2a2a4a", tickfont=dict(color="#888888"), zeroline=False, showticklabels=False), showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with col2:
        st.markdown(f"""<div class="chart-wrapper"><div class="test-value">{avg_pro:.0f} <span class="test-unit">g</span></div><div class="test-label">平均每日蛋白質</div></div>""", unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=pros, mode="lines+markers", line=dict(color="#38b6ff", width=3, shape="spline"), fill="tozeroy", fillcolor="rgba(56, 182, 255, 0.15)"))
        fig.update_layout(paper_bgcolor="#1e1e38", plot_bgcolor="#1e1e38", margin=dict(l=0, r=0, t=0, b=0), height=140, xaxis=dict(showgrid=False, tickfont=dict(color="#888888"), linecolor="#2a2a4a", showticklabels=False), yaxis=dict(showgrid=True, gridcolor="#2a2a4a", tickfont=dict(color="#888888"), zeroline=False, showticklabels=False), showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

else:
    st.subheader("D: 隱藏軸線 + 深色背景")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""<div class="test-card"><div class="test-value">{avg_cal:.0f} <span class="test-unit">kcal</span></div><div class="test-label">平均每日熱量</div></div>""", unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=cals, mode="lines+markers", line=dict(color="#FFA500", width=3, shape="spline"), marker=dict(size=8, color="#FFA500"), fill="tozeroy", fillcolor="rgba(255, 165, 0, 0.15)"))
        fig.update_layout(paper_bgcolor="#1e1e38", plot_bgcolor="#1e1e38", margin=dict(l=20, r=20, t=10, b=20), height=160, xaxis=dict(showgrid=False, tickfont=dict(color="#888888", size=10), linecolor="#2a2a4a", showline=True, zeroline=False), yaxis=dict(showgrid=True, gridcolor="#2a2a4a", tickfont=dict(color="#888888", size=10), zeroline=False, showline=False), showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with col2:
        st.markdown(f"""<div class="test-card"><div class="test-value">{avg_pro:.0f} <span class="test-unit">g</span></div><div class="test-label">平均每日蛋白質</div></div>""", unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=pros, mode="lines+markers", line=dict(color="#38b6ff", width=3, shape="spline"), marker=dict(size=8, color="#38b6ff"), fill="tozeroy", fillcolor="rgba(56, 182, 255, 0.15)"))
        fig.update_layout(paper_bgcolor="#1e1e38", plot_bgcolor="#1e1e38", margin=dict(l=20, r=20, t=10, b=20), height=160, xaxis=dict(showgrid=False, tickfont=dict(color="#888888", size=10), linecolor="#2a2a4a", showline=True, zeroline=False), yaxis=dict(showgrid=True, gridcolor="#2a2a4a", tickfont=dict(color="#888888", size=10), zeroline=False, showline=False), showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# 水量測試
st.divider()
st.subheader("水量長條圖測試")
bar_data = pd.DataFrame({"日期": dates, "水量": waters})
st.bar_chart(bar_data, x="日期", y="水量")
