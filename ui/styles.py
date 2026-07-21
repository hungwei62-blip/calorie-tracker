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
            [data-testid="stMainBlockContainer"]:has(.st-key-coach_overview_header),
            .main .block-container:has(.st-key-student_history_page),
            [data-testid="stMainBlockContainer"]:has(.st-key-student_history_page) {
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
                [data-testid="stMainBlockContainer"]:has(.st-key-coach_overview_header),
                .main .block-container:has(.st-key-student_history_page),
                [data-testid="stMainBlockContainer"]:has(.st-key-student_history_page) {
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
            .st-key-daily_record_page [data-testid="stFileUploader"] {
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

            /* ===== 學員日常紀錄：四分頁共用霧藍奶杏色票 ===== */
            .stApp:has(.st-key-daily_record_page),
            .stApp:has(.st-key-daily_record_page) .main,
            .stApp:has(.st-key-daily_record_page) [data-testid="stAppViewContainer"],
            .stApp:has(.st-key-daily_record_page) [data-testid="stMain"] {
                background: #FAFBFC !important;
            }

            .st-key-daily_record_page {
                --daily-record-primary-text: #27303D;
                --daily-record-secondary-text: #7C8798;
                --daily-record-tab-background: #EEF3F8;
                --daily-record-tab-selected: #F5E7DF;
                --daily-record-tab-selected-text: #B97C64;
                --daily-record-border: #E7EDF3;
                --daily-record-cta-background: #F6E8DE;
                --daily-record-cta-text: #B88470;
            }

            .st-key-daily_record_page h1,
            .st-key-daily_record_page h2,
            .st-key-daily_record_page h3,
            .st-key-daily_record_page [data-testid="stWidgetLabel"] p {
                color: var(--daily-record-primary-text) !important;
            }

            .st-key-daily_record_page [data-baseweb="tab-list"] {
                background: var(--daily-record-tab-background) !important;
                border-color: var(--daily-record-border) !important;
                box-shadow: 0 8px 22px rgba(124, 135, 152, 0.08) !important;
            }

            .st-key-daily_record_page button[data-baseweb="tab"] {
                color: var(--daily-record-secondary-text) !important;
            }

            .st-key-daily_record_page button[data-baseweb="tab"][aria-selected="true"] {
                color: var(--daily-record-tab-selected-text) !important;
                background: var(--daily-record-tab-selected) !important;
                box-shadow: 0 3px 10px rgba(185, 124, 100, 0.10) !important;
            }

            .st-key-daily_record_page [data-testid="stForm"],
            .st-key-daily_record_page [data-testid="stFileUploader"] {
                color: var(--daily-record-primary-text) !important;
                background: #FFFFFF !important;
                border-color: var(--daily-record-border) !important;
                box-shadow: 0 10px 28px rgba(124, 135, 152, 0.08) !important;
            }

            .st-key-daily_record_page [data-testid="stCaptionContainer"] p {
                color: var(--daily-record-secondary-text) !important;
            }

            .st-key-daily_record_page [data-testid="stMetric"] {
                background: #FFFFFF !important;
                border: 1px solid var(--daily-record-border) !important;
            }

            .st-key-food_input_mode [data-testid="stButtonGroup"],
            .st-key-food_photo_source [data-testid="stButtonGroup"] {
                gap: 10px !important;
                padding: 0 !important;
                background: transparent !important;
            }

            .st-key-food_input_mode button[data-testid="stBaseButton-segmented_control"],
            .st-key-food_photo_source button[data-testid="stBaseButton-segmented_control"] {
                min-height: 46px !important;
                padding: 9px 16px !important;
                color: var(--daily-record-secondary-text) !important;
                background: #FFFFFF !important;
                border: 1px solid var(--daily-record-border) !important;
                border-radius: 10px !important;
                box-shadow: none !important;
            }

            .st-key-food_input_mode button[data-testid="stBaseButton-segmented_control"][aria-pressed="true"],
            .st-key-food_input_mode button[data-testid="stBaseButton-segmented_control"][aria-checked="true"],
            .st-key-food_photo_source button[data-testid="stBaseButton-segmented_control"][aria-pressed="true"],
            .st-key-food_photo_source button[data-testid="stBaseButton-segmented_control"][aria-checked="true"] {
                color: var(--daily-record-tab-selected-text) !important;
                background: #FFFFFF !important;
                border-color: #E8CFC3 !important;
                box-shadow: 0 0 0 1px rgba(245, 231, 223, 0.80) !important;
            }

            .st-key-daily_record_page [data-testid="stNumberInput"] div[data-baseweb="input"],
            .st-key-daily_record_page [data-testid="stTextInput"] div[data-baseweb="input"] {
                overflow: hidden !important;
                background: #FFFFFF !important;
                border-color: var(--daily-record-border) !important;
                border-radius: 10px !important;
            }

            .st-key-daily_record_page [data-testid="stNumberInput"] input,
            .st-key-daily_record_page [data-testid="stNumberInput"] button,
            .st-key-daily_record_page [data-testid="stTextInput"] input {
                color: var(--daily-record-primary-text) !important;
                background: transparent !important;
            }

            .st-key-daily_record_page .st-key-training_types [data-testid="stButtonGroup"] {
                gap: 8px !important;
                padding: 0 !important;
                background: transparent !important;
            }

            .st-key-daily_record_page .st-key-training_types button {
                color: var(--daily-record-secondary-text) !important;
                background: #FFFFFF !important;
                border: 1px solid var(--daily-record-border) !important;
                box-shadow: none !important;
            }

            .st-key-daily_record_page div[data-testid="stFormSubmitButton"] button[data-testid^="stBaseButton"],
            .st-key-daily_record_page .st-key-analyze_food_photo button,
            .st-key-daily_record_page .st-key-save_analyzed_food button {
                color: #B88470 !important;
                -webkit-text-fill-color: #B88470 !important;
                background: #F6E8DE !important;
                background-color: #F6E8DE !important;
                background-image: none !important;
                border-color: #EBCFC0 !important;
                box-shadow: none !important;
            }

            .st-key-daily_record_page div[data-testid="stFormSubmitButton"] button[data-testid^="stBaseButton"]:hover,
            .st-key-daily_record_page .st-key-analyze_food_photo button:hover,
            .st-key-daily_record_page .st-key-save_analyzed_food button:hover {
                color: #A86E59 !important;
                -webkit-text-fill-color: #A86E59 !important;
                background: #F2DED2 !important;
                background-color: #F2DED2 !important;
                background-image: none !important;
                border-color: #E2BDAA !important;
            }

            .st-key-daily_record_page div[data-testid="stFormSubmitButton"] button[data-testid^="stBaseButton"]:active,
            .st-key-daily_record_page .st-key-analyze_food_photo button:active,
            .st-key-daily_record_page .st-key-save_analyzed_food button:active {
                background: #EDD4C6 !important;
                background-color: #EDD4C6 !important;
                background-image: none !important;
            }

            .st-key-daily_record_page div[data-testid="stFormSubmitButton"] button[data-testid^="stBaseButton"]:focus-visible,
            .st-key-daily_record_page .st-key-analyze_food_photo button:focus-visible,
            .st-key-daily_record_page .st-key-save_analyzed_food button:focus-visible {
                outline: 2px solid rgba(185, 124, 100, 0.34) !important;
                outline-offset: 2px !important;
            }

            .st-key-daily_record_page div[data-testid="stFormSubmitButton"] button[data-testid^="stBaseButton"]:disabled,
            .st-key-daily_record_page .st-key-analyze_food_photo button:disabled,
            .st-key-daily_record_page .st-key-save_analyzed_food button:disabled {
                color: rgba(184, 132, 112, 0.58) !important;
                -webkit-text-fill-color: rgba(184, 132, 112, 0.58) !important;
                background: rgba(246, 232, 222, 0.62) !important;
                background-color: rgba(246, 232, 222, 0.62) !important;
                background-image: none !important;
                border-color: rgba(235, 207, 192, 0.72) !important;
                opacity: 1 !important;
            }

            .st-key-daily_record_page div[data-testid="stFormSubmitButton"] button[data-testid^="stBaseButton"] [data-testid="stMarkdownContainer"],
            .st-key-daily_record_page div[data-testid="stFormSubmitButton"] button[data-testid^="stBaseButton"] p,
            .st-key-daily_record_page div[data-testid="stFormSubmitButton"] button[data-testid^="stBaseButton"] span {
                color: inherit !important;
                -webkit-text-fill-color: inherit !important;
                background: transparent !important;
                background-color: transparent !important;
            }

            .st-key-daily_record_page button[aria-pressed="true"],
            .st-key-daily_record_page button[aria-checked="true"],
            .st-key-daily_record_page button[data-active="true"] {
                color: var(--daily-record-tab-selected-text) !important;
                background: var(--daily-record-tab-selected) !important;
                border-color: #E8CFC3 !important;
            }

            .st-key-daily_record_page .st-key-cancel_analyzed_food button {
                color: var(--daily-record-secondary-text) !important;
                background: #FFFFFF !important;
                background-color: #FFFFFF !important;
                border-color: var(--daily-record-border) !important;
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
                .st-key-daily_record_page [data-testid="stFileUploader"] {
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

            /* ===== 首頁三張營養卡：桌面滑入、手機按住顯示目標 ===== */
            .st-key-calorie_goal_card,
            .st-key-water_goal_card,
            .st-key-protein_goal_card,
            .st-key-calorie_goal_card > div[data-testid="stVerticalBlock"],
            .st-key-water_goal_card > div[data-testid="stVerticalBlock"],
            .st-key-protein_goal_card > div[data-testid="stVerticalBlock"] {
                position: relative !important;
                min-width: 0 !important;
            }

            .st-key-calorie_goal_card > div[data-testid="stVerticalBlock"],
            .st-key-water_goal_card > div[data-testid="stVerticalBlock"],
            .st-key-protein_goal_card > div[data-testid="stVerticalBlock"] {
                gap: 0 !important;
            }

            .st-key-calorie_goal_card [data-testid="stHtml"]:has(.goal-card-tooltip),
            .st-key-water_goal_card [data-testid="stHtml"]:has(.goal-card-tooltip),
            .st-key-protein_goal_card [data-testid="stHtml"]:has(.goal-card-tooltip) {
                position: absolute !important;
                inset: 0 !important;
                z-index: 12 !important;
                width: 100% !important;
                height: 100% !important;
                pointer-events: none !important;
            }

            .goal-card-tooltip {
                position: absolute !important;
                top: 14px !important;
                left: 50% !important;
                max-width: calc(100% - 20px) !important;
                padding: 8px 12px !important;
                box-sizing: border-box !important;
                overflow: hidden !important;
                color: #FFFFFF !important;
                background: rgba(39, 48, 61, 0.94) !important;
                border: 1px solid rgba(255, 255, 255, 0.24) !important;
                border-radius: 10px !important;
                box-shadow: 0 8px 22px rgba(39, 48, 61, 0.22) !important;
                font-family: "PingFang TC", "Noto Sans TC", "Microsoft JhengHei", system-ui, sans-serif !important;
                font-size: 13px !important;
                font-weight: 600 !important;
                line-height: 1.3 !important;
                text-align: center !important;
                text-overflow: ellipsis !important;
                white-space: nowrap !important;
                opacity: 0 !important;
                transform: translate(-50%, -6px) !important;
                transition: opacity 140ms ease, transform 140ms ease !important;
                pointer-events: none !important;
            }

            @media (hover: hover) and (pointer: fine) {
                .st-key-calorie_goal_card:hover .goal-card-tooltip,
                .st-key-water_goal_card:hover .goal-card-tooltip,
                .st-key-protein_goal_card:hover .goal-card-tooltip {
                    opacity: 1 !important;
                    transform: translate(-50%, 0) !important;
                }
            }

            @media (hover: none) and (pointer: coarse) {
                .st-key-calorie_goal_card,
                .st-key-water_goal_card,
                .st-key-protein_goal_card {
                    -webkit-tap-highlight-color: transparent !important;
                    -webkit-touch-callout: none !important;
                    user-select: none !important;
                }

                .st-key-calorie_goal_card:active .goal-card-tooltip,
                .st-key-water_goal_card:active .goal-card-tooltip,
                .st-key-protein_goal_card:active .goal-card-tooltip {
                    opacity: 1 !important;
                    transform: translate(-50%, 0) !important;
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

            /* ===== 學員歷史：統一的清新健康色票 ===== */
            .stApp:has(.st-key-student_history_page),
            .stApp:has(.st-key-student_history_page) .main,
            .stApp:has(.st-key-student_history_page) [data-testid="stAppViewContainer"],
            .stApp:has(.st-key-student_history_page) [data-testid="stMain"] {
                background: #F7FAF8 !important;
            }

            .st-key-student_history_page {
                --history-primary: #A8D5C2;
                --history-primary-dark: #5A9C84;
                --history-accent: #F4B183;
                --history-accent-dark: #C87943;
                --history-surface: #FFFFFF;
                --history-background: #F7FAF8;
                --history-secondary: #7D8C8A;
                --history-border: #E6EDEB;
            }

            .st-key-student_history_page h1,
            .st-key-student_history_page h2,
            .st-key-student_history_page h3 {
                color: #34423E !important;
            }

            /* ===== 學員歷史：參考健康儀表板的體重圖卡 ===== */
            .st-key-student_weight_history_card {
                box-sizing: border-box !important;
                width: 100% !important;
                padding: 18px 18px 4px !important;
                overflow: hidden !important;
                background: var(--history-surface) !important;
                border: 1px solid var(--history-border) !important;
                border-radius: 20px !important;
                box-shadow: 0 8px 28px rgba(125, 140, 138, 0.08) !important;
            }

            .st-key-student_weight_history_card > div[data-testid="stVerticalBlock"] {
                gap: 4px !important;
            }

            .st-key-student_weight_history_card div[data-testid="stHorizontalBlock"] {
                align-items: center !important;
                flex-wrap: nowrap !important;
                gap: 12px !important;
            }

            .st-key-student_weight_history_card div[data-testid="stColumn"] {
                min-width: 0 !important;
            }

            .st-key-student_weight_history_card div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child {
                box-sizing: border-box !important;
                padding-left: 18px !important;
            }

            .st-key-student_weight_history_card .weight-history-card-heading {
                display: flex !important;
                align-items: baseline !important;
                gap: 9px !important;
                min-width: 0 !important;
                white-space: nowrap !important;
            }

            .st-key-student_weight_history_card .weight-history-card-heading > strong {
                color: #202522 !important;
                font-size: 30px !important;
                font-variant-numeric: tabular-nums !important;
                font-weight: 650 !important;
                line-height: 1 !important;
            }

            .st-key-student_weight_history_card .weight-history-card-heading > strong span {
                font-size: 18px !important;
                font-weight: 550 !important;
            }

            .st-key-student_weight_history_card .weight-history-change {
                color: var(--history-primary-dark) !important;
                font-size: 13px !important;
                font-variant-numeric: tabular-nums !important;
                font-weight: 550 !important;
            }

            .st-key-student_weight_history_card .weight-history-change.is-flat {
                color: var(--history-secondary) !important;
            }

            .st-key-student_weight_history_card [data-testid="stButtonGroup"] {
                justify-content: flex-end !important;
            }

            .st-key-student_weight_history_card [data-testid="stButtonGroup"] button,
            .st-key-student_weight_history_card button[data-testid="stBaseButton-segmented_control"] {
                min-height: 34px !important;
                padding: 5px 12px !important;
                color: var(--history-secondary) !important;
                background: var(--history-background) !important;
                border: none !important;
                border-radius: 10px !important;
                box-shadow: none !important;
                font-size: 12px !important;
            }

            .st-key-student_weight_history_card [data-testid="stButtonGroup"] button[aria-pressed="true"],
            .st-key-student_weight_history_card [data-testid="stButtonGroup"] button[aria-checked="true"] {
                color: #3E7664 !important;
                background: rgba(168, 213, 194, 0.30) !important;
                box-shadow: 0 2px 8px rgba(125, 140, 138, 0.08) !important;
            }

            .st-key-student_weight_history_chart,
            .st-key-student_weight_history_chart div[data-testid="stPlotlyChart"] {
                margin-bottom: 0 !important;
                padding-bottom: 0 !important;
                overflow: hidden !important;
            }

            @media (max-width: 480px) {
                .st-key-student_weight_history_card {
                    padding: 14px 12px 4px !important;
                    border-radius: 18px !important;
                }

                .st-key-student_weight_history_card div[data-testid="stHorizontalBlock"] {
                    gap: 8px !important;
                }

                .st-key-student_weight_history_card div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child {
                    flex: 1 1 auto !important;
                    width: auto !important;
                }

                .st-key-student_weight_history_card div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:last-child {
                    flex: 0 0 122px !important;
                    width: 122px !important;
                }

                .st-key-student_weight_history_card .weight-history-card-heading {
                    gap: 6px !important;
                }

                .st-key-student_weight_history_card .weight-history-card-heading > strong {
                    font-size: 25px !important;
                }

                .st-key-student_weight_history_card .weight-history-card-heading > strong span {
                    font-size: 15px !important;
                }

                .st-key-student_weight_history_card .weight-history-change {
                    font-size: 11px !important;
                }

                .st-key-student_weight_history_card [data-testid="stButtonGroup"] button,
                .st-key-student_weight_history_card button[data-testid="stBaseButton-segmented_control"] {
                    min-height: 32px !important;
                    padding: 4px 9px !important;
                    font-size: 11px !important;
                }

            }

            /* ===== 學員歷史：週／月訓練日曆 ===== */
            .st-key-student_training_history {
                margin-top: 12px !important;
            }

            .st-key-student_training_history_card {
                box-sizing: border-box !important;
                width: 100% !important;
                padding: 16px 18px 26px !important;
                overflow: hidden !important;
                background: var(--history-surface) !important;
                border: 1px solid #ECE6F3 !important;
                border-radius: 20px !important;
                box-shadow: 0 8px 28px rgba(106, 88, 143, 0.08) !important;
            }

            .st-key-student_training_history_card > div[data-testid="stVerticalBlock"] {
                gap: 10px !important;
            }

            .st-key-student_training_history_card [data-testid="stButtonGroup"] {
                width: min(230px, 100%) !important;
                margin: 0 auto 2px !important;
                padding: 3px !important;
                background: #ECE6F3 !important;
                border-radius: 999px !important;
            }

            .st-key-student_training_history_card [data-testid="stButtonGroup"] button,
            .st-key-student_training_history_card button[data-testid="stBaseButton-segmented_control"] {
                min-height: 34px !important;
                color: #746B80 !important;
                background: transparent !important;
                border: none !important;
                border-radius: 999px !important;
                box-shadow: none !important;
                font-size: 13px !important;
                font-weight: 500 !important;
            }

            .st-key-student_training_history_card [data-testid="stButtonGroup"] button[aria-pressed="true"],
            .st-key-student_training_history_card [data-testid="stButtonGroup"] button[aria-checked="true"] {
                color: #574577 !important;
                background: rgba(183, 161, 230, 0.48) !important;
            }

            .st-key-student_training_history_card div[data-testid="stHorizontalBlock"] {
                align-items: center !important;
                flex-wrap: nowrap !important;
                gap: 8px !important;
            }

            .st-key-student_training_history_card div[data-testid="stColumn"] {
                min-width: 0 !important;
            }

            .st-key-student_training_history_card .st-key-training_history_previous button,
            .st-key-student_training_history_card .st-key-training_history_next button {
                width: 36px !important;
                min-width: 36px !important;
                max-width: 36px !important;
                height: 36px !important;
                min-height: 36px !important;
                padding: 0 !important;
                color: #6A558F !important;
                background: rgba(183, 161, 230, 0.20) !important;
                border: none !important;
                border-radius: 50% !important;
                box-shadow: none !important;
            }

            .st-key-student_training_history_card .st-key-training_history_previous button:hover,
            .st-key-student_training_history_card .st-key-training_history_next button:hover {
                background: rgba(183, 161, 230, 0.34) !important;
            }

            .st-key-student_training_history_card .st-key-training_history_previous button:focus-visible,
            .st-key-student_training_history_card .st-key-training_history_next button:focus-visible {
                outline: none !important;
                box-shadow: 0 0 0 3px rgba(183, 161, 230, 0.42) !important;
            }

            .st-key-student_training_history_card .st-key-training_history_previous button:disabled,
            .st-key-student_training_history_card .st-key-training_history_next button:disabled {
                opacity: 0.35 !important;
            }

            .st-key-student_training_history_card .training-calendar-period {
                overflow: hidden !important;
                color: #4E435F !important;
                font-size: 15px !important;
                font-variant-numeric: tabular-nums !important;
                font-weight: 550 !important;
                line-height: 36px !important;
                text-align: center !important;
                text-overflow: ellipsis !important;
                white-space: nowrap !important;
            }

            .st-key-student_training_history_card .training-calendar {
                width: 100% !important;
                padding-top: 2px !important;
                font-family: system-ui, -apple-system, sans-serif !important;
            }

            .st-key-student_training_history_card .training-calendar-weekdays,
            .st-key-student_training_history_card .training-calendar-grid {
                display: grid !important;
                grid-template-columns: repeat(7, minmax(0, 1fr)) !important;
                width: 100% !important;
                column-gap: 8px !important;
            }

            .st-key-student_training_history_card .training-calendar-weekdays {
                margin-bottom: 9px !important;
                color: #7F718F !important;
                font-size: 11px !important;
                font-weight: 500 !important;
                text-align: center !important;
            }

            .st-key-student_training_history_card .training-calendar-grid {
                row-gap: 9px !important;
            }

            .st-key-student_training_history_card .training-calendar-day {
                display: grid !important;
                place-items: center !important;
                justify-self: center !important;
                width: min(42px, 100%) !important;
                aspect-ratio: 1 / 1 !important;
                color: #746B80 !important;
                background: #F5F2F9 !important;
                border-radius: 50% !important;
                font-size: 13px !important;
                font-variant-numeric: tabular-nums !important;
                font-weight: 500 !important;
                line-height: 1 !important;
            }

            .st-key-student_training_history_card .training-calendar-day.is-complete {
                color: #FFFFFF !important;
                background: #B7A1E6 !important;
                box-shadow: 0 4px 12px rgba(183, 161, 230, 0.38) !important;
            }

            .st-key-student_training_history_card .training-calendar-day.is-empty {
                background: transparent !important;
                box-shadow: none !important;
            }

            @media (max-width: 480px) {
                .st-key-student_training_history {
                    margin-top: 10px !important;
                }

                .st-key-student_training_history_card {
                    padding: 14px 10px 24px !important;
                    border-radius: 18px !important;
                }

                .st-key-student_training_history_card [data-testid="stButtonGroup"] {
                    width: min(200px, 100%) !important;
                }

                .st-key-student_training_history_card [data-testid="stButtonGroup"] button,
                .st-key-student_training_history_card button[data-testid="stBaseButton-segmented_control"] {
                    min-height: 32px !important;
                    font-size: 12px !important;
                }

                .st-key-student_training_history_card .training-calendar-period {
                    font-size: 13px !important;
                }

                .st-key-student_training_history_card .training-calendar-weekdays,
                .st-key-student_training_history_card .training-calendar-grid {
                    column-gap: 4px !important;
                }

                .st-key-student_training_history_card .training-calendar-weekdays {
                    margin-bottom: 7px !important;
                    font-size: 10px !important;
                }

                .st-key-student_training_history_card .training-calendar-grid {
                    row-gap: 7px !important;
                }

                .st-key-student_training_history_card .training-calendar-day {
                    width: min(38px, 100%) !important;
                    font-size: 12px !important;
                }
            }

            /* ===== 學員歷史：熱量與蛋白質雙軸趨勢 ===== */
            .st-key-student_nutrition_history {
                margin-top: 12px !important;
            }

            .st-key-student_nutrition_history_card {
                box-sizing: border-box !important;
                width: 100% !important;
                padding: 16px 0 8px !important;
                overflow: hidden !important;
                background: var(--history-surface) !important;
                border: 1px solid var(--history-border) !important;
                border-radius: 20px !important;
                box-shadow: 0 8px 28px rgba(125, 140, 138, 0.08) !important;
            }

            .st-key-student_nutrition_history_card > div[data-testid="stVerticalBlock"] {
                gap: 8px !important;
            }

            .st-key-student_nutrition_history_card [data-testid="stButtonGroup"] {
                width: min(180px, 100%) !important;
                margin-left: auto !important;
                margin-right: 18px !important;
                padding: 3px !important;
                background: var(--history-background) !important;
                border-radius: 12px !important;
            }

            .st-key-student_nutrition_history_card [data-testid="stButtonGroup"] button,
            .st-key-student_nutrition_history_card button[data-testid="stBaseButton-segmented_control"] {
                min-height: 32px !important;
                padding: 4px 10px !important;
                color: var(--history-secondary) !important;
                background: transparent !important;
                border: none !important;
                border-radius: 9px !important;
                box-shadow: none !important;
                font-size: 12px !important;
                font-weight: 500 !important;
            }

            .st-key-student_nutrition_history_card [data-testid="stButtonGroup"] button[aria-pressed="true"],
            .st-key-student_nutrition_history_card [data-testid="stButtonGroup"] button[aria-checked="true"] {
                color: #3E7664 !important;
                background: rgba(168, 213, 194, 0.30) !important;
                box-shadow: 0 2px 8px rgba(125, 140, 138, 0.08) !important;
            }

            .st-key-student_nutrition_history_card .nutrition-history-summary {
                display: grid !important;
                grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
                gap: 4px 14px !important;
                padding: 2px 22px 0 !important;
                font-family: system-ui, -apple-system, sans-serif !important;
            }

            .st-key-student_nutrition_history_card .nutrition-history-summary > div {
                min-width: 0 !important;
            }

            .st-key-student_nutrition_history_card .nutrition-history-summary > div + div {
                padding-left: 14px !important;
                border-left: 1px solid var(--history-border) !important;
            }

            .st-key-student_nutrition_history_card .nutrition-history-summary span,
            .st-key-student_nutrition_history_card .nutrition-history-summary strong,
            .st-key-student_nutrition_history_card .nutrition-history-summary small {
                font-variant-numeric: tabular-nums !important;
            }

            .st-key-student_nutrition_history_card .nutrition-history-summary > div > span {
                display: block !important;
                margin-bottom: 3px !important;
                color: var(--history-secondary) !important;
                font-size: 11px !important;
                font-weight: 500 !important;
            }

            .st-key-student_nutrition_history_card .nutrition-history-summary strong {
                margin-right: 5px !important;
                font-size: 24px !important;
                font-weight: 650 !important;
                line-height: 1 !important;
            }

            .st-key-student_nutrition_history_card .nutrition-history-summary .is-calories strong {
                color: var(--history-primary-dark) !important;
            }

            .st-key-student_nutrition_history_card .nutrition-history-summary .is-protein strong {
                color: var(--history-accent-dark) !important;
            }

            .st-key-student_nutrition_history_card .nutrition-history-summary small {
                color: var(--history-secondary) !important;
                font-size: 10px !important;
            }

            .st-key-student_nutrition_history_card div[data-testid="stAlert"] {
                margin-inline: 18px !important;
            }

            .st-key-student_nutrition_history_chart,
            .st-key-student_nutrition_history_chart div[data-testid="stPlotlyChart"] {
                margin-bottom: 0 !important;
                overflow: hidden !important;
            }

            @media (max-width: 480px) {
                .st-key-student_nutrition_history {
                    margin-top: 10px !important;
                }

                .st-key-student_nutrition_history_card {
                    padding: 14px 0 6px !important;
                    border-radius: 18px !important;
                }

                .st-key-student_nutrition_history_card [data-testid="stButtonGroup"] {
                    width: 150px !important;
                    margin-right: 10px !important;
                }

                .st-key-student_nutrition_history_card .nutrition-history-summary {
                    gap: 4px 8px !important;
                    padding-inline: 12px !important;
                }

                .st-key-student_nutrition_history_card .nutrition-history-summary > div + div {
                    padding-left: 8px !important;
                }

                .st-key-student_nutrition_history_card .nutrition-history-summary strong {
                    font-size: 20px !important;
                }

                .st-key-student_nutrition_history_card div[data-testid="stAlert"] {
                    margin-inline: 10px !important;
                }
            }

            /* ===== 學員歷史：飲水量單軸趨勢 ===== */
            .st-key-student_water_history {
                margin-top: 12px !important;
            }

            .st-key-student_water_history_card {
                box-sizing: border-box !important;
                width: 100% !important;
                padding: 16px 0 8px !important;
                overflow: hidden !important;
                background: #F6F9FC !important;
                border: 1px solid #E6EDF3 !important;
                border-radius: 20px !important;
                box-shadow: 0 8px 28px rgba(126, 143, 163, 0.09) !important;
            }

            .st-key-student_water_history_card > div[data-testid="stVerticalBlock"] {
                gap: 8px !important;
            }

            .st-key-student_water_history_card [data-testid="stButtonGroup"] {
                width: min(180px, 100%) !important;
                margin-left: auto !important;
                margin-right: 18px !important;
                padding: 3px !important;
                background: #FFFFFF !important;
                border-radius: 12px !important;
            }

            .st-key-student_water_history_card [data-testid="stButtonGroup"] button,
            .st-key-student_water_history_card button[data-testid="stBaseButton-segmented_control"] {
                min-height: 32px !important;
                padding: 4px 10px !important;
                color: #7E8FA3 !important;
                background: transparent !important;
                border: none !important;
                border-radius: 9px !important;
                box-shadow: none !important;
                font-size: 12px !important;
                font-weight: 500 !important;
            }

            .st-key-student_water_history_card [data-testid="stButtonGroup"] button[aria-pressed="true"],
            .st-key-student_water_history_card [data-testid="stButtonGroup"] button[aria-checked="true"] {
                color: #5E7FA5 !important;
                background: #E6F0FA !important;
                box-shadow: 0 2px 8px rgba(126, 143, 163, 0.10) !important;
            }

            .st-key-student_water_history_card .water-history-summary {
                padding: 2px 22px 0 !important;
                font-family: system-ui, -apple-system, sans-serif !important;
                font-variant-numeric: tabular-nums !important;
            }

            .st-key-student_water_history_card .water-history-summary > span {
                display: block !important;
                margin-bottom: 3px !important;
                color: #7E8FA3 !important;
                font-size: 11px !important;
                font-weight: 500 !important;
            }

            .st-key-student_water_history_card .water-history-summary strong {
                margin-right: 5px !important;
                color: #5E7FA5 !important;
                font-size: 24px !important;
                font-weight: 650 !important;
                line-height: 1 !important;
            }

            .st-key-student_water_history_card .water-history-summary small {
                color: #7E8FA3 !important;
                font-size: 10px !important;
            }

            .st-key-student_water_history_card div[data-testid="stAlert"] {
                margin-inline: 18px !important;
            }

            .st-key-student_water_history_chart,
            .st-key-student_water_history_chart div[data-testid="stPlotlyChart"] {
                margin-bottom: 0 !important;
                overflow: hidden !important;
            }

            @media (max-width: 480px) {
                .st-key-student_water_history {
                    margin-top: 10px !important;
                }

                .st-key-student_water_history_card {
                    padding: 14px 0 6px !important;
                    border-radius: 18px !important;
                }

                .st-key-student_water_history_card [data-testid="stButtonGroup"] {
                    width: 150px !important;
                    margin-right: 10px !important;
                }

                .st-key-student_water_history_card .water-history-summary {
                    padding-inline: 12px !important;
                }

                .st-key-student_water_history_card .water-history-summary strong {
                    font-size: 20px !important;
                }

                .st-key-student_water_history_card div[data-testid="stAlert"] {
                    margin-inline: 10px !important;
                }
            }

            /* ===== 學員今日完成度：原四卡下方的緊湊摘要 ===== */
            .st-key-daily_completion_card {
                margin-top: -4px !important;
                position: relative !important;
                overflow: visible !important;
                z-index: 5 !important;
            }

            .st-key-daily_completion_card:has(.daily-completion-details[open]) {
                z-index: 40 !important;
            }

            .st-key-daily_completion_card [data-testid="stMarkdownContainer"],
            .st-key-daily_completion_card .daily-completion-details {
                position: relative !important;
                overflow: visible !important;
            }

            .st-key-daily_completion_card .daily-completion-details > summary {
                display: block !important;
                list-style: none !important;
                cursor: pointer !important;
                -webkit-tap-highlight-color: transparent !important;
                user-select: none !important;
            }

            .st-key-daily_completion_card .daily-completion-details > summary::-webkit-details-marker {
                display: none !important;
            }

            .st-key-daily_completion_card .daily-completion-details > summary:focus-visible {
                outline: 3px solid rgba(184, 132, 112, 0.35) !important;
                outline-offset: 3px !important;
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

            .st-key-daily_completion_card .daily-completion-values {
                position: absolute !important;
                right: 12px !important;
                bottom: calc(100% + 12px) !important;
                left: 12px !important;
                z-index: 50 !important;
                box-sizing: border-box !important;
                padding: 14px 16px !important;
                color: #353532 !important;
                background: rgba(250, 250, 250, 0.98) !important;
                border: 1px solid rgba(120, 120, 115, 0.14) !important;
                border-radius: 16px !important;
                box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12) !important;
                font-family: system-ui, -apple-system, sans-serif !important;
            }

            .st-key-daily_completion_card .daily-completion-values::after {
                content: "" !important;
                position: absolute !important;
                right: 30px !important;
                bottom: -7px !important;
                width: 12px !important;
                height: 12px !important;
                background: #fafafa !important;
                border-right: 1px solid rgba(120, 120, 115, 0.14) !important;
                border-bottom: 1px solid rgba(120, 120, 115, 0.14) !important;
                transform: rotate(45deg) !important;
            }

            .daily-completion-values-title {
                margin-bottom: 8px !important;
                color: #777773 !important;
                font-size: 12px !important;
                font-weight: 600 !important;
                letter-spacing: 0.04em !important;
            }

            .daily-completion-value-row {
                display: flex !important;
                align-items: center !important;
                justify-content: space-between !important;
                gap: 16px !important;
                min-height: 28px !important;
                font-size: 14px !important;
            }

            .daily-completion-value-row + .daily-completion-value-row {
                border-top: 1px solid rgba(120, 120, 115, 0.08) !important;
            }

            .daily-completion-value-row strong {
                color: #252525 !important;
                font-size: 15px !important;
                font-variant-numeric: tabular-nums !important;
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
                grid-template-columns: repeat(3, max-content) !important;
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

            .st-key-auth_brand .auth-brand-chinese {
                min-width: 0 !important;
                white-space: nowrap !important;
                font-family: "Noto Sans TC", "PingFang TC", "Microsoft JhengHei", system-ui, sans-serif !important;
                font-size: 1em !important;
                font-weight: inherit !important;
                letter-spacing: 0.04em !important;
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
                    grid-template-columns: repeat(3, max-content) !important;
                    font-size: clamp(14px, 4.4vw, 18px) !important;
                    gap: 0.14em !important;
                }

                .st-key-auth_brand .auth-brand-tagline {
                    max-width: 360px !important;
                    margin-top: 12px !important;
                    padding: 0 6px !important;
                    font-size: 14px !important;
                    line-height: 1.75 !important;
                }
            }

            /* 登入與註冊維持既有亮色設計，不跟隨一般系統深色模式。 */
            .stApp:has(.st-key-auth_brand) {
                color-scheme: light !important;
            }

            .stApp:has(.st-key-auth_brand) div[data-baseweb="input"],
            .stApp:has(.st-key-auth_brand) input {
                background-color: #ffffff !important;
                color: #2F3E46 !important;
                -webkit-text-fill-color: #2F3E46 !important;
            }

            .stApp:has(.st-key-auth_brand) [data-testid="stWidgetLabel"] p,
            .stApp:has(.st-key-auth_brand) input::placeholder {
                color: #2F3E46 !important;
                opacity: 1 !important;
            }

            .stApp:has(.st-key-auth_brand) input:-webkit-autofill {
                -webkit-box-shadow: 0 0 0 1000px #ffffff inset !important;
                -webkit-text-fill-color: #2F3E46 !important;
            }

            /* 登入模式固定於單一視窗，不允許頁面上下捲動。 */
            html:has(.st-key-login_panel),
            body:has(.st-key-login_panel),
            .stApp:has(.st-key-login_panel),
            .stApp:has(.st-key-login_panel) [data-testid="stAppViewContainer"],
            .stApp:has(.st-key-login_panel) [data-testid="stMain"] {
                height: 100% !important;
                max-height: 100dvh !important;
                overflow: hidden !important;
                overscroll-behavior: none !important;
            }

            .main .block-container:has(.st-key-login_panel),
            [data-testid="stMainBlockContainer"]:has(.st-key-login_panel) {
                height: 100dvh !important;
                max-height: 100dvh !important;
                padding-top: 3.75rem !important;
                padding-bottom: 0.75rem !important;
                box-sizing: border-box !important;
                overflow: hidden !important;
            }

            .st-key-login_panel [data-testid="stForm"] {
                margin-top: 20px !important;
                margin-bottom: 20px !important;
            }

            .st-key-login_secondary_action > div[data-testid="stVerticalBlock"] {
                gap: 8px !important;
            }

            @media (max-height: 700px) {
                .main .block-container:has(.st-key-login_panel),
                [data-testid="stMainBlockContainer"]:has(.st-key-login_panel) {
                    padding-top: 3.25rem !important;
                    padding-bottom: 0.5rem !important;
                }

                .st-key-auth_brand .auth-brand-tagline {
                    margin-top: 8px !important;
                    line-height: 1.45 !important;
                }

                .st-key-login_panel [data-testid="stForm"] {
                    margin-top: 12px !important;
                    margin-bottom: 12px !important;
                    padding: 22px !important;
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

            /* 註冊模式專用的緊湊版面；不改動登入與其他頁面的表單。 */
            .stApp:has(.st-key-registration_page) {
                color-scheme: light !important;
            }

            .stApp:has(.st-key-registration_page) div[data-baseweb="input"],
            .stApp:has(.st-key-registration_page) input {
                background-color: #ffffff !important;
                color: #2F3E46 !important;
                -webkit-text-fill-color: #2F3E46 !important;
            }

            .stApp:has(.st-key-registration_page) [data-testid="stWidgetLabel"] p,
            .stApp:has(.st-key-registration_page) input::placeholder {
                color: #2F3E46 !important;
                opacity: 1 !important;
            }

            .stApp:has(.st-key-registration_page) input:-webkit-autofill {
                -webkit-box-shadow: 0 0 0 1000px #ffffff inset !important;
                -webkit-text-fill-color: #2F3E46 !important;
            }

            .main .block-container:has(.st-key-registration_page),
            [data-testid="stMainBlockContainer"]:has(.st-key-registration_page) {
                padding-top: 4.25rem !important;
                padding-bottom: 1.25rem !important;
            }

            .st-key-registration_page {
                width: 100% !important;
                max-width: 820px !important;
                margin: 0 auto !important;
            }

            .st-key-registration_page h3 {
                margin: 0 0 4px !important;
                color: #2F3E46 !important;
            }

            .st-key-registration_page [data-testid="stForm"] {
                max-width: 760px !important;
                margin: 6px auto !important;
                padding: 18px 22px !important;
                border-radius: 24px !important;
            }

            .st-key-registration_page [data-testid="stForm"] [data-testid="stVerticalBlock"] {
                gap: 0.55rem !important;
            }

            .st-key-registration_page [data-testid="stHorizontalBlock"] {
                gap: 1rem !important;
            }

            @media (max-width: 768px) {
                .main .block-container:has(.st-key-registration_page),
                [data-testid="stMainBlockContainer"]:has(.st-key-registration_page) {
                    padding-top: 3.75rem !important;
                    padding-bottom: 1rem !important;
                }

                .st-key-registration_page [data-testid="stForm"] {
                    margin: 4px auto !important;
                    padding: 12px 14px !important;
                    border-radius: 18px !important;
                }
            }



        </style>

        """, unsafe_allow_html=True)
