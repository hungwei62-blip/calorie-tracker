# HANDOFF.md - 飲食控制管理系統 學員歷史 Plotly 圖表問題分析

## 檔案位置
- 主檔案：D:\\projects\\Calories\\app.py

## 🔴 核心問題：縮排錯誤（Indentation Bug）

### 問題描述
整個「每日攝取趨勢」區塊（深色卡片、Plotly 熱量圖、Plotly 蛋白質圖、水量長條圖）被錯誤地嵌套在 if weights: 的 else: 分支內部。

### 影響範圍
- 當學員**有**體重記錄時 → if weights: 執行 → else: 分支被跳過 → **整個每日攝取趨勢區塊完全消失**
- 當學員**沒有**體重記錄時 → else: 執行 → 每日攝取趨勢才會顯示

### 錯誤程式碼結構（app.py 第 988-1052 行）

`python
988:     st.subheader("⚖️ 體重變化")
989:     if weights:              # 4 spaces indent
990:         wchart = { ... }
991-994:     ...
994:         st.line_chart(wchart, x="日期", y="體重 (kg)")
995:     else:                    # 4 spaces indent
996:         st.info("此區間沒有體重記錄。")
                                    # (blank lines)
997-999:
1000:         st.subheader("📈 每日攝取趨勢")   # ❌ 8 spaces indent - 錯誤！在 else 內部
1001-1009:     CSS st.markdown(...)            # ❌ 8 spaces indent
1010-1011:                                 # ❌ 8 spaces indent
1012:         if daily:                       # ❌ 8 spaces indent - 在 else 內部
1013-1046:     Plotly 圖表程式碼              # ❌ 12 spaces indent
1048-1049:     else: st.info("...")          # ❌ 12 spaces indent
1050-1051:                                 # ❌ 8 spaces indent
1052:     st.subheader("🏋️ 訓練記錄")        # ✅ 4 spaces indent - 正確位置
`

### 正確結構應該是

`python
988:     st.subheader("⚖️ 體重變化")
989:     if weights:
990:         wchart = { ... }
994:         st.line_chart(wchart, x="日期", y="體重 (kg)")
995:     else:
996:         st.info("此區間沒有體重記錄。")
                                    # (blank lines)
                                    # ✅ 4 spaces indent - 獨立於 if/else 之外
1000:     st.subheader("📈 每日攝取趨勢")       # ✅ 4 spaces indent - 移出 else
1001-1009:     CSS st.markdown(...)            # ✅ 4 spaces indent
1010-1011:                                 # ✅ 4 spaces indent
1012:     if daily:                       # ✅ 4 spaces indent - 與 if weights 同級
1013-1046:     Plotly 圖表程式碼              # ✅ 8 spaces indent
1048-1049:     else: st.info("...")
                                    # ✅ 4 spaces indent
1052:     st.subheader("🏋️ 訓練記錄")
`

## 修復方式

將 st.subheader("📈 每日攝取趨勢")（第 1000 行）到 st.info("此區間沒有飲食記錄。")（第 1049 行）的所有內容，向左減少 4 個空格的縮排。

### 具體來說：
- 第 1000 行：st.subheader("📈 每日攝取趨勢") → 從 8 spaces 改為 4 spaces
- 第 1003-1009 行（CSS）：st.markdown(...) → 從 8 spaces 改為 4 spaces  
- 第 1012 行：if daily: → 從 8 spaces 改為 4 spaces
- 第 1027-1046 行（Plotly 程式碼）：→ 從 12 spaces 改為 8 spaces
- 第 1048-1049 行：else: st.info(...) → 從 12 spaces 改為 8 spaces

## 其他觀察

### 1. Plotly 背景透明問題
- paper_bgcolor="rgba(0,0,0,0)" 和 plot_bgcolor="rgba(0,0,0,0)" 設為完全透明
- 建議改為 paper_bgcolor="rgba(0,0,0,0)" 但需要 .chart-card 的深色背景襯托
- 這個設定本身沒問題，但需要確認 HTML card 有正確套用到

### 2. 水量長條圖使用 st.bar_chart
- 水量使用 Streamlit 內建的 st.bar_chart()，不支援深色卡片包覆
- 如需一致性美化，可改用 Plotly 或 Matplotlib

### 3. Student Status 標題
- 第 773 行 def page_coach_student_history(): 函數內
- 找到 "**Student Status**" 並改為 "本日學員狀態"
- 需確認此文字在檔案中的確切位置

## 待修復清單
1. ✅ 縮排錯誤：將每日攝取趨勢區塊移出 else weights: 分支
2. ⬜ 測試 Plotly 圖表是否正常顯示
3. ⬜ 測試水量長條圖是否正常顯示
4. ⬜ 確認深色卡片 CSS 是否正確套用
