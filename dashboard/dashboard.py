import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="E-Commerce Data Analysis",
    page_icon="🛒",
    layout="wide"
)

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('main_data.csv')
    # Convert datetime columns
    datetime_columns = ['order_purchase_timestamp', 'order_approved_at', 
                    'order_delivered_carrier_date', 'order_delivered_customer_date',
                    'order_estimated_delivery_date']
    
    for column in datetime_columns:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column])
    return df

# Display loading message
with st.spinner('Loading data...'):
    all_df = load_data()

# Title and introduction
st.title('🛒 E-Commerce Data Analysis Dashboard')
st.markdown("""
This dashboard presents insights from the E-Commerce public dataset analysis, focusing on:
- Sales and revenue trends over time
- Best and worst-performing product categories
- Customer and order metrics
- Payment methods and review scores
""")

# Sidebar for navigation
st.sidebar.title('Navigation')
options = st.sidebar.radio('Select a section:', 
    ['Overview', 'Sales & Revenue Trends', 'Product Category Analysis', 'Customer Analysis', 'Additional Insights'])

# Create monthly aggregation for trend analysis
@st.cache_data
def prepare_monthly_data(df):
    monthly_orders_df = df.groupby(pd.Grouper(key='order_purchase_timestamp', freq='M')).agg({
        "order_id": lambda x: x.nunique(),
        "price": "sum"
    }).reset_index()
    
    monthly_orders_df.columns = ["order_date", "order_count", "revenue"]
    monthly_orders_df['month_name'] = monthly_orders_df['order_date'].dt.strftime('%B %Y')
    return monthly_orders_df

# Create category analysis dataframes
@st.cache_data
def prepare_category_data(df):
    # Top and bottom categories
    top_categories = df.groupby("product_category_name_english")["price"].sum().sort_values(ascending=False).reset_index().head(10)
    bottom_categories = df.groupby("product_category_name_english")["price"].sum().sort_values(ascending=True).reset_index().head(10)
    
    # Category stats
    category_stats = df.groupby("product_category_name_english").agg({
        "order_id": lambda x: x.nunique(),
        "price": ["count", "min", "mean", "max", "sum"]
    })
    category_stats.columns = ["order_count", "item_count", "min_price", "avg_price", "max_price", "total_sales"]
    category_stats = category_stats.sort_values(by="total_sales", ascending=False).reset_index()
    
    return top_categories, bottom_categories, category_stats

# Create RFM analysis
@st.cache_data
def prepare_rfm_data(df):
    rfm_df = df.groupby(by="customer_id", as_index=False).agg({
        "order_purchase_timestamp": "max",  # Last purchase date (Recency)
        "order_id": lambda x: x.nunique(),  # Number of orders (Frequency)
        "price": "sum"  # Total spending (Monetary)
    })
    
    rfm_df.columns = ["customer_id", "last_purchase_date", "frequency", "monetary"]
    
    # Calculate recency in days
    recent_date = df["order_purchase_timestamp"].max()
    rfm_df["recency"] = rfm_df["last_purchase_date"].apply(lambda x: (recent_date - x).days)
    
    rfm_df.drop("last_purchase_date", axis=1, inplace=True)
    return rfm_df

# Create delivery performance analysis
@st.cache_data
def prepare_delivery_data(df):
    orders_delivery_df = df.dropna(subset=['order_delivered_customer_date']).drop_duplicates(subset=['order_id'])
    orders_delivery_df['actual_delivery_time'] = (orders_delivery_df['order_delivered_customer_date'] - 
                                                orders_delivery_df['order_purchase_timestamp']).dt.days
    orders_delivery_df['estimated_delivery_time'] = (orders_delivery_df['order_estimated_delivery_date'] - 
                                                orders_delivery_df['order_purchase_timestamp']).dt.days
    orders_delivery_df['delivery_difference'] = orders_delivery_df['estimated_delivery_time'] - orders_delivery_df['actual_delivery_time']
    
    return orders_delivery_df

# Prepare all the data we need
monthly_data = prepare_monthly_data(all_df)
top_categories, bottom_categories, category_stats = prepare_category_data(all_df)
rfm_data = prepare_rfm_data(all_df)
delivery_data = prepare_delivery_data(all_df)

# Calculate metrics for overview
total_orders = all_df['order_id'].nunique()
total_revenue = all_df['price'].sum()
avg_order_value = total_revenue / total_orders
on_time_delivery_rate = (delivery_data['delivery_difference'] >= 0).mean() * 100

# Payment methods
payment_methods = all_df.groupby("payment_type").agg({
    "order_id": lambda x: x.nunique(),
    "payment_value": "sum"
}).reset_index()

# Review scores
if 'review_score' in all_df.columns:
    review_distribution = all_df['review_score'].value_counts().reset_index()
    review_distribution.columns = ['score', 'count']
    avg_review_score = all_df['review_score'].mean()
else:
    review_distribution = pd.DataFrame({'score': range(1, 6), 'count': [0, 0, 0, 0, 0]})
    avg_review_score = 0

# Customer states
customer_states = all_df.groupby('customer_state')['customer_id'].nunique().reset_index()
customer_states.columns = ['state', 'customer_count']
customer_states = customer_states.sort_values('customer_count', ascending=False)

# Display sections based on selection
if options == 'Overview':
    st.header('📊 Dashboard Overview')
    
    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Orders", f"{total_orders:,}")
    with col2:
        st.metric("Total Revenue", f"R$ {total_revenue:,.2f}")
    with col3:
        st.metric("Avg. Order Value", f"R$ {avg_order_value:.2f}")
    with col4:
        st.metric("On-time Delivery", f"{on_time_delivery_rate:.1f}%")
    
    # Two charts side by side
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("🔝 Top 5 Product Categories")
        fig = px.bar(
            top_categories.head(5),
            x="price",
            y="product_category_name_english",
            orientation='h',
            title="Best Performing Categories",
            labels={"price": "Total Sales (R$)", "product_category_name_english": ""},
            color_discrete_sequence=["#72BCD4"] * 5
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        st.subheader("📊 Payment Methods")
        fig = px.pie(
            payment_methods, 
            values='order_id', 
            names='payment_type',
            title="Orders by Payment Method",
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Review score distribution
    st.subheader("⭐ Customer Review Scores")
    
    fig = px.bar(
        review_distribution.sort_values('score'), 
        x="score", 
        y="count",
        title=f"Distribution of Review Scores (Average: {avg_review_score:.2f}/5)",
        labels={"score": "Review Score (1-5)", "count": "Number of Reviews"},
        color="score",
        color_continuous_scale=px.colors.sequential.Blues
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
elif options == 'Sales & Revenue Trends':
    st.header('📈 Sales & Revenue Trends')
    
    # Time period filter
    st.subheader("Select Time Period")
    date_range = st.date_input(
        "Select date range",
        [monthly_data['order_date'].min().date(), monthly_data['order_date'].max().date()],
        min_value=monthly_data['order_date'].min().date(),
        max_value=monthly_data['order_date'].max().date()
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_monthly_data = monthly_data[
            (monthly_data['order_date'].dt.date >= start_date) & 
            (monthly_data['order_date'].dt.date <= end_date)
        ]
    else:
        filtered_monthly_data = monthly_data
    
    # Order count trend
    st.subheader("Monthly Order Count")
    fig = px.line(
        filtered_monthly_data, 
        x="order_date", 
        y="order_count",
        markers=True,
        title="Number of Orders per Month",
        labels={"order_date": "Month", "order_count": "Order Count"},
        line_shape="linear"
    )
    fig.update_traces(line_color="#72BCD4", line_width=3)
    st.plotly_chart(fig, use_container_width=True)
    
    # Revenue trend
    st.subheader("Monthly Revenue")
    fig = px.line(
        filtered_monthly_data, 
        x="order_date", 
        y="revenue",
        markers=True,
        title="Total Revenue per Month",
        labels={"order_date": "Month", "revenue": "Revenue (R$)"},
        line_shape="linear"
    )
    fig.update_traces(line_color="#72BCD4", line_width=3)
    st.plotly_chart(fig, use_container_width=True)
    
    # Average order value
    filtered_monthly_data['avg_order_value'] = filtered_monthly_data['revenue'] / filtered_monthly_data['order_count']
    
    st.subheader("Average Order Value")
    fig = px.line(
        filtered_monthly_data, 
        x="order_date", 
        y="avg_order_value",
        markers=True,
        title="Average Order Value per Month",
        labels={"order_date": "Month", "avg_order_value": "Avg. Order Value (R$)"},
        line_shape="linear"
    )
    fig.update_traces(line_color="#72BCD4", line_width=3)
    st.plotly_chart(fig, use_container_width=True)
    
elif options == 'Product Category Analysis':
    st.header('🏷️ Product Category Analysis')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top Performing Categories")
        fig = px.bar(
            top_categories.head(10),
            x="price",
            y="product_category_name_english",
            orientation='h',
            title="Best Performing Categories by Total Sales",
            labels={"price": "Total Sales (R$)", "product_category_name_english": ""},
            color="price",
            color_continuous_scale=px.colors.sequential.Blues
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Worst Performing Categories")
        fig = px.bar(
            bottom_categories.head(10),
            x="price",
            y="product_category_name_english",
            orientation='h',
            title="Worst Performing Categories by Total Sales",
            labels={"price": "Total Sales (R$)", "product_category_name_english": ""},
            color="price",
            color_continuous_scale=px.colors.sequential.Blues
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Category details table
    st.subheader("Category Performance Details")
    
    # Format the category stats for better display
    display_category_stats = category_stats.copy()
    display_category_stats['avg_price'] = display_category_stats['avg_price'].round(2)
    display_category_stats['total_sales'] = display_category_stats['total_sales'].round(2)
    
    # Allow filtering by category
    selected_categories = st.multiselect(
        "Select categories to display",
        options=category_stats['product_category_name_english'].unique(),
        default=category_stats['product_category_name_english'].head(5).tolist()
    )
    
    if selected_categories:
        filtered_stats = display_category_stats[display_category_stats['product_category_name_english'].isin(selected_categories)]
    else:
        filtered_stats = display_category_stats
        
    st.dataframe(filtered_stats, use_container_width=True)
    
elif options == 'Customer Analysis':
    st.header('👥 Customer Analysis')
    
    # Customer geographic distribution
    st.subheader("Customer Distribution by State")
    
    # Top 10 states by customer count
    top_states = customer_states.head(10)
    
    fig = px.bar(
        top_states,
        x="state",
        y="customer_count",
        title="Number of Customers by State (Top 10)",
        labels={"state": "State", "customer_count": "Number of Customers"},
        color="customer_count",
        color_continuous_scale=px.colors.sequential.Blues
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # RFM Analysis
    st.subheader("Customer RFM Analysis")
    
    # Display RFM metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Avg. Recency (days)", f"{rfm_data['recency'].mean():.1f}")
        
        # Top 5 customers by recency (lower is better)
        st.subheader("Top Customers by Recency")
        top_recency = rfm_data.sort_values('recency').head(5)
        fig = px.bar(
            top_recency,
            x="customer_id",
            y="recency",
            title="Top 5 Customers by Recency (Lower is Better)",
            labels={"customer_id": "Customer ID", "recency": "Days Since Last Purchase"},
            color_discrete_sequence=["#72BCD4"] * 5
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.metric("Avg. Frequency (orders)", f"{rfm_data['frequency'].mean():.1f}")
        
        # Top 5 customers by frequency
        st.subheader("Top Customers by Frequency")
        top_frequency = rfm_data.sort_values('frequency', ascending=False).head(5)
        fig = px.bar(
            top_frequency,
            x="customer_id",
            y="frequency",
            title="Top 5 Customers by Order Frequency",
            labels={"customer_id": "Customer ID", "frequency": "Number of Orders"},
            color_discrete_sequence=["#72BCD4"] * 5
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        st.metric("Avg. Monetary Value", f"R$ {rfm_data['monetary'].mean():.2f}")
        
        # Top 5 customers by monetary value
        st.subheader("Top Customers by Spending")
        top_monetary = rfm_data.sort_values('monetary', ascending=False).head(5)
        fig = px.bar(
            top_monetary,
            x="customer_id",
            y="monetary",
            title="Top 5 Customers by Total Spending",
            labels={"customer_id": "Customer ID", "monetary": "Total Spending (R$)"},
            color_discrete_sequence=["#72BCD4"] * 5
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # RFM Scatter Plot
    st.subheader("RFM Relationship")
    
    # Allow user to select which dimensions to plot
    x_axis = st.selectbox("Select X-axis", ["recency", "frequency", "monetary"], index=0)
    y_axis = st.selectbox("Select Y-axis", ["recency", "frequency", "monetary"], index=1)
    
    # Create the scatter plot
    fig = px.scatter(
        rfm_data,
        x=x_axis,
        y=y_axis,
        title=f"Relationship between {x_axis.capitalize()} and {y_axis.capitalize()}",
        labels={x_axis: x_axis.capitalize(), y_axis: y_axis.capitalize()},
        color="monetary" if y_axis != "monetary" and x_axis != "monetary" else "frequency",
        size="frequency" if y_axis != "frequency" and x_axis != "frequency" else "monetary",
        hover_data=["customer_id", "recency", "frequency", "monetary"]
    )
    st.plotly_chart(fig, use_container_width=True)
    
elif options == 'Additional Insights':
    st.header('🔍 Additional Insights')
    
    # Delivery performance
    st.subheader("Delivery Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # On-time delivery percentage
        on_time_delivery = (delivery_data['delivery_difference'] >= 0).mean() * 100
        st.metric("On-time Delivery Rate", f"{on_time_delivery:.2f}%")
        
        # Average delivery times
        avg_estimated = delivery_data['estimated_delivery_time'].mean()
        avg_actual = delivery_data['actual_delivery_time'].mean()
        
        delivery_stats = pd.DataFrame({
            'Metric': ['Estimated Delivery Time', 'Actual Delivery Time'],
            'Days': [avg_estimated, avg_actual]
        })
        
        fig = px.bar(
            delivery_stats,
            x="Metric",
            y="Days",
            title="Average Delivery Times",
            color="Metric",
            color_discrete_sequence=["#D3D3D3", "#72BCD4"]
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Delivery difference histogram
        fig = px.histogram(
            delivery_data,
            x="delivery_difference",
            nbins=30,
            title="Delivery Performance (Estimated vs. Actual)",
            labels={"delivery_difference": "Days (Positive = Early, Negative = Late)"},
            color_discrete_sequence=["#72BCD4"]
        )
        
        # Add a vertical line at x=0
        fig.add_vline(x=0, line_width=2, line_dash="dash", line_color="red")
        
        # Add annotation for on-time boundary
        # fig.add_annotation(
        #     x=0,
        #     y=fig.data[0].y.max() * 0.95,
        #     text="On-time boundary",
        #     showarrow=True,
        #     arrowhead=1,
        #     ax=-40,
        #     ay=0
        # )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Payment method analysis
    st.subheader("Payment Method Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Payment method by order count
        fig = px.bar(
            payment_methods.sort_values('order_id', ascending=False),
            x="payment_type",
            y="order_id",
            title="Orders by Payment Method",
            labels={"payment_type": "Payment Type", "order_id": "Number of Orders"},
            color="payment_type",
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Payment method by revenue
        fig = px.bar(
            payment_methods.sort_values('payment_value', ascending=False),
            x="payment_type",
            y="payment_value",
            title="Revenue by Payment Method",
            labels={"payment_type": "Payment Type", "payment_value": "Total Value (R$)"},
            color="payment_type",
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Review score analysis
    if 'review_score' in all_df.columns:
        st.subheader("Customer Review Analysis")
        
        # Score distribution with percentage
        total_reviews = review_distribution['count'].sum()
        review_distribution['percentage'] = (review_distribution['count'] / total_reviews * 100).round(1)
        
        fig = px.bar(
            review_distribution.sort_values('score'),
            x="score",
            y="count",
            title="Distribution of Review Scores",
            labels={"score": "Review Score (1-5)", "count": "Number of Reviews"},
            text="percentage",
            color="score",
            color_continuous_scale=px.colors.sequential.Blues
        )
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("**Created by:** Dias Utsman | **Email:** utsmand91@gmail.com | **ID Dicoding:** dias_utsman")