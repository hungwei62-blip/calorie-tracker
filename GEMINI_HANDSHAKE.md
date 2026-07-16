# 🍽️ Calorie Tracker - Project Handshake for Gemini

## Project Overview
- **Path**: `D:\projects\Calories`
- **Tech Stack**: Streamlit + Google Sheets (gspread) + Firebase Storage + Gemini 2.5 Flash
- **Roles**: Coach / Student management system
- **Live**: [https://worldgymzoe-caloriesoe.streamlit.app/](https://worldgymzoe-caloriesoe.streamlit.app/)
- **Repo**: [hungwei62-blip/calorie-tracker](https://github.com/hungwei62-blip/calorie-tracker)
- **Python**: 3.14 (Streamlit Cloud)

## Current Status

### ✅ Completed Features
1. **Coach Features**
   - Student overview dashboard (`page_coach_overview()`)
   - Student history page with charts (weight trend, diet pie, intake trends, training table)
   - Coach notes (Notes sheet: create/read/update/delete)
   - Export: CSV (UTF-8 BOM) + PDF (matplotlib, 5-page A4)
   - Modify student goals

2. **Student Features**
   - Daily diet record (protein/carbs/fat/calories/water)
   - AI food analysis via Gemini (text + image)
   - TDEE calculation page
   - Weight tracking
   - Training log (back/chest/legs/core/cardio)

3. **Performance**
   - `@st.cache_data(ttl=60)` on read functions
   - Cache clearing on writes to avoid Sheets API 429

### 🔴 Open Issues

| Issue | Description |
|-------|-------------|
| PDF Chinese Font | matplotlib cannot render Chinese on Streamlit Cloud (missing fonts) |
| Excel Import | `calories` field may not be read correctly |
| Coach Notes | No confirmation dialog for delete |

### 📋 Pending Tasks

| Priority | Task | Description |
|----------|------|-------------|
| High | T1-5 | Coach add new student feature |
| Medium | T3-4 | Coach view student details page |
| Low | - | Excel export (needs openpyxl) |
| Low | T5-1 | Unit tests |

## Project Structure

```
Calories/
├── app.py                      # Main Streamlit app
├── services/
│   ├── sheets.py               # Google Sheets operations
│   ├── gemini.py               # Gemini AI integration
│   ├── firebase.py             # Firebase Storage
│   └── auth.py                 # Authentication
├── requirements.txt            # Dependencies
├── .streamlit/
│   └── secrets.toml            # API keys (NOT committed)
└── docs/                       # Setup documentation
```

## Google Sheets Structure

| Sheet | Purpose |
|-------|---------|
| Users | Coach & student accounts (email, name, role, coach_id) |
| Goals | Student nutrition targets (protein/carbs/fat/calories/water) |
| Records | Daily diet records |
| Weight | Weight history |
| Training | Training logs (back/chest/legs/core/cardio) |
| Notes | Coach observations with timestamps |

## Local Testing

```powershell
cd D:\projects\Calories
streamlit run app.py
```

Access at: [http://localhost:8501](http://localhost:8501)

## Known Constraints

1. **Sheets API 429**: Rate limit - use 60s cache TTL
2. **PDF Chinese**: Need font configuration for matplotlib
3. **Git in Codex**: Cannot use `git add/commit` in Codex shell; use local terminal

---

*Created: 2026-07-16*
