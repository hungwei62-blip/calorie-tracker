"""共用 Streamlit 視覺樣式。"""
import streamlit as st


def apply_global_styles() -> None:
        st.markdown("""

        <style>

            @import url('https://fonts.googleapis.com/css2?family=Line+Seed+JP:wght@400&display=swap');

            .stApp {

                background-color: #FFFFFF !important;

                color: #2F3E46 !important;

                font-family: 'Line Seed JP', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;

            }

            h1, h2, h3, h4, h5, h6 {

                color: #2F3E46 !important;

                font-weight: 400 !important;

            }

            div[data-testid="stMetric"] {

                background-color: #FFFFFF !important;

                padding: 20px 24px !important;

                border-radius: 16px !important;

                box-shadow: 0 8px 24px rgba(149, 157, 165, 0.06) !important;

            }

            div[data-testid="stMetric"] label {

                color: #666 !important;

            }

            div[data-testid="stMetric"] [data-testid="stMetricValue"] {

                color: #2F3E46 !important;

            }

            div[data-testid="stSidebar"] {

                background-color: #F8F9FA !important;

            }

            div.stButton > button {

                background-color: #4A7C59 !important;

                color: #FFFFFF !important;

                border-radius: 12px !important;

                border: none !important;

                padding: 0.5rem 1rem !important;

            }

            div.stButton > button:hover {

                background-color: #385E43 !important;

            }

            div[data-testid="stFormSubmitButton"] button {

                background-color: #4A7C59 !important;

                color: #FFFFFF !important;

                border-radius: 12px !important;

                border: none !important;

                padding: 0.6rem 2rem !important;

            }

            div[data-testid="stFormSubmitButton"] button:hover {

                background-color: #385E43 !important;

            }

            div[data-testid="stTabs"] button[aria-selected="true"] {

                background-color: #4A7C59 !important;

                color: #FFFFFF !important;

            }

            body, .stApp, .stApp > div, .main, .main > div,

            .block-container, section.main > div,

            [data-testid="stSidebar"], [data-testid="stSidebarContent"],

            div[data-testid="stVerticalBlock"], div[data-testid="stHorizontalBlock"],

            .stTabs, div[data-testid="stTabContent"],

            .stForm, [data-testid="stFormSubmitButton"] {

                background-color: #FFFFFF !important;

            }

            [data-testid="stTabsContent"] {

                background-color: #FFFFFF !important;

            }

            .stTabs * {

                background-color: #FFFFFF !important;

            }

            div[data-testid="stProgressBar"] > div > div {

                background-color: #4A7C59 !important;

            }

            /* ===== Mobile Responsive (手機響應式) ===== */
            @media (max-width: 768px) {
                /* 調整區塊標題大小 */
                h1 { font-size: 1.4rem !important; }
                h2 { font-size: 1.2rem !important; }
                h3 { font-size: 1rem !important; }

                /* Metric 卡片在手機上更好看 */
                div[data-testid="stMetric"] {
                    margin-bottom: 8px !important;
                    padding: 12px !important;
                    border-radius: 12px !important;
                }

                /* 側邊欄調整 */
                [data-testid="stSidebar"] {
                    width: 200px !important;
                    min-width: 200px !important;
                }

                /* 讓所有 columns 在手機上自動換行 */
                .stColumns > div {
                    flex-wrap: wrap !important;
                }

                /* 4欄 -> 2x2 在手機上 */
                div.stHorizontalBlock:has(> div:nth-child(4)) {
                    flex-wrap: wrap !important;
                }
                div.stHorizontalBlock:has(> div:nth-child(4)) > div {
                    min-width: 48% !important;
                    flex: 0 0 48% !important;
                }

                /* 5欄 -> 3+2 或全部堆疊 */
                div.stHorizontalBlock:has(> div:nth-child(5)) {
                    flex-wrap: wrap !important;
                }
                div.stHorizontalBlock:has(> div:nth-child(5)) > div {
                    min-width: 48% !important;
                    flex: 0 0 48% !important;
                }

                /* 按鈕全寬 */
                div.stButton > button,
                div[data-testid="stFormSubmitButton"] button {
                    width: 100% !important;
                    padding: 0.5rem 1rem !important;
                    font-size: 0.9rem !important;
                }

                /* 表單輸入框全寬 */
                .stTextInput > div > div > input,
                .stNumberInput > div > div > input,
                .stTextArea > div > div > textarea,
                .stSelectbox > div > div > select {
                    width: 100% !important;
                }

                /* 資料表可橫向滾動 */
                .dataframe {
                    overflow-x: auto !important;
                    display: block !important;
                }

                /* Tabs 在手機上可橫向滾動 */
                div[data-testid="stTabs"] {
                    overflow-x: auto !important;
                    white-space: nowrap !important;
                }

                /* 進度條調整 */
                div[data-testid="stProgressBar"] {
                    height: 8px !important;
                }

                /* 下載按鈕在手機上全寬 */
                .stDownloadButton > button {
                    width: 100% !important;
                }

                /* Expander 在手機上全寬 */
                .streamlit-expanderHeader {
                    font-size: 0.9rem !important;
                }
            }

            /* 超小手機 (320px - 400px) */
            @media (max-width: 400px) {
                h1 { font-size: 1.2rem !important; }
                h2 { font-size: 1.1rem !important; }
                h3 { font-size: 0.95rem !important; }

                div[data-testid="stMetric"] {
                    padding: 10px !important;
                }

                /* 4欄直接變成2欄 */
                div.stHorizontalBlock:has(> div:nth-child(4)) > div {
                    min-width: 100% !important;
                    flex: 0 0 100% !important;
                }

                /* 5欄也變成2欄 */
                div.stHorizontalBlock:has(> div:nth-child(5)) > div {
                    min-width: 100% !important;
                    flex: 0 0 100% !important;
                }
            }


            /* ===== Dashboard Styles (教練端) ===== */

            /* 狀態指示燈 */
            .status-green { color: #22C55E; }
            .status-yellow { color: #EAB308; }
            .status-red { color: #DC2626; }

            /* 學員卡片容器 */
            .student-card {
                background: #FFFFFF;
                border-radius: 16px;
                padding: 20px;
                margin: 10px 0;
                border: 1px solid #E5E7EB;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            }

            /* 進度條優化 */
            div[data-testid="stProgressBar"] {
                height: 12px !important;
                border-radius: 6px !important;
                background-color: #E5E7EB !important;
            }

            div[data-testid="stProgressBar"] > div > div {
                background: linear-gradient(90deg, #22C55E, #10B981) !important;
                border-radius: 6px !important;
            }

            /* 警示進度條 */
            .progress-warning > div > div {
                background: linear-gradient(90deg, #EAB308, #F59E0B) !important;
            }

            .progress-danger > div > div {
                background: linear-gradient(90deg, #DC2626, #EF4444) !important;
            }

            /* 數據卡片 */
            .metric-card {
                background: #FFFFFF;
                border-radius: 12px;
                padding: 16px;
                border: 1px solid #E5E7EB;
                text-align: center;
            }

            /* 即時更新指示 */
            .live-indicator {
                display: inline-block;
                width: 10px;
                height: 10px;
                background-color: #22C55E;
                border-radius: 50%;
                animation: pulse 2s infinite;
            }

            @keyframes pulse {
                0% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }
                70% { box-shadow: 0 0 0 10px rgba(34, 197, 94, 0); }
                100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
            }

            /* 按鍵樣式優化 */
            div.stButton > button {
                background-color: #3B82F6 !important;
                border-radius: 8px !important;
            }

            div.stButton > button:hover {
                background-color: #2563EB !important;
            }


            /* ========================================== */
            /* ========================================== */
            /* 底部導航 - 簡化版（按鈕在 layout 流中） */
            /* ========================================== */

            /* 按鈕樣式 - 48x48 圓形白色按鈕 */
            .st-key-bottom_navigation {
                position: fixed !important;
                left: 50% !important;
                bottom: max(12px, env(safe-area-inset-bottom)) !important;
                transform: translateX(-50%) !important;
                z-index: 1000 !important;
                width: max-content !important;
                max-width: calc(100vw - 24px) !important;
                padding: 8px !important;
                overflow-x: auto !important;
                overflow-y: hidden !important;
                overscroll-behavior-x: contain;
                -webkit-overflow-scrolling: touch;
                scrollbar-width: none;
                background: rgba(255, 255, 255, 0.92) !important;
                border: 1px solid rgba(229, 231, 235, 0.9) !important;
                border-radius: 20px !important;
                box-shadow: 0 12px 32px rgba(31, 41, 55, 0.16) !important;
                backdrop-filter: blur(14px);
                -webkit-backdrop-filter: blur(14px);
            }

            /* Hover 效果 */
            .st-key-bottom_navigation::-webkit-scrollbar {
                display: none;
            }

            .st-key-bottom_navigation > div,
            .st-key-bottom_navigation [data-testid="stHorizontalBlock"],
            .st-key-bottom_navigation [data-testid="stColumn"] {
                background: transparent !important;
            }

            .st-key-bottom_navigation [data-testid="stHorizontalBlock"] {
                min-width: max-content !important;
                flex-wrap: nowrap !important;
                justify-content: center !important;
                gap: 8px !important;
            }

            .st-key-bottom_navigation [data-testid="stColumn"] {
                flex: 0 0 auto !important;
                width: auto !important;
                min-width: 88px !important;
            }

            .st-key-bottom_navigation div.stButton > button {
                min-width: 88px !important;
                height: 48px !important;
                padding: 0.5rem 0.75rem !important;
                border-radius: 14px !important;
                white-space: nowrap !important;
                font-size: 0.86rem !important;
                font-weight: 600 !important;
                line-height: 1 !important;
                transition: transform 0.18s ease, background-color 0.18s ease,
                            color 0.18s ease, box-shadow 0.18s ease !important;
            }

            .st-key-bottom_navigation button[data-testid="stBaseButton-secondary"] {
                color: #4B5563 !important;
                background: rgba(255, 255, 255, 0.72) !important;
                border: 1px solid transparent !important;
                box-shadow: none !important;
            }

            .st-key-bottom_navigation button[data-testid="stBaseButton-primary"] {
                color: #FFFFFF !important;
                background: #4A7C59 !important;
                border: 1px solid #4A7C59 !important;
                box-shadow: 0 5px 12px rgba(74, 124, 89, 0.24) !important;
            }

            .st-key-bottom_navigation div.stButton > button:hover {
                transform: translateY(-1px) !important;
            }

            .st-key-bottom_navigation div.stButton > button:focus-visible {
                outline: 3px solid rgba(74, 124, 89, 0.28) !important;
                outline-offset: 2px !important;
            }


            /* 內容不被導航列遮住 */
            .main .block-container {
                padding-bottom: calc(112px + env(safe-area-inset-bottom)) !important;
            }

            @media (max-width: 768px) {
                .st-key-bottom_navigation {
                    left: 12px !important;
                    right: 12px !important;
                    transform: none !important;
                    width: auto !important;
                    max-width: none !important;
                }

                .st-key-bottom_navigation [data-testid="stHorizontalBlock"] {
                    justify-content: safe center !important;
                }
            }




            /* ============================================================
               強制限制登入表單（st.form）寬度並使其水平置中
               ============================================================ */
            div[data-testid="stForm"] {
                max-width: 400px !important;              /* 限制最大寬度，防止橫向拉長 */
                width: 100% !important;
                margin: 40px auto !important;            /* 頂部外距 40px，auto 達成水平置中 */
                background: #ffffff !important;          /* 純白卡片背景 */
                border-radius: 32px !important;          /* 大圓角 */
                padding: 30px !important;                 /* 內部留白 */
                border: 1px solid #E5E7EB !important;     /* 柔和細邊框 */
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05) !important; /* 懸浮感陰影 */
                box-sizing: border-box !important;
            }

            /* 確保 Form 內部的元素不會溢出 */
            div[data-testid="stForm"] > div {
                width: 100% !important;
                box-sizing: border-box !important;
            }



        </style>

        """, unsafe_allow_html=True)
