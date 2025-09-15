import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
from datetime import datetime, timedelta


# Page configuration
st.set_page_config(
    page_title="SendGrid Analytics Dashboard",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === 1 GB upload/message limits ===
st.set_option("server.maxUploadSize", 1024)   # MB → 1 GB
st.set_option("server.maxMessageSize", 1024)  # bump message size too

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1f77b4;
    }
    
    .filter-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    .success-rate { color: #28a745; }
    .warning-rate { color: #ffc107; }
    .danger-rate { color: #dc3545; }
    
    .download-section {
        background: #e8f5e8;
        padding: 1rem;
        border-radius: 8px;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Main title
st.markdown('<h1 class="main-header">📧 SendGrid Email Analytics Dashboard</h1>', unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.header("🔧 Configuration")
    
    # File upload section
    st.subheader("📁 Data Upload")
    uploaded_file = st.file_uploader(
        "Upload SendGrid Events CSV",
        type="csv",
        help="Upload your SendGrid events CSV file to start analyzing email performance"
    )
    
    # Enforce 1 GB limit client-side for nicer UX (Streamlit still enforces server options)
    MAX_MB = 1024
    if uploaded_file is not None:
        size_bytes = getattr(uploaded_file, "size", 0)
        if size_bytes and size_bytes > MAX_MB * 1024 * 1024:
            st.error(f"❌ File too large: {(size_bytes/1024/1024):.1f} MB. Limit is {MAX_MB} MB.")
            st.stop()
        st.success("✅ File uploaded successfully!")

def to_excel(df_):
    """Convert DataFrame to Excel format for download"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_.to_excel(writer, index=False, sheet_name='Email_Rates')
        workbook = writer.book
        worksheet = writer.sheets['Email_Rates']
        
        # Add formatting
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        for col_num, value in enumerate(df_.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
    return output.getvalue()

def create_rate_chart(processed, delivered, opened, bounced, title="Email Performance"):
    """Create an interactive donut chart for email rates"""
    fig = go.Figure(data=[go.Pie(
        labels=['Delivered', 'Opened', 'Bounced', 'Not Delivered'],
        values=[delivered, opened, bounced, processed - delivered - bounced],
        hole=.3,
        marker_colors=['#28a745', '#17a2b8', '#dc3545', '#6c757d']
    )])
    
    fig.update_layout(
        title=title,
        showlegend=True,
        height=400,
        font=dict(size=12)
    )
    
    return fig

def display_metric_cards(processed, delivered, opened, bounced):
    """Display metrics in an organized card layout"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📤 Emails Sent",
            value=f"{processed:,}",
            help="Total number of emails processed by SendGrid"
        )
    
    with col2:
        delivery_rate = (delivered / processed * 100) if processed else 0
        color = "normal" if delivery_rate >= 95 else "inverse"
        st.metric(
            label="✅ Delivered",
            value=f"{delivered:,}",
            delta=f"{delivery_rate:.1f}%",
            delta_color=color,
            help="Emails successfully delivered to recipients"
        )
    
    with col3:
        open_rate = (opened / delivered * 100) if delivered else 0
        color = "normal" if open_rate >= 20 else "inverse"
        st.metric(
            label="👁️ Opened",
            value=f"{opened:,}",
            delta=f"{open_rate:.1f}%",
            delta_color=color,
            help="Emails opened by recipients"
        )
    
    with col4:
        bounce_rate = (bounced / processed * 100) if processed else 0
        color = "inverse" if bounce_rate <= 5 else "normal"
        st.metric(
            label="❌ Bounced",
            value=f"{bounced:,}",
            delta=f"{bounce_rate:.1f}%",
            delta_color=color,
            help="Emails that bounced and were not delivered"
        )

# Main application logic
if uploaded_file is not None:
    # Load and process data
    with st.spinner("🔄 Processing your data..."):
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip()

        # Data validation
        required_columns = ["event", "message_id", "processed"]
        if not all(col in df.columns for col in required_columns):
            st.error(f"❌ Missing required columns: {required_columns}")
            st.stop()

        # Keep only relevant events
        valid_events = ["processed", "delivered", "open", "bounce"]
        df = df[df["event"].isin(valid_events)]

        # Process datetime
        df["processed_datetime"] = pd.to_datetime(df["processed"], errors='coerce')
        df = df.dropna(subset=["processed_datetime"])
        df["processed_date"] = df["processed_datetime"].dt.date

        # Find processed message IDs
        processed_ids = set(df.loc[df["event"] == "processed", "message_id"].unique())
        df = df[df["message_id"].isin(processed_ids)]

        # Remove duplicates
        df["unique_event"] = df["message_id"].astype(str) + "_" + df["event"] + "_" + df["processed_date"].astype(str)
        df = df.drop_duplicates(subset=["unique_event"])

        # Get subjects
        processed_df = df[df["event"] == "processed"][["message_id", "subject"]].drop_duplicates(subset=["message_id"])
        df = df.merge(processed_df, on="message_id", how="left", suffixes=('', '_processed'))
        df["subject"] = df["subject_processed"]

    # Sidebar filters
    with st.sidebar:
        st.subheader("🎯 Filters")
        
        # Date range filter
        min_date = df["processed_date"].min()
        max_date = df["processed_date"].max()
        
        date_range = st.date_input(
            "📅 Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            help="Select the date range for analysis"
        )
        
        # Subject filter
        unique_subjects = sorted(df["subject"].dropna().unique())
        if len(unique_subjects) > 1:
            selected_subjects = st.multiselect(
                "📧 Email Subjects",
                options=unique_subjects,
                default=unique_subjects,
                help="Filter by specific email subjects"
            )
        else:
            selected_subjects = unique_subjects
            
        # Email exclusion filter
        unique_emails = sorted(df["email"].dropna().unique()) if "email" in df.columns else []
        excluded_emails = []
        
        if unique_emails:
            with st.expander("🚫 Exclude Specific Emails"):
                excluded_emails = st.multiselect(
                    "Select emails to exclude from analysis",
                    options=unique_emails,
                    help="Exclude specific email addresses from the analysis"
                )

    # Apply filters
    df_filtered = df.copy()
    
    # Date filter
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        mask = (df_filtered["processed_date"] >= start_date) & (df_filtered["processed_date"] <= end_date)
        df_filtered = df_filtered[mask]
    
    # Subject filter
    df_filtered = df_filtered[df_filtered["subject"].isin(selected_subjects)]
    
    # Email exclusion filter
    if excluded_emails:
        df_filtered = df_filtered[~df_filtered["email"].isin(excluded_emails)]

    # Main dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Daily Trends", "🔍 Date Drilldown", "📥 Downloads"])

    # Tab 1: Overview
    with tab1:
        st.header("📊 Email Performance Overview")
        
        # Calculate overall metrics
        processed_set = set(df_filtered[df_filtered["event"] == "processed"]["message_id"].unique())
        delivered_set = set(df_filtered[df_filtered["event"] == "delivered"]["message_id"].unique())
        open_set = set(df_filtered[df_filtered["event"] == "open"]["message_id"].unique())
        bounce_set = set(df_filtered[df_filtered["event"] == "bounce"]["message_id"].unique())

        total_processed = len(processed_set)
        total_delivered = len(delivered_set.intersection(processed_set))
        total_open = len(open_set.intersection(delivered_set))
        total_bounce = len(bounce_set.intersection(processed_set))

        if total_processed > 0:
            # Display metric cards
            display_metric_cards(total_processed, total_delivered, total_open, total_bounce)
            
            st.markdown("---")
            
            # Performance visualization
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Donut chart
                fig_donut = create_rate_chart(
                    total_processed, total_delivered, total_open, total_bounce,
                    "Email Performance Distribution"
                )
                st.plotly_chart(fig_donut, use_container_width=True)
            
            with col2:
                # Performance rates
                delivery_rate = (total_delivered / total_processed * 100) if total_processed else 0
                open_rate = (total_open / total_delivered * 100) if total_delivered else 0
                bounce_rate = (total_bounce / total_processed * 100) if total_processed else 0
                
                st.subheader("📋 Performance Rates")
                
                # Create gauge-like metrics
                rate_data = {
                    "Metric": ["Delivery Rate", "Open Rate", "Bounce Rate"],
                    "Rate (%)": [delivery_rate, open_rate, bounce_rate],
                    "Status": [
                        "🟢 Excellent" if delivery_rate >= 95 else "🟡 Good" if delivery_rate >= 90 else "🔴 Needs Improvement",
                        "🟢 Excellent" if open_rate >= 25 else "🟡 Good" if open_rate >= 15 else "🔴 Needs Improvement",
                        "🟢 Excellent" if bounce_rate <= 2 else "🟡 Acceptable" if bounce_rate <= 5 else "🔴 High"
                    ]
                }
                
                st.dataframe(
                    pd.DataFrame(rate_data),
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.warning("⚠️ No data available for the selected filters.")

    # Tab 2: Daily Trends
    with tab2:
        st.header("📈 Daily Email Performance Trends")
        
        if total_processed > 0:
            # Create daily pivot
            pivot = df_filtered.pivot_table(
                index="processed_date",
                columns="event",
                values="message_id",
                aggfunc=lambda x: x.nunique(),
                fill_value=0
            ).reset_index().sort_values("processed_date")

            # Ensure all columns exist
            for col in ["processed", "delivered", "open", "bounce"]:
                if col not in pivot.columns:
                    pivot[col] = 0

            # Calculate rates
            pivot["Delivery Rate (%)"] = pivot.apply(
                lambda row: (row["delivered"] / row["processed"] * 100) if row["processed"] else 0, axis=1
            )
            pivot["Open Rate (%)"] = pivot.apply(
                lambda row: (row["open"] / row["delivered"] * 100) if row["delivered"] else 0, axis=1
            )
            pivot["Bounce Rate (%)"] = pivot.apply(
                lambda row: (row["bounce"] / row["processed"] * 100) if row["processed"] else 0, axis=1
            )

            # Time series charts
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Email Volume Over Time', 'Delivery Rate Trend', 'Open Rate Trend', 'Bounce Rate Trend'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )

            # Volume chart
            fig.add_trace(
                go.Scatter(x=pivot["processed_date"], y=pivot["processed"], name="Processed", line=dict(color='#1f77b4')),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=pivot["processed_date"], y=pivot["delivered"], name="Delivered", line=dict(color='#28a745')),
                row=1, col=1
            )

            # Rate charts
            fig.add_trace(
                go.Scatter(x=pivot["processed_date"], y=pivot["Delivery Rate (%)"], name="Delivery Rate", line=dict(color='#28a745')),
                row=1, col=2
            )
            fig.add_trace(
                go.Scatter(x=pivot["processed_date"], y=pivot["Open Rate (%)"], name="Open Rate", line=dict(color='#17a2b8')),
                row=2, col=1
            )
            fig.add_trace(
                go.Scatter(x=pivot["processed_date"], y=pivot["Bounce Rate (%)"], name="Bounce Rate", line=dict(color='#dc3545')),
                row=2, col=2
            )

            fig.update_layout(height=600, showlegend=False, title_text="Email Performance Trends")
            st.plotly_chart(fig, use_container_width=True)

            # Data table
            st.subheader("📋 Daily Performance Data")
            st.dataframe(
                pivot.round(2),
                use_container_width=True
            )
        else:
            st.warning("⚠️ No data available for trends analysis.")

    # Tab 3: Date Drilldown
    with tab3:
        st.header("🔍 Date-Specific Analysis")
        
        if total_processed > 0:
            available_dates = sorted(df_filtered["processed_date"].unique(), reverse=True)
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                selected_date = st.selectbox(
                    "📅 Select Date",
                    options=available_dates,
                    format_func=lambda x: x.strftime("%Y-%m-%d (%A)"),
                    help="Choose a specific date to analyze"
                )
            
            if selected_date:
                df_date = df_filtered[df_filtered["processed_date"] == selected_date]
                
                # Calculate date-specific metrics
                processed_set_date = set(df_date[df_date["event"] == "processed"]["message_id"].unique())
                delivered_set_date = set(df_date[df_date["event"] == "delivered"]["message_id"].unique())
                open_set_date = set(df_date[df_date["event"] == "open"]["message_id"].unique())
                bounce_set_date = set(df_date[df_date["event"] == "bounce"]["message_id"].unique())

                total_processed_date = len(processed_set_date)
                total_delivered_date = len(delivered_set_date.intersection(processed_set_date))
                total_open_date = len(open_set_date.intersection(delivered_set_date))
                total_bounce_date = len(bounce_set_date.intersection(processed_set_date))

                st.subheader(f"📊 Performance for {selected_date.strftime('%B %d, %Y')}")
                
                if total_processed_date > 0:
                    display_metric_cards(total_processed_date, total_delivered_date, total_open_date, total_bounce_date)
                    
                    # Comparison with overall averages
                    st.markdown("---")
                    st.subheader("📈 Comparison with Overall Average")
                    
                    overall_delivery_rate = (total_delivered / total_processed * 100) if total_processed else 0
                    overall_open_rate = (total_open / total_delivered * 100) if total_delivered else 0
                    overall_bounce_rate = (total_bounce / total_processed * 100) if total_processed else 0
                    
                    date_delivery_rate = (total_delivered_date / total_processed_date * 100) if total_processed_date else 0
                    date_open_rate = (total_open_date / total_delivered_date * 100) if total_delivered_date else 0
                    date_bounce_rate = (total_bounce_date / total_processed_date * 100) if total_processed_date else 0
                    
                    comparison_data = {
                        "Metric": ["Delivery Rate (%)", "Open Rate (%)", "Bounce Rate (%)"],
                        "Selected Date": [round(date_delivery_rate, 2), round(date_open_rate, 2), round(date_bounce_rate, 2)],
                        "Overall Average": [round(overall_delivery_rate, 2), round(overall_open_rate, 2), round(overall_bounce_rate, 2)],
                        "Difference": [
                            round(date_delivery_rate - overall_delivery_rate, 2),
                            round(date_open_rate - overall_open_rate, 2),
                            round(date_bounce_rate - overall_bounce_rate, 2)
                        ]
                    }
                    
                    st.dataframe(
                        pd.DataFrame(comparison_data),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("ℹ️ No email data found for the selected date.")
        else:
            st.warning("⚠️ No data available for date analysis.")

    # Tab 4: Downloads
    with tab4:
        st.header("📥 Export Data")
        
        if total_processed > 0:
            st.markdown("### Available Downloads")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Summary Reports")
                
                # Overall summary
                overall_summary_df = pd.DataFrame({
                    "Metric": ["Total Processed", "Total Delivered", "Total Opened", "Total Bounced", 
                              "Delivery Rate (%)", "Open Rate (%)", "Bounce Rate (%)"],
                    "Value": [total_processed, total_delivered, total_open, total_bounce,
                             round((total_delivered / total_processed * 100) if total_processed else 0, 2),
                             round((total_open / total_delivered * 100) if total_delivered else 0, 2),
                             round((total_bounce / total_processed * 100) if total_processed else 0, 2)]
                })
                
                overall_excel_data = to_excel(overall_summary_df)
                st.download_button(
                    label="📊 Download Overall Summary",
                    data=overall_excel_data,
                    file_name=f"sendgrid_overall_summary_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            with col2:
                st.subheader("📈 Daily Data")
                
                # Daily pivot data
                if 'pivot' in locals():
                    daily_excel_data = to_excel(pivot)
                    st.download_button(
                        label="📈 Download Daily Trends",
                        data=daily_excel_data,
                        file_name=f"sendgrid_daily_trends_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            
            st.markdown("---")
            st.markdown("### 📋 Raw Data Export")
            
            # Filtered data export
            filtered_excel_data = to_excel(df_filtered)
            st.download_button(
                label="📋 Download Filtered Raw Data",
                data=filtered_excel_data,
                file_name=f"sendgrid_filtered_data_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.info("ℹ️ No data available for download. Please check your filters.")

else:
    # Welcome screen
    st.markdown("""
    <div style='text-align: center; padding: 3rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin: 2rem 0;'>
        <h2 style='color: white; margin-bottom: 1rem;'>Welcome to SendGrid Analytics Dashboard</h2>
        <p style='color: white; font-size: 1.1rem; margin-bottom: 2rem;'>
            Upload your SendGrid events CSV file to start analyzing your email performance with 
            interactive charts, detailed metrics, and actionable insights.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 📊 **Overview Analytics**
        - Email delivery rates
        - Open and bounce metrics
        - Performance indicators
        """)
    
    with col2:
        st.markdown("""
        ### 📈 **Trend Analysis**
        - Daily performance trends
        - Interactive charts
        - Time-series visualization
        """)
    
    with col3:
        st.markdown("""
        ### 🔍 **Detailed Insights**
        - Date-specific analysis
        - Comparative metrics
        - Export capabilities
        """)
    
    st.info("👆 Use the sidebar to upload your SendGrid events CSV file and get started!")