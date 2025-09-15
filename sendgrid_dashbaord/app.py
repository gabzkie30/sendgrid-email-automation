"""
Main Streamlit application for SendGrid Analytics Dashboard
"""

import streamlit as st
from datetime import datetime

# Import custom modules
from config import UI_CONFIG, COLORS
from data_processor import SendGridDataProcessor
from visualizations import (
    create_trend_chart, 
    create_performance_donut, 
    create_rate_comparison_chart,
    create_volume_bar_chart
)
from utils import (
    to_excel, 
    generate_filename, 
    format_number, 
    get_performance_status
)


def setup_page():
    """Configure Streamlit page settings and custom CSS"""
    st.set_page_config(
        page_title=UI_CONFIG['page_title'],
        page_icon=UI_CONFIG['page_icon'],
        layout=UI_CONFIG['layout'],
        initial_sidebar_state=UI_CONFIG['sidebar_state']
    )
    
    # Custom CSS for clean design
    st.markdown(f"""
    <style>
        .main-header {{
            font-size: 2rem;
            font-weight: 600;
            color: {COLORS['primary']};
            margin-bottom: 2rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid {COLORS['light_gray']};
        }}
        
        .metric-card {{
            background: #ffffff;
            padding: 1.5rem;
            border-radius: 8px;
            border: 1px solid {COLORS['border']};
            text-align: center;
        }}
        
        .section-header {{
            font-size: 1.2rem;
            font-weight: 500;
            color: {COLORS['secondary']};
            margin: 1.5rem 0 1rem 0;
        }}
        
        .upload-area {{
            border: 2px dashed #bdc3c7;
            border-radius: 8px;
            padding: 2rem;
            text-align: center;
            background: #fafbfc;
        }}
        
        .status-excellent {{ color: #27ae60; }}
        .status-good {{ color: #f39c12; }}
        .status-poor {{ color: #e74c3c; }}
    </style>
    """, unsafe_allow_html=True)


def render_sidebar(processor):
    """Render sidebar with filters and controls"""
    with st.sidebar:
        st.subheader("📁 Upload Data")
        uploaded_file = st.file_uploader(
            "Choose SendGrid CSV file", 
            type="csv",
            help="Upload your SendGrid events CSV file"
        )
        
        if uploaded_file:
            # Load data
            if 'data_loaded' not in st.session_state:
                success, message = processor.load_data(uploaded_file)
                if success:
                    processor.process_data()
                    st.session_state.data_loaded = True
                    st.success("✅ Data loaded successfully!")
                else:
                    st.error(f"❌ {message}")
                    return None, None, None, None
            
            # Filters section
            st.subheader("🎯 Filters")
            
            # Date range filter
            min_date, max_date = processor.get_date_range()
            if min_date and max_date:
                date_range = st.date_input(
                    "Date Range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
            else:
                date_range = None
            
            # Subject filter
            subjects = processor.get_unique_subjects()
            if subjects:
                selected_subjects = st.multiselect(
                    "Email Subjects",
                    options=subjects,
                    default=subjects,
                    help="Select email subjects to include in analysis"
                )
            else:
                selected_subjects = []
            
            # Email exclusion filter
            emails = processor.get_unique_emails()
            excluded_emails = []
            if emails:
                with st.expander("🚫 Exclude Emails"):
                    excluded_emails = st.multiselect(
                        "Select emails to exclude",
                        options=emails,
                        help="Exclude specific email addresses from analysis"
                    )
            
            return uploaded_file, date_range, selected_subjects, excluded_emails
        
        return None, None, None, None


def render_metrics_overview(metrics):
    """Render key metrics in card layout"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📤 Emails Sent",
            format_number(metrics['total_processed']),
            help="Total number of emails processed by SendGrid"
        )
    
    with col2:
        delivery_status, _ = get_performance_status(metrics['delivery_rate'], 'delivery_rate')
        st.metric(
            "✅ Delivered",
            format_number(metrics['total_delivered']),
            f"{metrics['delivery_rate']:.1f}%",
            help="Emails successfully delivered to recipients"
        )
        st.caption(delivery_status)
    
    with col3:
        open_status, _ = get_performance_status(metrics['open_rate'], 'open_rate')
        st.metric(
            "👁️ Opened",
            format_number(metrics['total_opened']),
            f"{metrics['open_rate']:.1f}%",
            help="Emails opened by recipients"
        )
        st.caption(open_status)
    
    with col4:
        bounce_status, _ = get_performance_status(metrics['bounce_rate'], 'bounce_rate')
        st.metric(
            "❌ Bounced",
            format_number(metrics['total_bounced']),
            f"{metrics['bounce_rate']:.1f}%",
            help="Emails that bounced and were not delivered"
        )
        st.caption(bounce_status)


def render_daily_view(processor):
    """Render daily performance view"""
    pivot_data = processor.create_daily_pivot()
    
    if not pivot_data.empty:
        # Display data table
        st.subheader("📅 Daily Performance")
        
        # Format the display data
        display_data = pivot_data.copy()
        display_data = display_data.round(1)
        
        st.dataframe(
            display_data[[
                'processed_date', 'processed', 'delivered', 'open', 
                'bounce', 'Delivery Rate', 'Open Rate', 'Bounce Rate'
            ]],
            use_container_width=True,
            hide_index=True
        )
        
        return pivot_data
    else:
        st.warning("⚠️ No daily data available")
        return None


def render_trends_view(pivot_data):
    """Render trends and visualizations"""
    if pivot_data is not None and len(pivot_data) > 1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Volume trends
            fig_volume = create_trend_chart(pivot_data, "Email Volume Trends")
            st.plotly_chart(fig_volume, use_container_width=True)
        
        with col2:
            # Rate trends
            fig_rates = create_rate_comparison_chart(pivot_data, "Performance Rate Trends")
            st.plotly_chart(fig_rates, use_container_width=True)
        
        # Volume bar chart
        st.subheader("📊 Daily Volume Breakdown")
        fig_bars = create_volume_bar_chart(pivot_data, "Daily Email Volume")
        st.plotly_chart(fig_bars, use_container_width=True)
        
    elif pivot_data is not None and len(pivot_data) == 1:
        st.info("ℹ️ Need more than one day of data to show trends")
    else:
        st.warning("⚠️ No trend data available")


def render_export_section(processor, metrics, pivot_data):
    """Render data export section"""
    st.subheader("📥 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📊 Summary Report**")
        summary_df = processor.create_summary_dataframe(metrics)
        summary_excel = to_excel(summary_df)
        
        st.download_button(
            "📊 Download Summary",
            data=summary_excel,
            file_name=generate_filename("summary"),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col2:
        st.markdown("**📈 Daily Data**")
        if pivot_data is not None and not pivot_data.empty:
            daily_excel = to_excel(pivot_data)
            
            st.download_button(
                "📈 Download Daily Data",
                data=daily_excel,
                file_name=generate_filename("daily_data"),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.info("No daily data available for export")


def render_welcome_screen():
    """Render welcome screen when no data is uploaded"""
    st.markdown("""
    <div class="upload-area">
        <h3>📧 SendGrid Email Analytics Dashboard</h3>
        <p>Upload your SendGrid events CSV file to start analyzing your email performance.</p>
        <p style="color: #7f8c8d; font-size: 0.9rem;">
            Supported events: processed, delivered, open, bounce
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature highlights
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📊 Performance Overview**")
        st.markdown("""
        • Delivery rates and metrics
        • Open and engagement tracking  
        • Bounce analysis and insights
        """)
    
    with col2:
        st.markdown("**📈 Trend Analysis**")
        st.markdown("""
        • Daily performance tracking
        • Interactive visualizations
        • Time-series analysis
        """)
    
    with col3:
        st.markdown("**📥 Data Export**")
        st.markdown("""
        • Excel report generation
        • Summary and detailed data
        • Filtered data exports
        """)


def main():
    """Main application function"""
    # Setup page configuration
    setup_page()
    
    # Initialize data processor
    if 'processor' not in st.session_state:
        st.session_state.processor = SendGridDataProcessor()
    
    processor = st.session_state.processor
    
    # Header
    st.markdown('<h1 class="main-header">SendGrid Email Analytics Dashboard</h1>', 
                unsafe_allow_html=True)
    
    # Render sidebar and get filters
    uploaded_file, date_range, selected_subjects, excluded_emails = render_sidebar(processor)
    
    if uploaded_file and 'data_loaded' in st.session_state:
        # Apply filters
        filtered_data = processor.apply_filters(
            date_range=date_range,
            selected_subjects=selected_subjects,
            excluded_emails=excluded_emails
        )
        
        # Calculate metrics
        metrics = processor.calculate_metrics(filtered_data)
        
        if metrics['total_processed'] > 0:
            # Render main content
            render_metrics_overview(metrics)
            
            st.markdown("---")
            
            # Create tabs
            tab1, tab2, tab3 = st.tabs(["📅 Daily View", "📈 Trends", "📥 Export"])
            
            with tab1:
                pivot_data = render_daily_view(processor)
            
            with tab2:
                pivot_data = processor.create_daily_pivot()
                render_trends_view(pivot_data)
            
            with tab3:
                pivot_data = processor.create_daily_pivot()
                render_export_section(processor, metrics, pivot_data)
        
        else:
            st.warning("⚠️ No data found with current filters. Please adjust your filter settings.")
    
    else:
        # Show welcome screen
        render_welcome_screen()


if __name__ == "__main__":
    main()