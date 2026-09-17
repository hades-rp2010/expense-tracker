import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime, timedelta
import db

# Initialize database
db.init_db()

st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💷",
    layout="wide",
)

# Styling tweaks
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #e9ecef;
    }
    .stMetric {
        background-color: transparent !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("💷 Expense Tracker")

# Sidebar: Expense Entry & Category Management
with st.sidebar:
    st.header("➕ Log New Expense")
    
    categories = db.get_categories()
    
    with st.form("expense_form", clear_on_submit=True):
        amount = st.number_input("Amount (£)", min_value=0.01, step=0.01, format="%.2f")
        category = st.selectbox("Category", options=categories)
        expense_date = st.date_input("Expense Date", value=date.today())
        notes = st.text_input("Note / Description (Optional)", placeholder="e.g. Sainsbury's lunch")
        
        submitted = st.form_submit_button("Record Expense", use_container_width=True)
        if submitted:
            if amount <= 0:
                st.error("Amount must be greater than 0.")
            else:
                db.add_expense(amount, category, expense_date, notes)
                st.success(f"Recorded £{amount:.2f} for {category}!")
                st.rerun()

    st.markdown("---")
    st.subheader("🏷️ Manage Categories")
    with st.form("category_form", clear_on_submit=True):
        new_cat = st.text_input("New Category Name")
        add_cat_btn = st.form_submit_button("Add Category", use_container_width=True)
        if add_cat_btn:
            if new_cat and db.add_category(new_cat):
                st.success(f"Category '{new_cat.strip()}' added!")
                st.rerun()
            elif new_cat:
                st.warning("Category already exists or is invalid.")

# Main Dashboard
today = date.today()

# Time Period Selection
st.subheader("📊 Analytics Overview")
filter_option = st.radio(
    "Filter by Time Horizon:",
    options=["Past 7 days", "Past 30 days", "Past 3 months", "All Time"],
    horizontal=True,
    index=1,
)

if filter_option == "Past 7 days":
    start_date = today - timedelta(days=7)
elif filter_option == "Past 30 days":
    start_date = today - timedelta(days=30)
elif filter_option == "Past 3 months":
    start_date = today - timedelta(days=90)
else:
    start_date = None

expenses_data = db.get_expenses(start_date=start_date, end_date=today)
df = pd.DataFrame(expenses_data)

if not df.empty:
    df["expense_date"] = pd.to_datetime(df["expense_date"]).dt.date
    df["amount"] = df["amount"].astype(float)

    # Top summary metrics
    total_spent = df["amount"].sum()
    
    # Anchor date is strictly 15/09/2026 for all tabs
    anchor_date = date(2026, 9, 15)
    days_count = max((today - anchor_date).days + 1, 1)
    daily_avg = total_spent / days_count

    cat_totals = df.groupby("category")["amount"].sum().reset_index()
    top_category_row = cat_totals.sort_values(by="amount", ascending=False).iloc[0]
    top_cat = top_category_row["category"]
    top_cat_amt = top_category_row["amount"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Spent", f"£{total_spent:,.2f}")
    c2.metric("Daily Average", f"£{daily_avg:,.2f}")
    c3.metric("Top Spend Category", f"{top_cat} (£{top_cat_amt:,.2f})")

    st.markdown("---")

    # Analytics Charts
    col_pie, col_bar = st.columns(2)

    with col_pie:
        st.subheader("Category Distribution")
        fig_pie = px.pie(
            cat_totals,
            names="category",
            values="amount",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        fig_pie.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>Spent: £%{value:,.2f}<br>Percentage: %{percent}<extra></extra>",
        )
        fig_pie.update_layout(
            margin=dict(t=30, b=10, l=10, r=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_bar:
        st.subheader("Spend by Category")
        cat_sorted = cat_totals.sort_values(by="amount", ascending=True)
        fig_bar = px.bar(
            cat_sorted,
            x="amount",
            y="category",
            orientation="h",
            text="amount",
            labels={"amount": "Total (£)", "category": "Category"},
            color="amount",
            color_continuous_scale="Blues",
        )
        fig_bar.update_traces(
            texttemplate="£%{text:,.2f}",
            textposition="outside",
            hovertemplate="<b>%{y}</b>: £%{x:,.2f}<extra></extra>",
        )
        fig_bar.update_layout(
            margin=dict(t=30, b=10, l=10, r=10),
            coloraxis_showscale=False,
            xaxis=dict(showgrid=True),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # Detailed Expense Records & In-Table Editing
    st.subheader("📋 Expense Entries (Editable)")
    st.caption("💡 Edit as many cells as you like directly in the table. Uncommitted edits will be highlighted in orange/red. Click **'💾 Save Table Changes'** to commit all edits at once.")

    edit_df = df[["id", "expense_date", "category", "amount", "notes"]].copy()
    all_categories = db.get_categories()

    # Inspect current session state for uncommitted changes in this editor to highlight them
    editor_state = st.session_state.get("expenses_editor", {})
    edited_rows = editor_state.get("edited_rows", {}) if isinstance(editor_state, dict) else {}

    def highlight_uncommitted(data):
        styles = pd.DataFrame("", index=data.index, columns=data.columns)
        for row_idx, changed_cols in edited_rows.items():
            try:
                row_loc = int(row_idx)
                if row_loc in styles.index:
                    for col_name in changed_cols.keys():
                        if col_name in styles.columns:
                            # Highlight uncommitted cells in distinctive soft orange-red
                            styles.loc[row_loc, col_name] = "background-color: #ffc9c9; color: #b71c1c; font-weight: bold;"
            except Exception:
                continue
        return styles

    styled_edit_df = edit_df.style.apply(highlight_uncommitted, axis=None)

    edited_df = st.data_editor(
        styled_edit_df,
        key="expenses_editor",
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "id": st.column_config.NumberColumn(
                "ID",
                disabled=True,
                help="Unique expense ID (cannot be modified)",
                width="small",
            ),
            "expense_date": st.column_config.DateColumn(
                "Date",
                format="YYYY-MM-DD",
                required=True,
            ),
            "category": st.column_config.SelectboxColumn(
                "Category",
                options=all_categories,
                required=True,
            ),
            "amount": st.column_config.NumberColumn(
                "Amount (£)",
                format="£%.2f",
                min_value=0.01,
                step=0.01,
                required=True,
            ),
            "notes": st.column_config.TextColumn(
                "Notes",
                width="large",
            ),
        },
    )

    col_save, col_del = st.columns([1, 1])

    with col_save:
        if st.button("💾 Save Table Changes", type="primary", use_container_width=True):
            changes_detected = False
            # Check for edits via st.session_state['expenses_editor'] as well as direct DataFrame diff
            editor_changes = st.session_state.get("expenses_editor", {})
            edited_rows_dict = editor_changes.get("edited_rows", {}) if isinstance(editor_changes, dict) else {}
            deleted_rows_list = editor_changes.get("deleted_rows", []) if isinstance(editor_changes, dict) else {}

            # Process all edited rows
            orig_dict = edit_df.set_index("id").to_dict(orient="index")
            current_dict = edited_df.dropna(subset=["id"]).set_index("id").to_dict(orient="index")

            for exp_id, row in current_dict.items():
                if exp_id in orig_dict:
                    orig_row = orig_dict[exp_id]
                    # Check any differences across all fields
                    date_changed = str(row["expense_date"]) != str(orig_row["expense_date"])
                    cat_changed = str(row["category"]) != str(orig_row["category"])
                    amt_changed = abs(float(row["amount"]) - float(orig_row["amount"])) > 1e-4
                    note_changed = str(row.get("notes") or "") != str(orig_row.get("notes") or "")

                    if date_changed or cat_changed or amt_changed or note_changed:
                        db.update_expense(
                            expense_id=int(exp_id),
                            amount=float(row["amount"]),
                            category=str(row["category"]),
                            expense_date=row["expense_date"],
                            notes=str(row.get("notes") or ""),
                        )
                        changes_detected = True

            # Process deleted rows from keyboard shortcuts / row removals
            deleted_ids = set(orig_dict.keys()) - set(current_dict.keys())
            for d_id in deleted_ids:
                db.delete_expense(int(d_id))
                changes_detected = True

            if changes_detected:
                # Clear editor state to reset cell highlighting
                if "expenses_editor" in st.session_state:
                    del st.session_state["expenses_editor"]
                st.success("✅ All changes saved successfully!")
                st.rerun()
            else:
                st.info("No modifications detected to save.")

    with col_del:
        with st.popover("🗑️ Delete an Entry"):
            entry_to_delete = st.selectbox(
                "Select entry to delete:",
                options=df["id"].tolist(),
                format_func=lambda x: f"ID #{x}: {df.loc[df['id'] == x, 'expense_date'].values[0]} - {df.loc[df['id'] == x, 'category'].values[0]} - £{df.loc[df['id'] == x, 'amount'].values[0]:.2f}",
            )
            if st.button("Confirm Delete", type="secondary", use_container_width=True):
                db.delete_expense(entry_to_delete)
                st.success(f"Entry #{entry_to_delete} deleted!")
                st.rerun()

else:
    st.info("💡 No expenses found for the selected time window. Add some using the left sidebar to see charts and analytics!")
