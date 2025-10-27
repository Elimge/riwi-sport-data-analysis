# app.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from src.db.database import get_engine
from scipy.stats import shapiro

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="RIWI Sport Dashboard")

# --- Data Loading and Processing Functions (Cache for performance) ---
@st.cache_data
def load_data():
    """
    Loads data from the database, performs feature engineering,
    and returns it as a Pandas DataFrame. Cached for better performance.
    """
    main_query = """
    SELECT
        oi.id_order_item,
        o.id_order,
        o.payment_date,
        c.id_customer,
        c.full_name AS customer_name,
        c.email AS customer_email,
        a.city,
        a.department,
        p.id_product,
        p.name AS product_name,
        p.price AS product_price,
        cat.id_category,
        cat.name AS category_name,
        oi.amount AS quantity,
        oi.subtotal
    FROM public.order_item oi
    JOIN public."order" o ON oi.order_id = o.id_order
    JOIN public.customer c ON o.customer_id = c.id_customer
    JOIN public.address a ON c.address_id = a.id_address
    JOIN public.product p ON oi.product_id = p.id_product
    JOIN public.category cat ON p.category_id = cat.id_category
    WHERE o.is_active = true AND c.is_active = true AND p.is_active = true;
    """
    engine = get_engine()
    if engine:
        df = pd.read_sql_query(main_query, engine)
        
        # --- CORRECTION 1: Use 'df' instead of 'df_sales' inside the function ---
        df['payment_date'] = df['payment_date'].dt.tz_localize(None)
        df['year'] = df['payment_date'].dt.year
        df['month'] = df['payment_date'].dt.month
        df['day_of_week'] = df['payment_date'].dt.day_name()
        df['category_name'] = df['category_name'].astype('category')
        return df
    return None

def plot_top_n(data, n, x_col, y_col, title, xlabel, ylabel, ax):
    """
    Reusable function to plot Top N.
    """
    top_data = data.nlargest(n, x_col)
    sns.barplot(
        ax=ax, 
        x=x_col, 
        y=y_col, 
        data=top_data, 
        hue=y_col,
        palette='viridis',
        dodge=False,
        legend=False
    )
    ax.set_title(title, fontsize=14)
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)

# --- Main Data Load ---
df_sales = load_data()

# --- App Rendering ---
if df_sales is not None:
    st.title("📊 RIWI Sport - Sales and Customer Dashboard")
    st.markdown("Interactive dashboard to analyze sales performance and customer behavior.")

    # --- Sidebar Filters ---
    st.sidebar.header("Filters")
    selected_department = st.sidebar.multiselect(
        "Select Department",
        options=df_sales['department'].unique(),
        default=df_sales['department'].unique()
    )
    
    df_filtered = df_sales[df_sales['department'].isin(selected_department)]

    # --- Main KPIs ---
    st.header("General KPIs")
    total_revenue = df_filtered['subtotal'].sum()
    total_orders = df_filtered['id_order'].nunique()
    total_customers = df_filtered['id_customer'].nunique()
    aov = total_revenue / total_orders if total_orders > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"${total_revenue:,.0f}")
    col2.metric("Total Orders", f"{total_orders:,}")
    col3.metric("Average Order Value (AOV)", f"${aov:,.2f}")

    st.markdown("---") # Visual separator

    category_agg_data = df_filtered.groupby(['id_category', 'category_name'], observed=True).agg(
        total_revenue=('subtotal', 'sum'),
        total_quantity=('quantity', 'sum')
    ).reset_index()

    product_agg_data = df_filtered.groupby(['id_product', 'product_name']).agg(
        total_revenue=('subtotal', 'sum'),
        total_quantity=('quantity', 'sum')
    ).reset_index()

    st.header("Visual Performance Analysis")
    fig, axes = plt.subplots(2, 2, figsize=(20, 14))
    plot_top_n(category_agg_data, 5, 'total_revenue', 'category_name', 'Top 5 Categories by Revenue', 'Total Revenue ($)', 'Category', axes[0, 0])
    plot_top_n(category_agg_data, 5, 'total_quantity', 'category_name', 'Top 5 Categories by Quantity', 'Total Quantity Sold', '', axes[0, 1])
    plot_top_n(product_agg_data, 5, 'total_revenue', 'product_name', 'Top 5 Products by Revenue', 'Total Revenue ($)', 'Product', axes[1, 0])
    plot_top_n(product_agg_data, 5, 'total_quantity', 'product_name', 'Top 5 Products by Quantity', 'Total Quantity Sold', '', axes[1, 1])
    st.pyplot(fig)

    st.markdown("---")
    
    st.header("Distribution Analysis")
    fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 7))

    # Histogram of subtotal
    sns.histplot(df_filtered['subtotal'], kde=True, bins=30, ax=ax1)
    ax1.set_title('Order Item Value Distribution')
    ax1.set_xlabel('Subtotal ($)')
    ax1.set_ylabel('Frequency')

    # Boxplot by category
    sns.boxplot(x='category_name', y='subtotal', data=df_filtered, ax=ax2, palette='viridis')
    ax2.set_title('Subtotal Distribution by Category')
    ax2.set_xlabel('Category')
    ax2.set_ylabel('Subtotal ($)')
    ax2.tick_params(axis='x', rotation=45)
    st.pyplot(fig2)

    # Heatmap (requires at least 2 departments to be interesting)
    if len(selected_department) > 1:
        st.header("Geographic and Category Analysis")
        city_category_pivot = df_filtered.pivot_table(index='city', columns='category_name', values='subtotal', aggfunc='sum', fill_value=0)
        fig3, ax3 = plt.subplots(figsize=(16, 10))
        sns.heatmap(city_category_pivot, annot=True, fmt=".0f", cmap='viridis', linewidths=.5, ax=ax3)
        ax3.set_title('Revenue Heatmap by City and Category', fontsize=16)
        st.pyplot(fig3)

else:
    st.error("Data could not be loaded. Please check the database connection.")