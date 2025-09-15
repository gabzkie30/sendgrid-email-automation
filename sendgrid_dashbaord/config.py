"""
Configuration file for SendGrid Analytics Dashboard
Contains all constants, settings, and configuration parameters
"""

# Valid SendGrid events to process
VALID_EVENTS = ["processed", "delivered", "open", "bounce"]

# Required columns in the CSV file
REQUIRED_COLUMNS = ["event", "message_id", "processed"]

# Color scheme for charts
COLORS = {
    'processed': '#3498db',
    'delivered': '#2ecc71', 
    'open': '#f39c12',
    'bounce': '#e74c3c',
    'primary': '#2c3e50',
    'secondary': '#34495e',
    'light_gray': '#ecf0f1',
    'border': '#e1e8ed'
}

# Performance benchmarks
BENCHMARKS = {
    'delivery_rate': {
        'excellent': 95,
        'good': 90
    },
    'open_rate': {
        'excellent': 25,
        'good': 15
    },
    'bounce_rate': {
        'excellent': 2,
        'acceptable': 5
    }
}

# UI Configuration
UI_CONFIG = {
    'page_title': "SendGrid Analytics",
    'page_icon': "📧",
    'layout': "wide",
    'sidebar_state': "expanded"
}

# Chart configuration
CHART_CONFIG = {
    'height': 300,
    'margin': dict(l=0, r=0, t=40, b=0),
    'plot_bgcolor': 'white'
}

# File export settings
EXPORT_CONFIG = {
    'engine': 'xlsxwriter',
    'sheet_name': 'Email_Analytics'
}