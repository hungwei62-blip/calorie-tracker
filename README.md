# 健身教練管理系統 (Calorie Tracker)

一個基於 Streamlit 的健身教練管理系統，用於管理學員的飲食、訓練和體重記錄。

## 功能特色

- **飲食記錄**：支援 AI 圖片辨識與文字輸入
- **體重追蹤**：記錄並圖表化體重變化
- **熱量計算**：自動計算攝取熱量、蛋白質、碳水、脂肪
- **學員管理**：教練可管理多位學員的飲食與體重

## 技術棧

- **前端**：Streamlit
- **後端**：Python
- **資料庫**：Google Sheets
- **儲存**：Firebase Storage
- **AI**：Google Gemini 2.5 Flash

## 安裝與執行

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 專案結構

```
Calories/
├── app.py              # 主應用程式
├── services/           # 服務模組
├── static/             # 靜態資源
└── requirements.txt    # 依賴套件
```

## 作者

hungwei62
