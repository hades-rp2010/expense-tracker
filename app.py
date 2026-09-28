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

    st.markdown("---")
    st.subheader("🎯 Monthly Category Budgets")
    current_budgets = db.get_monthly_budgets()
    if categories:
        budget_category = st.selectbox("Budget category", options=categories, key="budget_category")
        current_limit = current_budgets.get(budget_category, 0.0)
        with st.form("budget_form", clear_on_submit=False):
            budget_amount = st.number_input(
                "Monthly limit (£)", min_value=0.01, step=0.01, format="%.2f",
                value=max(current_limit, 0.01), key=f"monthly_budget_amount_{budget_category}",
            )
            save_budget = st.form_submit_button("Save Monthly Budget", use_container_width=True)
            if save_budget:
                db.set_monthly_budget(budget_category, budget_amount)
                st.success(f"Monthly budget for {budget_category} saved.")
                st.rerun()

        if current_budgets:
            remove_category = st.selectbox(
                "Remove a budget", options=list(current_budgets),
                format_func=lambda name: f"{name} (£{current_budgets[name]:,.2f}/month)",
                key="remove_budget_category",
            )
            if st.button("Remove Selected Budget", use_container_width=True):
                db.delete_monthly_budget(remove_category)
                st.rerun()

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
    period_days = 7
    start_date = today - timedelta(days=period_days - 1)
elif filter_option == "Past 30 days":
    period_days = 30
    start_date = today - timedelta(days=period_days - 1)
elif filter_option == "Past 3 months":
    period_days = 90
    start_date = today - timedelta(days=period_days - 1)
else:
    period_days = None
    start_date = None

expenses_data = db.get_expenses(start_date=start_date, end_date=today)
df = pd.DataFrame(expenses_data)

if not df.empty:
    df["expense_date"] = pd.to_datetime(df["expense_date"]).dt.date
    df["amount"] = df["amount"].astype(float)

    # Top summary metrics
    total_spent = df["amount"].sum()
    
    # Average the selected period's spend over elapsed days since tracking began,
    # capped at the selected horizon, with a minimum denominator of one.
    anchor_date = date(2026, 9, 15)
    days_since_anchor = max((today - anchor_date).days, 1)
    days_count = min(period_days, days_since_anchor) if period_days else days_since_anchor
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
            orig_dict = edit_df.set_index("id").to_dict(orient="index")
            updates = []
            additions = []
            invalid_rows = []

            def is_blank(value):
                return value is None or pd.isna(value) or (isinstance(value, str) and not value.strip())

            for _, row in edited_df.iterrows():
                if not is_blank(row.get("id")):
                    expense_id = int(row["id"])
                    if expense_id not in orig_dict:
                        continue
                    orig_row = orig_dict[expense_id]
                    changed = (
                        str(row["expense_date"]) != str(orig_row["expense_date"])
                        or str(row["category"]) != str(orig_row["category"])
                        or abs(float(row["amount"]) - float(orig_row["amount"])) > 1e-4
                        or str(row.get("notes") or "") != str(orig_row.get("notes") or "")
                    )
                    if changed:
                        updates.append({"id": expense_id, **row.drop(labels=["id"]).to_dict()})
                    continue

                values = [row.get("expense_date"), row.get("category"), row.get("amount"), row.get("notes")]
                if all(is_blank(value) for value in values):
                    continue
                if is_blank(row.get("expense_date")) or is_blank(row.get("category")) or is_blank(row.get("amount")):
                    invalid_rows.append(str(len(additions) + 1))
                    continue
                try:
                    amount_value = float(row["amount"])
                    if amount_value <= 0 or str(row["category"]) not in all_categories:
                        raise ValueError
                except (TypeError, ValueError):
                    invalid_rows.append(str(len(additions) + 1))
                    continue
                additions.append({
                    "expense_date": row["expense_date"],
                    "category": str(row["category"]),
                    "amount": amount_value,
                    "notes": row.get("notes") or "",
                })

            current_ids = {int(value) for value in edited_df["id"] if not is_blank(value)}
            deletions = sorted(set(orig_dict) - current_ids)

            if invalid_rows:
                st.error("Complete each new row with a valid date, category, and amount greater than £0.00 before saving.")
            elif updates or additions or deletions:
                db.save_expense_changes(updates, additions, deletions)
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

# Monthly spending history by category, independent of the selected dashboard horizon.
st.markdown("---")
st.subheader("📅 Spending Trends")
monthly_data = db.get_expenses(end_date=today)
monthly_df = pd.DataFrame(monthly_data)
if not monthly_df.empty:
    monthly_df["expense_datetime"] = pd.to_datetime(monthly_df["expense_date"])
    monthly_df["month"] = monthly_df["expense_datetime"].dt.to_period("M").dt.to_timestamp()
    trend_categories = sorted(monthly_df["category"].dropna().unique().tolist())
    if "monthly_trend_categories" in st.session_state:
        st.session_state["monthly_trend_categories"] = [
            category for category in st.session_state["monthly_trend_categories"]
            if category in trend_categories
        ]
    else:
        st.session_state["monthly_trend_categories"] = trend_categories

    trend_interval = st.radio(
        "Trend interval",
        options=["Weekly", "Monthly"],
        horizontal=True,
        key="spending_trend_interval",
    )
    if trend_interval == "Weekly":
        monthly_df["period"] = monthly_df["expense_datetime"].dt.to_period("W-SUN").dt.start_time
        period_label = "Week starting"
        tick_format = "%d %b %Y"
        tick_interval = "D7"
    else:
        monthly_df["period"] = monthly_df["month"]
        period_label = "Month"
        tick_format = "%b %Y"
        tick_interval = "M1"

    select_all_col, deselect_all_col, _ = st.columns([1, 1, 4])
    with select_all_col:
        if st.button("Select all", key="select_all_trend_categories"):
            st.session_state["monthly_trend_categories"] = trend_categories
    with deselect_all_col:
        if st.button("Deselect all", key="deselect_all_trend_categories"):
            st.session_state["monthly_trend_categories"] = []

    selected_trend_categories = st.multiselect(
        "Categories included in spending trends",
        options=trend_categories,
        help="Choose which categories contribute to period totals and the category breakdown.",
        key="monthly_trend_categories",
    )
    if selected_trend_categories:
        trend_df = monthly_df[monthly_df["category"].isin(selected_trend_categories)]
        period_totals = (
            trend_df.groupby("period", as_index=False)["amount"].sum()
            .sort_values("period")
        )
        total_fig = px.bar(
            period_totals,
            x="period",
            y="amount",
            labels={"period": period_label, "amount": "Total spend (£)"},
            title=f"Total spending by {trend_interval.lower()}",
        )
        total_fig.update_traces(
            texttemplate="£%{y:,.2f}",
            textposition="outside",
            hovertemplate="%{x|" + tick_format + "}<br>Total: £%{y:,.2f}<extra></extra>",
        )
        total_fig.update_layout(
            showlegend=False,
            xaxis=dict(tickformat=tick_format, dtick=tick_interval),
            yaxis_title="Total spent (£)",
            margin=dict(t=45, b=10, l=10, r=10),
        )
        st.plotly_chart(total_fig, use_container_width=True)

        category_totals = (
            trend_df.groupby(["period", "category"], as_index=False)["amount"].sum()
            .sort_values("period")
        )
        category_fig = px.bar(
            category_totals,
            x="period",
            y="amount",
            color="category",
            barmode="stack",
            labels={"period": period_label, "amount": "Spend (£)", "category": "Category"},
            title=f"Spending by category, {trend_interval.lower()}",
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        category_fig.update_traces(
            hovertemplate="%{x|" + tick_format + "}<br>Spend: £%{y:,.2f}<extra>%{fullData.name}</extra>",
        )
        category_fig.update_layout(
            xaxis=dict(tickformat=tick_format, dtick=tick_interval),
            yaxis_title="Total spent (£)",
            legend_title_text="Category",
            margin=dict(t=45, b=10, l=10, r=10),
        )
        st.plotly_chart(category_fig, use_container_width=True)
    else:
        st.info("Select at least one category to display the monthly trend.")
else:
    st.info("Monthly spending will appear here once you record expenses.")

# Current-month performance against configured category budgets.
st.markdown("---")
st.subheader("🎯 This Month’s Budget")
monthly_budgets = db.get_monthly_budgets()
if monthly_budgets:
    month_start = today.replace(day=1)
    month_expenses = db.get_expenses(start_date=month_start, end_date=today)
    month_spend_df = pd.DataFrame(month_expenses)
    spent_by_category = (
        month_spend_df.groupby("category")["amount"].sum().to_dict()
        if not month_spend_df.empty else {}
    )
    budget_total = sum(monthly_budgets.values())
    budget_spent = sum(float(spent_by_category.get(category, 0.0)) for category in monthly_budgets)
    remaining_total = budget_total - budget_spent
    metric_columns = st.columns(3)
    metric_columns[0].metric("Budgeted", f"£{budget_total:,.2f}")
    metric_columns[1].metric("Spent in Budgeted Categories", f"£{budget_spent:,.2f}")
    metric_columns[2].metric("Remaining", f"£{remaining_total:,.2f}", delta=f"£{remaining_total:,.2f}")

    budget_rows = []
    for category, limit in sorted(monthly_budgets.items()):
        spent = float(spent_by_category.get(category, 0.0))
        remaining = limit - spent
        budget_rows.append({
            "Category": category,
            "Budget (£)": limit,
            "Spent (£)": spent,
            "Remaining (£)": remaining,
            "Used (%)": min(spent / limit, 1.0),
        })
    st.dataframe(
        pd.DataFrame(budget_rows),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Budget (£)": st.column_config.NumberColumn(format="£%.2f"),
            "Spent (£)": st.column_config.NumberColumn(format="£%.2f"),
            "Remaining (£)": st.column_config.NumberColumn(format="£%.2f"),
            "Used (%)": st.column_config.ProgressColumn(
                "Used", min_value=0, max_value=1, format="percent",
            ),
        },
    )
    over_budget = [row["Category"] for row in budget_rows if row["Remaining (£)"] < 0]
    if over_budget:
        st.warning("Over budget: " + ", ".join(over_budget))
else:
    st.info("Set monthly limits by category in the sidebar to track your budget.")
