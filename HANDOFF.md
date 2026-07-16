# HANDOFF.md - 底部導航列工作交接

## 📋 任務概述

**目標：** 將教練端頁面的左側欄位（sidebar）導航按鈕移至畫面底部，改為底部導航列。

**目前狀態：** 規劃中，尚未實作

---

## 🎯 需求規格

### 1. 視覺設計

| 項目 | 規格 |
| --- | --- |
| 位置 | 畫面底部居中，距底部 20px |
| 外觀 | 白色背景，圓角 28px，陰影 `0 4px 12px rgba(0,0,0,0.1)` |
| 內距 | padding: 8px 20px |
| z-index | 100 |

### 2. 按鈕設計

| 項目 | 規格 |
| --- | --- |
| 數量 | 2 個（教練端） |
| 排列 | 水平並排，gap: 16px |
| 尺寸 | min-width: 100px, padding: 12px 24px |
| 圓角 | 20px |
| 間距 | 12px 24px |

### 3. 圖示（Font Awesome）

| 頁面 | 圖示 | 說明文字 |
| --- | --- | --- |
| 學員狀態 | `fa-chart-pie` | 學員狀態 |
| 教練歷史 | `fa-users` | 教練歷史 |

### 4. 狀態樣式

| 狀態 | 背景 | 圖示顏色 | 文字顏色 |
| --- | --- | --- | --- |
| 預設 | transparent | #9CA3AF | #9CA3AF |
| 選中（active） | #FFF78B（黃色） | #1F2937 | #1F2937（粗體 600） |

### 5. 點擊行為

- 點擊按鈕後跳轉至對應頁面
- 當前頁面的按鈕顯示黃色背景（active 狀態）

---

## 📁 相關檔案

### HTML 原型
- `D:\projects\Calories\demo_bottom_nav.html` - 底部導航的純 HTML/CSS/JS 原型
- 包含完整的導航切換邏輯和樣式

### CSS 樣式參考
```css
.bottom-nav {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: #ffffff;
    border-radius: 28px;
    padding: 8px 20px;
    display: flex;
    gap: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    z-index: 100;
}

.nav-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 12px 24px;
    border-radius: 20px;
    border: none;
    background: transparent;
    cursor: pointer;
    min-width: 100px;
}

.nav-btn.active {
    background: #FFF78B;
}

.nav-btn i {
    font-size: 24px;
    color: #9CA3AF;
    margin-bottom: 4px;
}

.nav-btn.active i {
    color: #1F2937;
}

.nav-btn span {
    font-size: 12px;
    color: #9CA3AF;
}

.nav-btn.active span {
    color: #1F2937;
    font-weight: 600;
}
```

### JavaScript 導航邏輯
```javascript
function switchPage(page) {
    // 移除所有頁面的 active class
    document.querySelectorAll('.page').forEach(function(p) {
        p.classList.remove('active');
    });
    
    // 移除所有按鈕的 active class
    document.querySelectorAll('.nav-btn').forEach(function(btn) {
        btn.classList.remove('active');
    });
    
    // 顯示目標頁面
    if (page === 'status') {
        document.getElementById('statusPage').classList.add('active');
        document.querySelectorAll('.nav-btn')[0].classList.add('active');
        window.scrollTo(0, 0);
    } else {
        document.getElementById('historyPage').classList.add('active');
        document.querySelectorAll('.nav-btn')[1].classList.add('active');
        window.scrollTo(0, 0);
    }
}
```

---

## ⚠️ 遇到的問題

### 問題 1：Streamlit widget 渲染限制

**描述：** Streamlit 的 `st.button()` 和 `st.markdown()` 渲染順序會導致 styled div 和實際按鈕分離。

**嘗試的解決方案：**

1. **使用 HTML/JS 實現**
   - 使用 `st.html()` 或 `st.markdown(..., unsafe_allow_html=True)` 注入 HTML/CSS/JS
   - 透過 URL query params (`?p=頁面名`) 傳遞導航狀態
   - 使用 `window.location.href` 重新導向

2. **問題：** JavaScript `window.location.href` 會導致整頁重新載入，可能造成 session_state 丟失

### 問題 2：Python 編碼損壞

**描述：** 嘗試修改 app.py 時，中文字元（特別是 CSS 內的內容）被破壞成乱码。

**原因：** PowerShell 和 Python 的字符串轉義混合使用導致編碼問題

**解決方式：** 從 GitHub 恢復乾淨版本

---

## 🔧 建議實作方向

### 方案 A：使用 st.query_params + st.rerun()

```python
# 檢查 URL 參數
query_params = st.query_params
if "p" in query_params:
    nav_page = query_params["p"]
    if nav_page in ["學員狀態", "學員歷史"]:
        st.session_state.page = nav_page
        st.rerun()

# 渲染底部導航 HTML
current_page = st.session_state.get("page", "學員狀態")
active_status = "active" if current_page == "學員狀態" else ""

nav_html = f"""
<div class="bottom-nav">
    <button class="nav-btn {active_status}" onclick="navigateTo('學員狀態')">
        <i class="fas fa-chart-pie"></i>
        <span>學員狀態</span>
    </button>
    ...
</div>
<script>
function navigateTo(page) {{
    const url = new URL(window.location.href);
    url.searchParams.set('p', page);
    window.location.href = url.toString();
}}
</script>
"""
st.html(nav_html)
```

### 方案 B：使用 streamlit-extras 或 custom-component

考虑使用社群元件如 `streamlit-navigation` 或自定義 component

---

## 📝 實作檢查清單

- [ ] 移除 `with st.sidebar:` 區塊
- [ ] 新增 Font Awesome stylesheet link
- [ ] 新增底部導航 CSS 樣式
- [ ] 實作 URL query params 導航邏輯
- [ ] 渲染兩個導航按鈕（學員狀態、教練歷史）
- [ ] 確保 active 狀態正確顯示
- [ ] 測試頁面跳轉正常運作
- [ ] 移除頂部多餘的教練名稱顯示（如有的話）
- [ ] Git commit 並推送到 GitHub

---

## 🔗 參考資源

- [Font Awesome 6.4 Icons](https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css)
- [Streamlit query_params](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.query_params)
- HTML 原型：`D:\projects\Calories\demo_bottom_nav.html`

---

## 📅 建立日期

2026-07-16
