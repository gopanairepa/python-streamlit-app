import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Mock data generation (cached so it stays stable across reruns)
# ---------------------------------------------------------------------------

@st.cache_data
def generate_data():
    np.random.seed(42)
    n_rows = 2000
    start = datetime(2025, 1, 1)
    dates = [start + timedelta(days=int(d)) for d in np.random.randint(0, 365, n_rows)]

    regions = np.random.choice(["North", "South", "East", "West"], n_rows, p=[0.3, 0.25, 0.25, 0.2])
    categories = np.random.choice(["Electronics", "Clothing", "Home & Garden", "Sports", "Books"], n_rows)
    reps = np.random.choice(
        ["Alice", "Bob", "Carol", "David", "Eva", "Frank", "Grace", "Hank"], n_rows
    )

    base_price = {
        "Electronics": 350, "Clothing": 75, "Home & Garden": 120, "Sports": 95, "Books": 25,
    }
    revenue = np.array([base_price[c] for c in categories]) * (1 + np.random.normal(0, 0.3, n_rows))
    revenue = np.clip(revenue, 5, None).round(2)
    units = np.random.randint(1, 20, n_rows)

    df = pd.DataFrame({
        "date": dates,
        "region": regions,
        "category": categories,
        "sales_rep": reps,
        "revenue": revenue,
        "units_sold": units,
    })
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


df = generate_data()

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------

st.sidebar.header("Filters")

date_range = st.sidebar.date_input(
    "Date range",
    value=(df["date"].min().date(), df["date"].max().date()),
    min_value=df["date"].min().date(),
    max_value=df["date"].max().date(),
)

selected_regions = st.sidebar.multiselect("Region", df["region"].unique(), default=df["region"].unique())
selected_categories = st.sidebar.multiselect("Category", df["category"].unique(), default=df["category"].unique())

# Apply filters
mask = (
    (df["date"].dt.date >= date_range[0])
    & (df["date"].dt.date <= date_range[1])
    & (df["region"].isin(selected_regions))
    & (df["category"].isin(selected_categories))
)
filtered = df[mask]

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("Sales Analytics Dashboard")
st.markdown("Interactive overview of 2025 sales performance — powered by mock data.")

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------

total_revenue = filtered["revenue"].sum()
total_units = filtered["units_sold"].sum()
avg_order = filtered["revenue"].mean() if len(filtered) else 0
n_orders = len(filtered)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Revenue", f"${total_revenue:,.0f}")
c2.metric("Units Sold", f"{total_units:,}")
c3.metric("Avg Order Value", f"${avg_order:,.2f}")
c4.metric("Total Orders", f"{n_orders:,}")

# ---------------------------------------------------------------------------
# Charts row 1: Revenue over time + Revenue by region
# ---------------------------------------------------------------------------

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Monthly Revenue Trend")
    monthly = (
        filtered.set_index("date")
        .resample("ME")["revenue"]
        .sum()
        .reset_index()
    )
    monthly.columns = ["month", "revenue"]
    fig_trend = px.area(monthly, x="month", y="revenue", color_discrete_sequence=["#636EFA"])
    fig_trend.update_layout(xaxis_title="", yaxis_title="Revenue ($)", margin=dict(t=10))
    st.plotly_chart(fig_trend, use_container_width=True)

with col_right:
    st.subheader("Revenue by Region")
    region_rev = filtered.groupby("region")["revenue"].sum().reset_index()
    fig_region = px.pie(region_rev, values="revenue", names="region", hole=0.4)
    fig_region.update_layout(margin=dict(t=10))
    st.plotly_chart(fig_region, use_container_width=True)

# ---------------------------------------------------------------------------
# Charts row 2: Category breakdown + Top reps
# ---------------------------------------------------------------------------

col_left2, col_right2 = st.columns(2)

with col_left2:
    st.subheader("Revenue by Category")
    cat_rev = filtered.groupby("category")["revenue"].sum().sort_values(ascending=True).reset_index()
    fig_cat = px.bar(cat_rev, x="revenue", y="category", orientation="h", color="category")
    fig_cat.update_layout(showlegend=False, margin=dict(t=10), xaxis_title="Revenue ($)", yaxis_title="")
    st.plotly_chart(fig_cat, use_container_width=True)

with col_right2:
    st.subheader("Top Sales Reps")
    rep_rev = (
        filtered.groupby("sales_rep")
        .agg(total_revenue=("revenue", "sum"), orders=("revenue", "count"))
        .sort_values("total_revenue", ascending=False)
        .head(8)
        .reset_index()
    )
    fig_rep = px.bar(
        rep_rev, x="total_revenue", y="sales_rep", orientation="h",
        color="total_revenue", color_continuous_scale="Blues",
    )
    fig_rep.update_layout(
        showlegend=False, margin=dict(t=10),
        xaxis_title="Revenue ($)", yaxis_title="", coloraxis_showscale=False,
    )
    st.plotly_chart(fig_rep, use_container_width=True)

# ---------------------------------------------------------------------------
# Scatter: Revenue vs Units
# ---------------------------------------------------------------------------

st.subheader("Revenue vs. Units Sold (per order)")
fig_scatter = px.scatter(
    filtered, x="units_sold", y="revenue", color="category",
    hover_data=["sales_rep", "region", "date"],
    opacity=0.6,
)
fig_scatter.update_layout(
    xaxis_title="Units Sold", yaxis_title="Revenue ($)", margin=dict(t=10),
)
st.plotly_chart(fig_scatter, use_container_width=True)

# ---------------------------------------------------------------------------
# Raw data explorer
# ---------------------------------------------------------------------------

with st.expander("View Raw Data"):
    st.dataframe(
        filtered.style.format({"revenue": "${:,.2f}"}),
        use_container_width=True,
        height=400,
    )
    st.download_button(
        "Download CSV",
        filtered.to_csv(index=False),
        file_name="sales_data.csv",
        mime="text/csv",
    )
