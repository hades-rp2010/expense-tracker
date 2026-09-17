# Project Guidelines & Agent Steering (`AGENTS.md`)

This file contains persistent steering instructions, guidelines, and architecture rules for all agents operating in this repository.

---

## 1. Environment & Dependency Management
- **Tooling:** Strictly use **`uv`** for all virtual environments and package management.
  - Add packages via `uv add <package>` (never raw `pip install`).
  - Run all commands through `uv run ...` (e.g. `uv run streamlit run app.py`).
  - Keep `.venv/` isolated and untracked.

## 2. Git & Version Control
- **Sensitive Data:** Never commit transaction data, SQLite databases (`expenses.db`, `*.db`), secret files, or environment files.
- **Commit Standards:** Strictly follow **Linux Foundation commit message standards**:
  - Format: `<subsystem/area>: <Imperative summary under 72 characters>`
  - Separate header and body with a blank line.
  - Body must explain what was changed and why, with lines wrapped cleanly.
  - Use structured bullet points for detailed components.

## 3. UI, Formatting & UX Rules
- **Stack:** Python, Streamlit, Plotly Express, and SQLite.
- **Currency:** GBP (`£`) with 2-decimal precision (`step=0.01` on numeric inputs and table editors).
- **In-Table Editing:**
  - Allow multiple cell edits in `st.data_editor`.
  - Highlight uncommitted/pending modifications in soft orange-red (`#ffc9c9` / `#b71c1c`).
  - Batch commit all table edits when the user clicks `💾 Save Table Changes`.

## 4. Analytics & Calculation Logic
- **Daily Average Anchor Date:**
  - The daily average calculation is strictly anchored to **15/09/2026** across all time horizon tabs:
    $$\text{Days} = \max((\text{Today} - 2026\text{-}09\text{-}15) + 1, 1)$$
    $$\text{Daily Average} = \frac{\text{Total Spent}}{\text{Days}}$$

---

*Append new rules, architecture decisions, and operational constraints to this file as the project evolves.*
