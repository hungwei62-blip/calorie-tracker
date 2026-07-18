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

                /* 強制使用實際 viewport 寬度，避免手機呈現桌面版內容寬度 */
                .main .block-container {
                    width: 100% !important;
                    max-width: 100% !important;
                    min-width: 0 !important;
                    padding-left: 1rem !important;
                    padding-right: 1rem !important;
                    box-sizing: border-box !important;
                }

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


            /* ===== 學員首頁：縮小頂部留白且不影響其他頁面 ===== */
            .main .block-container:has(.st-key-student_home_header),
            [data-testid="stMainBlockContainer"]:has(.st-key-student_home_header) {
                padding-top: 32px !important;
            }

            .st-key-student_home_header .student-home-welcome {
                margin-top: 0 !important;
            }

            @media (max-width: 768px) {
                .main .block-container:has(.st-key-student_home_header),
                [data-testid="stMainBlockContainer"]:has(.st-key-student_home_header) {
                    padding-top: 32px !important;
                }
            }

            /* ===== 學員每日進度卡：所有尺寸固定雙欄 ===== */
            .st-key-daily_progress_cards [data-testid="stHorizontalBlock"] {
                display: flex !important;
                flex-wrap: nowrap !important;
                gap: 10px !important;
                align-items: stretch !important;
            }

            .st-key-daily_progress_cards [data-testid="stColumn"] {
                flex: 0 0 calc(50% - 5px) !important;
                width: calc(50% - 5px) !important;
                min-width: 0 !important;
                max-width: calc(50% - 5px) !important;
            }

            .st-key-daily_progress_cards div[data-testid="stPlotlyChart"] {
                margin: 0 !important;
                overflow: hidden !important;
                border-radius: 24px !important;
                box-shadow: 0 8px 24px rgba(199, 237, 246, 0.30) !important;
            }

            @media (max-width: 768px) {
                .st-key-daily_progress_cards div[data-testid="stPlotlyChart"] {
                    border-radius: 18px !important;
                }
            }

            /* ===== 學員今日概況：體重與 Calories 固定雙欄 ===== */
            .st-key-daily_summary_cards [data-testid="stHorizontalBlock"] {
                display: flex !important;
                flex-wrap: nowrap !important;
                gap: 10px !important;
                align-items: stretch !important;
            }

            .st-key-daily_summary_cards [data-testid="stColumn"] {
                flex: 0 0 calc(50% - 5px) !important;
                width: calc(50% - 5px) !important;
                min-width: 0 !important;
                max-width: calc(50% - 5px) !important;
            }

            .st-key-daily_summary_cards [data-testid="stColumn"]:first-child {
                position: relative !important;
            }

            .st-key-daily_summary_cards div[data-testid="stPlotlyChart"] {
                height: 180px !important;
                margin: 0 !important;
                overflow: hidden !important;
                border-radius: 24px !important;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04) !important;
            }

            .st-key-daily_summary_cards .weight-card {
                width: 100% !important;
                height: 180px !important;
                min-height: 180px !important;
                padding: 24px !important;
                box-sizing: border-box !important;
                overflow: hidden !important;
                background-color: #f8f8f8 !important;
                border-radius: 24px !important;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.03) !important;
            }

            .st-key-daily_summary_cards .weight-title {
                margin-bottom: 12px !important;
                color: #1a1a1a !important;
                font-family: system-ui, -apple-system, sans-serif !important;
                font-size: 15px !important;
                font-weight: 500 !important;
            }

            .st-key-daily_summary_cards .weight-value {
                color: #1a1a1a !important;
                font-family: system-ui, -apple-system, sans-serif !important;
                font-size: 28px !important;
                font-weight: 700 !important;
                line-height: 1 !important;
            }

            .st-key-daily_summary_cards .weight-unit {
                margin-left: 6px !important;
                color: #a0a0a0 !important;
                font-size: 18px !important;
                font-weight: 400 !important;
            }

            .st-key-daily_summary_cards .weight-trend {
                display: flex !important;
                align-items: center !important;
                margin-top: 12px !important;
                color: #1a1a1a !important;
                font-family: system-ui, -apple-system, sans-serif !important;
                font-size: 14px !important;
                font-weight: 500 !important;
            }

            .st-key-daily_summary_cards .st-key-weight_add_btn {
                position: absolute !important;
                top: 16px !important;
                right: 16px !important;
                width: 40px !important;
                height: 40px !important;
                z-index: 10 !important;
            }

            .st-key-daily_summary_cards .st-key-weight_add_btn button {
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                width: 40px !important;
                min-width: 40px !important;
                max-width: 40px !important;
                height: 40px !important;
                min-height: 40px !important;
                padding: 0 !important;
                color: #6f6f6a !important;
                background-color: rgba(255, 255, 255, 0.76) !important;
                border: 1px solid rgba(120, 120, 115, 0.14) !important;
                border-radius: 50% !important;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
                font-size: 18px !important;
            }

            .st-key-daily_summary_cards .st-key-weight_add_btn button:hover {
                background-color: rgba(255, 255, 255, 0.94) !important;
                box-shadow: 0 3px 10px rgba(0, 0, 0, 0.05) !important;
            }

            .st-key-daily_summary_cards .st-key-weight_add_btn [data-testid="stMarkdownContainer"] {
                position: absolute !important;
                width: 1px !important;
                height: 1px !important;
                padding: 0 !important;
                margin: -1px !important;
                overflow: hidden !important;
                clip: rect(0, 0, 0, 0) !important;
                white-space: nowrap !important;
                border: 0 !important;
            }

            .st-key-daily_summary_cards .st-key-weight_add_btn [data-testid="stIconMaterial"] {
                margin: 0 !important;
                color: #6f6f6a !important;
            }

            @media (max-width: 768px) {
                .st-key-daily_summary_cards div[data-testid="stPlotlyChart"],
                .st-key-daily_summary_cards .weight-card {
                    border-radius: 18px !important;
                }

                .st-key-daily_summary_cards .weight-card {
                    padding: 18px 14px !important;
                }

                .st-key-daily_summary_cards .weight-title {
                    max-width: calc(100% - 38px) !important;
                    font-size: 15px !important;
                }

                .st-key-daily_summary_cards .weight-value {
                    font-size: 28px !important;
                }

                .st-key-daily_summary_cards .weight-unit {
                    margin-left: 4px !important;
                    font-size: 14px !important;
                }

                .st-key-daily_summary_cards .weight-trend {
                    font-size: 11px !important;
                }

                .st-key-daily_summary_cards .st-key-weight_add_btn {
                    top: 12px !important;
                    right: 12px !important;
                    width: 34px !important;
                    height: 34px !important;
                }

                .st-key-daily_summary_cards .st-key-weight_add_btn button {
                    width: 34px !important;
                    min-width: 34px !important;
                    max-width: 34px !important;
                    height: 34px !important;
                    min-height: 34px !important;
                    font-size: 15px !important;
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
                top: auto !important;
                left: 50% !important;
                right: auto !important;
                bottom: 12px !important;
                bottom: calc(12px + constant(safe-area-inset-bottom)) !important;
                bottom: calc(12px + env(safe-area-inset-bottom, 0px)) !important;
                margin: 0 !important;
                -webkit-transform: translate3d(-50%, 0, 0) !important;
                transform: translate3d(-50%, 0, 0) !important;
                will-change: transform;
                z-index: 2147483000 !important;
                width: max-content !important;
                max-width: calc(100vw - 24px) !important;
                padding: 6px 16px !important;
                overflow: visible !important;
                background: #f7f7f7 !important;
                border: 1px solid rgba(238, 238, 238, 0.95) !important;
                border-radius: 999px !important;
                box-shadow: 0 4px 16px rgba(31, 41, 55, 0.09) !important;
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
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
                gap: 6px !important;
            }

            .st-key-bottom_navigation [data-testid="stColumn"] {
                flex: 0 0 auto !important;
                width: 48px !important;
                min-width: 48px !important;
                max-width: 48px !important;
            }

            .st-key-bottom_navigation div.stButton {
                width: 48px !important;
                min-width: 48px !important;
                max-width: 48px !important;
                height: 48px !important;
                border: none !important;
                outline: none !important;
                box-shadow: none !important;
            }

            .st-key-bottom_navigation div.stButton > button,
            .st-key-bottom_navigation button[data-testid^="stBaseButton"] {
                width: 48px !important;
                min-width: 48px !important;
                max-width: 48px !important;
                height: 48px !important;
                min-height: 48px !important;
                max-height: 48px !important;
                aspect-ratio: 1 / 1 !important;
                padding: 0 !important;
                border-radius: 50% !important;
                color: #242424 !important;
                background: #ffffff !important;
                border: none !important;
                outline: none !important;
                box-shadow: none !important;
                transition: transform 0.12s ease, background-color 0.12s ease,
                            box-shadow 0.12s ease !important;
            }

            .st-key-bottom_navigation button::before,
            .st-key-bottom_navigation button::after {
                border: none !important;
                outline: none !important;
                box-shadow: none !important;
            }

            /* 視覺隱藏文字，保留按鈕名稱供螢幕閱讀器辨識。 */
            .st-key-bottom_navigation div.stButton [data-testid="stMarkdownContainer"] {
                position: absolute !important;
                width: 1px !important;
                height: 1px !important;
                padding: 0 !important;
                margin: -1px !important;
                overflow: hidden !important;
                clip: rect(0, 0, 0, 0) !important;
                white-space: nowrap !important;
                border: 0 !important;
            }

            .st-key-bottom_navigation [data-testid="stIconMaterial"] {
                margin: 0 !important;
                font-size: 22px !important;
                line-height: 1 !important;
            }

            .st-key-bottom_navigation div.stButton > button:hover,
            .st-key-bottom_navigation button[data-testid^="stBaseButton"]:hover {
                background: #ffffff !important;
                border: none !important;
                outline: none !important;
                box-shadow: none !important;
            }

            .st-key-bottom_navigation div.stButton > button:active,
            .st-key-bottom_navigation button[data-testid^="stBaseButton"]:active {
                background: #FFF08A !important;
                border: none !important;
                outline: none !important;
                transform: scale(0.94) !important;
                box-shadow: none !important;
            }

            .st-key-bottom_navigation div.stButton > button:focus,
            .st-key-bottom_navigation button[data-testid^="stBaseButton"]:focus {
                border: none !important;
                outline: none !important;
                box-shadow: none !important;
            }

            .st-key-bottom_navigation div.stButton > button:focus-visible,
            .st-key-bottom_navigation button[data-testid^="stBaseButton"]:focus-visible {
                border: none !important;
                outline: none !important;
                box-shadow: 0 0 0 3px rgba(255, 240, 138, 0.85) !important;
            }


            /* 內容不被導航列遮住 */
            .main .block-container {
                padding-bottom: 100px !important;
                padding-bottom: calc(100px + constant(safe-area-inset-bottom)) !important;
                padding-bottom: calc(100px + env(safe-area-inset-bottom, 0px)) !important;
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
