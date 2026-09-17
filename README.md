# Expense Tracker

A lightweight, single-page expense tracker with analytics, built with **Python**, **Streamlit**, **Plotly**, and **SQLite**.

## Features
- **Expense Logging:** Input amount (£ GBP), category, date, and optional note.
- **Custom Categories:** Choose from predefined categories or dynamically add your own.
- **Analytics & Visualizations:**
  - Dynamic time horizon filtering: **Past 7 days**, **Past 30 days**, **Past 3 months**, and **All Time**.
  - **Pie / Donut Chart:** Interactive breakdown of expenses across categories.
  - **Bar Graph:** Total spending by category.
  - **KPI Metrics:** Total spend, daily average, top category.
- **Local Persistence:** Uses SQLite (`expenses.db`), stored locally with zero configuration required.
- **Record Management:** View full tabular breakdown and delete entries.

## How to Run

1. Navigate to the project directory:
```bash
cd /Users/rishabhpatra/workplace/expense-tracker
```

2. Run the Streamlit application using `uv`:
```bash
uv run streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.
