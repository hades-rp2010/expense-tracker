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
  - Tracking starts on **15/09/2026**. For a selected horizon, divide that horizon's spend by the smaller of its calendar-day length and the elapsed tracking days. Count elapsed days without adding one for the anchor date, with a minimum of one:
    $$\text{Tracking Days} = \max(\text{Today} - 2026\text{-}09\text{-}15, 1)$$
    $$\text{Days} = \min(\text{Horizon Days}, \text{Tracking Days})$$
    $$\text{Daily Average} = \frac{\text{Selected Horizon Spend}}{\text{Days}}$$
  - For **All Time**, use Tracking Days as Days.

---

*Append new rules, architecture decisions, and operational constraints to this file as the project evolves.*
