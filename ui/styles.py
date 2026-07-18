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
            [data-testid="stMainBlockContainer"]:has(.st-key-student_home_header),
            .main .block-container:has(.st-key-coach_overview_header),
            [data-testid="stMainBlockContainer"]:has(.st-key-coach_overview_header) {
                padding-top: 32px !important;
            }

            .st-key-student_home_header .student-home-welcome,
            .st-key-coach_overview_header .coach-home-welcome {
                margin-top: 0 !important;
            }

            .main .block-container:has(.st-key-daily_completion_card),
            [data-testid="stMainBlockContainer"]:has(.st-key-daily_completion_card) {
                padding-bottom: 80px !important;
                padding-bottom: calc(80px + constant(safe-area-inset-bottom)) !important;
                padding-bottom: calc(80px + env(safe-area-inset-bottom, 0px)) !important;
            }

            @media (max-width: 768px) {
                .main .block-container:has(.st-key-student_home_header),
                [data-testid="stMainBlockContainer"]:has(.st-key-student_home_header),
                .main .block-container:has(.st-key-coach_overview_header),
                [data-testid="stMainBlockContainer"]:has(.st-key-coach_overview_header) {
                    padding-top: 32px !important;
                }
            }

            /* ===== 學員日常紀錄：首頁一致的無圖示卡片風格 ===== */
            .main .block-container:has(.st-key-daily_record_page),
            [data-testid="stMainBlockContainer"]:has(.st-key-daily_record_page) {
                padding-top: 32px !important;
            }

            .st-key-daily_record_page {
                font-family: system-ui, -apple-system, sans-serif !important;
            }

            @media (max-width: 768px) {
                .main .block-container:has(.st-key-daily_record_page),
                [data-testid="stMainBlockContainer"]:has(.st-key-daily_record_page) {
                    padding-top: 32px !important;
                }
            }

            .st-key-daily_record_page [data-baseweb="tab-list"] {
                gap: 4px !important;
                min-height: 58px !important;
                padding: 6px !important;
                align-items: center !important;
                overflow: visible !important;
                background: #f7f7f7 !important;
                border: 1px solid rgba(120, 120, 115, 0.12) !important;
                border-radius: 999px !important;
                box-shadow: 0 6px 18px rgba(0, 0, 0, 0.04) !important;
            }

            .st-key-daily_record_page button[data-baseweb="tab"] {
                min-height: 42px !important;
                padding: 10px 16px !important;
                color: #545451 !important;
                background: transparent !important;
                border-radius: 999px !important;
                font-size: 14px !important;
                font-weight: 500 !important;
                line-height: 1.35 !important;
                overflow: visible !important;
            }

            .st-key-daily_record_page button[data-baseweb="tab"][aria-selected="true"] {
                color: #1a1a1a !important;
                background: #ffffff !important;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06) !important;
            }

            .st-key-daily_record_page [data-baseweb="tab-highlight"] {
                display: none !important;
            }

            .st-key-daily_record_page [data-testid="stTabs"],
            .st-key-daily_record_page [data-testid="stTabsContent"] {
                overflow: visible !important;
            }

            .st-key-daily_record_page [data-testid="stTabContent"] {
                padding-top: 18px !important;
            }

            .st-key-daily_record_page [data-testid="stTabContent"]:has(.st-key-food_record_panel) {
                padding-top: 12px !important;
            }

            .st-key-food_record_panel,
            .st-key-food_record_panel [data-testid="stForm"] {
                margin-bottom: 0 !important;
            }

            .st-key-food_record_panel > div[data-testid="stVerticalBlock"] {
                gap: 12px !important;
            }

            .main .block-container:has(.st-key-food_record_panel),
            [data-testid="stMainBlockContainer"]:has(.st-key-food_record_panel) {
                padding-bottom: 80px !important;
                padding-bottom: calc(80px + constant(safe-area-inset-bottom)) !important;
                padding-bottom: calc(80px + env(safe-area-inset-bottom, 0px)) !important;
            }

            .st-key-daily_record_page [data-testid="stForm"],
            .st-key-daily_record_page [data-testid="stFileUploader"],
            .st-key-daily_record_page [data-testid="stCameraInput"] {
                padding: 22px !important;
                background: #f8f8f8 !important;
                border: 1px solid rgba(120, 120, 115, 0.08) !important;
                border-radius: 24px !important;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.03) !important;
            }

            .st-key-daily_record_page [data-testid="stMetric"] {
                padding: 18px !important;
                background: #f8f8f8 !important;
                border-radius: 18px !important;
            }

            .st-key-daily_record_page div.stButton > button,
            .st-key-daily_record_page div[data-testid="stFormSubmitButton"] button,
            .st-key-daily_record_page button[data-testid^="stBaseButton"]:not([data-baseweb="tab"]) {
                min-height: 46px !important;
                padding: 10px 16px !important;
                color: #343431 !important;
                background: #ffffff !important;
                border: 1px solid rgba(112, 112, 106, 0.24) !important;
                border-radius: 10px !important;
                outline: none !important;
                box-shadow: none !important;
                font-family: system-ui, -apple-system, sans-serif !important;
                font-size: 14px !important;
                font-weight: 500 !important;
                line-height: 1.35 !important;
            }

            .st-key-daily_record_page div.stButton > button:hover,
            .st-key-daily_record_page div[data-testid="stFormSubmitButton"] button:hover,
            .st-key-daily_record_page button[data-testid^="stBaseButton"]:not([data-baseweb="tab"]):hover {
                color: #242421 !important;
                background: #f5f5f2 !important;
                border-color: rgba(96, 96, 90, 0.34) !important;
                box-shadow: none !important;
            }

            .st-key-daily_record_page div.stButton > button:active,
            .st-key-daily_record_page div[data-testid="stFormSubmitButton"] button:active,
            .st-key-daily_record_page button[data-testid^="stBaseButton"]:not([data-baseweb="tab"]):active {
                background: #ecece8 !important;
                transform: scale(0.99) !important;
            }

            .st-key-daily_record_page div.stButton > button:focus-visible,
            .st-key-daily_record_page div[data-testid="stFormSubmitButton"] button:focus-visible,
            .st-key-daily_record_page button[data-testid^="stBaseButton"]:not([data-baseweb="tab"]):focus-visible {
                outline: 2px solid rgba(112, 112, 106, 0.30) !important;
                outline-offset: 2px !important;
            }

            .st-key-daily_record_page button[aria-pressed="true"],
            .st-key-daily_record_page button[data-active="true"] {
                color: #1f1f1c !important;
                background: #eeeeea !important;
                border-color: rgba(96, 96, 90, 0.30) !important;
            }

            .st-key-daily_record_page button > div,
            .st-key-daily_record_page button [data-testid="stMarkdownContainer"],
            .st-key-daily_record_page button p,
            .st-key-daily_record_page button span {
                color: inherit !important;
                background: transparent !important;
            }

            @media (max-width: 768px) {
                .st-key-daily_record_page [data-baseweb="tab-list"] {
                    width: 100% !important;
                    min-height: 58px !important;
                }

                .st-key-daily_record_page button[data-baseweb="tab"] {
                    flex: 1 1 25% !important;
                    min-width: 0 !important;
                    min-height: 42px !important;
                    padding: 10px 5px !important;
                    font-size: 13px !important;
                }

                .st-key-daily_record_page [data-testid="stForm"],
                .st-key-daily_record_page [data-testid="stFileUploader"],
                .st-key-daily_record_page [data-testid="stCameraInput"] {
                    padding: 16px !important;
                    border-radius: 18px !important;
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
                height: 180px !important;
                min-height: 180px !important;
                max-height: 180px !important;
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
                background-color: #e8e5f4 !important;
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
                flex-wrap: nowrap !important;
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
                    padding: 24px 14px !important;
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

            /* ===== 學員今日完成度：原四卡下方的緊湊摘要 ===== */
            .st-key-daily_completion_card {
                margin-top: -4px !important;
            }

            .st-key-daily_completion_card .daily-completion-card {
                box-sizing: border-box !important;
                width: 100% !important;
                min-height: 104px !important;
                padding: 12px 16px !important;
                color: #252525 !important;
                background: rgba(250, 250, 250, 0.96) !important;
                border: 1px solid rgba(120, 120, 115, 0.10) !important;
                border-radius: 22px !important;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.035) !important;
                font-family: system-ui, -apple-system, sans-serif !important;
            }

            .daily-completion-heading,
            .daily-completion-footer,
            .daily-completion-items {
                display: flex !important;
                align-items: center !important;
            }

            .daily-completion-heading {
                justify-content: space-between !important;
                font-size: 14px !important;
                font-weight: 500 !important;
                line-height: 1.2 !important;
            }

            .daily-completion-heading strong {
                color: #1a1a1a !important;
                font-size: 22px !important;
                font-weight: 650 !important;
            }

            .daily-completion-track {
                width: 100% !important;
                height: 8px !important;
                margin-top: 6px !important;
                overflow: hidden !important;
                background: #ececea !important;
                border-radius: 999px !important;
            }

            .daily-completion-track > span {
                display: block !important;
                height: 100% !important;
                background: #b9c9d6 !important;
                border-radius: inherit !important;
                transition: width 180ms ease !important;
            }

            .daily-completion-card.has-bonus .daily-completion-track > span {
                background: linear-gradient(90deg, #acd9f5 0%, #d8c8f2 54%, #ffb9a7 100%) !important;
                box-shadow: 0 0 10px rgba(178, 157, 225, 0.42) !important;
            }

            .daily-completion-footer {
                justify-content: space-between !important;
                gap: 10px !important;
                margin-top: 7px !important;
            }

            .daily-completion-meta {
                flex: 0 0 auto !important;
                color: #777773 !important;
                font-size: 11px !important;
                line-height: 1.2 !important;
            }

            .daily-completion-items {
                justify-content: flex-end !important;
                gap: 10px !important;
            }

            .daily-completion-item {
                position: relative !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                width: 30px !important;
                height: 30px !important;
                color: #91918d !important;
                background: #f1f1ef !important;
                border-radius: 50% !important;
            }

            .daily-completion-item.is-complete {
                color: #6f7790 !important;
                background: #f0eff7 !important;
            }

            .daily-completion-icon,
            .daily-completion-icon svg {
                display: block !important;
                width: 18px !important;
                height: 18px !important;
            }

            .daily-completion-icon svg,
            .daily-completion-badge svg {
                fill: none !important;
                stroke: currentColor !important;
                stroke-width: 1.7 !important;
                stroke-linecap: round !important;
                stroke-linejoin: round !important;
            }

            .daily-completion-badge {
                position: absolute !important;
                top: -4px !important;
                right: -4px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                width: 14px !important;
                height: 14px !important;
                color: #ffffff !important;
                background: #a6a6a2 !important;
                border: 2px solid #fafafa !important;
                border-radius: 50% !important;
            }

            .daily-completion-item.is-complete .daily-completion-badge {
                background: #7b9f8a !important;
            }

            .daily-completion-badge svg {
                width: 10px !important;
                height: 10px !important;
                stroke-width: 2.1 !important;
            }

            @media (max-width: 768px) {
                .st-key-student_home_header .student-home-welcome,
                .st-key-coach_overview_header .coach-home-welcome {
                    margin-bottom: 14px !important;
                }

                .daily-completion-items {
                    gap: 8px !important;
                }
            }

            @media (max-width: 768px) and (max-height: 700px) {
                .st-key-daily_summary_cards div[data-testid="stPlotlyChart"],
                .st-key-daily_summary_cards .weight-card,
                .st-key-daily_progress_cards div[data-testid="stPlotlyChart"] {
                    height: 158px !important;
                    min-height: 158px !important;
                }

                .st-key-daily_progress_cards [data-testid="stColumn"] {
                    max-height: 158px !important;
                }

                .st-key-daily_summary_cards .weight-card {
                    padding: 18px 14px !important;
                }

                .st-key-daily_summary_cards .weight-title {
                    margin-bottom: 8px !important;
                }

                .st-key-daily_summary_cards .weight-trend {
                    margin-top: 8px !important;
                }

                .st-key-daily_completion_card .daily-completion-card {
                    min-height: 94px !important;
                    padding: 9px 12px !important;
                    border-radius: 18px !important;
                }

                .daily-completion-heading strong {
                    font-size: 20px !important;
                }

                .daily-completion-footer {
                    margin-top: 5px !important;
                }

                .daily-completion-item {
                    width: 27px !important;
                    height: 27px !important;
                }

                .daily-completion-icon,
                .daily-completion-icon svg {
                    width: 16px !important;
                    height: 16px !important;
                }
            }

            /* ===== 手機版四張首頁卡片：由欄寬推導精確 1:1 ===== */
            @media (max-width: 480px) {
                .st-key-daily_summary_cards .weight-card,
                .st-key-daily_summary_cards div[data-testid="stPlotlyChart"],
                .st-key-daily_progress_cards div[data-testid="stPlotlyChart"] {
                    width: 100% !important;
                    height: auto !important;
                    min-height: 0 !important;
                    max-height: none !important;
                    aspect-ratio: 1 / 1 !important;
                }

                .st-key-daily_progress_cards [data-testid="stColumn"] {
                    max-height: none !important;
                }

                .st-key-daily_summary_cards div[data-testid="stPlotlyChart"] > div,
                .st-key-daily_progress_cards div[data-testid="stPlotlyChart"] > div,
                .st-key-daily_summary_cards .js-plotly-plot,
                .st-key-daily_progress_cards .js-plotly-plot,
                .st-key-daily_summary_cards .plot-container,
                .st-key-daily_progress_cards .plot-container,
                .st-key-daily_summary_cards .svg-container,
                .st-key-daily_progress_cards .svg-container {
                    width: 100% !important;
                    height: 100% !important;
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
            .st-key-auth_brand .auth-brand-lockup {
                width: 100% !important;
                margin: 0 auto !important;
                text-align: center !important;
                font-family: system-ui, -apple-system, "Segoe UI", sans-serif !important;
            }

            .st-key-auth_brand .auth-brand-title {
                display: grid !important;
                grid-template-columns: max-content max-content 105px !important;
                align-items: center !important;
                justify-content: center !important;
                gap: 0.22em !important;
                width: max-content !important;
                max-width: 100% !important;
                margin: 0 auto !important;
                color: #2f3e46 !important;
                font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", sans-serif !important;
                font-size: clamp(18px, 2.8vw, 24px) !important;
                font-weight: 600 !important;
                line-height: 1.25 !important;
                white-space: nowrap !important;
            }

            .st-key-auth_brand .auth-brand-english {
                min-width: 0 !important;
                white-space: nowrap !important;
                font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", sans-serif !important;
                letter-spacing: 0.045em !important;
            }

            .st-key-auth_brand .auth-brand-logo-frame {
                display: block !important;
                min-width: 0 !important;
                width: 100% !important;
                height: 31px !important;
                overflow: hidden !important;
                background: #ffffff !important;
            }

            .st-key-auth_brand .auth-brand-logo {
                display: block !important;
                width: 100% !important;
                height: 100% !important;
                object-fit: cover !important;
                object-position: center !important;
            }

            .st-key-auth_brand .auth-brand-divider {
                min-width: 0 !important;
                white-space: nowrap !important;
                color: #a3aaa7 !important;
                font-weight: 300 !important;
            }

            .st-key-auth_brand .auth-brand-tagline {
                max-width: 680px !important;
                margin: 14px auto 0 !important;
                color: #6f7774 !important;
                font-family: "PingFang TC", "PingFang SC", "Noto Sans TC", "Microsoft JhengHei", system-ui, sans-serif !important;
                font-size: 15px !important;
                font-weight: 400 !important;
                line-height: 1.8 !important;
                letter-spacing: 0.025em !important;
                text-align: center !important;
            }

            .st-key-auth_brand .auth-brand-tagline span {
                display: block !important;
            }

            @media (max-width: 768px) {
                .st-key-auth_brand .auth-brand-title {
                    grid-template-columns: max-content max-content 80px !important;
                    font-size: clamp(14px, 4.4vw, 18px) !important;
                    gap: 0.14em !important;
                }

                .st-key-auth_brand .auth-brand-logo-frame {
                    height: 24px !important;
                }

                .st-key-auth_brand .auth-brand-tagline {
                    max-width: 360px !important;
                    margin-top: 12px !important;
                    padding: 0 6px !important;
                    font-size: 14px !important;
                    line-height: 1.75 !important;
                }
            }

            .st-key-login_panel div[data-testid="stFormSubmitButton"] button,
            .st-key-login_secondary_action div.stButton > button {
                min-height: 44px !important;
                color: #414541 !important;
                background: rgba(255, 255, 255, 0.72) !important;
                background-color: rgba(255, 255, 255, 0.72) !important;
                border: 1px solid rgba(112, 116, 110, 0.24) !important;
                border-radius: 12px !important;
                outline: none !important;
                box-shadow: none !important;
                font-family: "PingFang TC", "Noto Sans TC", "Microsoft JhengHei", system-ui, sans-serif !important;
                font-size: 14px !important;
                font-weight: 500 !important;
                transition: background-color 120ms ease, border-color 120ms ease, transform 120ms ease !important;
            }

            .st-key-login_panel div[data-testid="stFormSubmitButton"] button {
                width: 100% !important;
            }

            .st-key-login_secondary_action,
            .st-key-login_secondary_action div.stButton,
            .st-key-login_secondary_action div.stButton > button {
                width: fit-content !important;
            }

            .st-key-login_panel div[data-testid="stFormSubmitButton"] button:hover,
            .st-key-login_secondary_action div.stButton > button:hover {
                color: #2f332f !important;
                background: rgba(247, 247, 244, 0.94) !important;
                background-color: rgba(247, 247, 244, 0.94) !important;
                border-color: rgba(96, 100, 94, 0.34) !important;
                box-shadow: none !important;
            }

            .st-key-login_panel div[data-testid="stFormSubmitButton"] button:active,
            .st-key-login_secondary_action div.stButton > button:active {
                background: rgba(237, 237, 232, 0.96) !important;
                background-color: rgba(237, 237, 232, 0.96) !important;
                transform: scale(0.99) !important;
            }

            .st-key-login_panel div[data-testid="stFormSubmitButton"] button:focus-visible,
            .st-key-login_secondary_action div.stButton > button:focus-visible {
                outline: 2px solid rgba(112, 116, 110, 0.30) !important;
                outline-offset: 2px !important;
            }

            .st-key-login_panel div[data-testid="stFormSubmitButton"] button > div,
            .st-key-login_panel div[data-testid="stFormSubmitButton"] button p,
            .st-key-login_secondary_action div.stButton > button > div,
            .st-key-login_secondary_action div.stButton > button p {
                color: inherit !important;
                background: transparent !important;
            }

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
