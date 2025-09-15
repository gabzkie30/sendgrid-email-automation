"""
Visualization module for SendGrid Analytics Dashboard
Contains all chart creation and data visualization functions
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import COLORS, CHART_CONFIG


def create_trend_chart(data, title="Email Performance Over Time"):
    """
    Create a line chart showing email trends over time
    
    Args:
        data (pd.DataFrame): DataFrame with daily data
        title (str): Chart title
    
    Returns:
        plotly.graph_objects.Figure: Interactive line chart
    """
    if data.empty:
        return go.Figure().add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    fig = px.line(
        data, 
        x='processed_date', 
        y=['processed', 'delivered', 'open'], 
        title=title,
        color_discrete_map={
            'processed': COLORS['processed'],
            'delivered': COLORS['delivered'], 
            'open': COLORS['open']
        },
        labels={
            'processed_date': 'Date',
            'value': 'Number of Emails',
            'variable': 'Event Type'
        }
    )
    
    fig.update_layout(
        showlegend=True,
        height=CHART_CONFIG['height'],
        margin=CHART_CONFIG['margin'],
        plot_bgcolor=CHART_CONFIG['plot_bgcolor'],
        hovermode='x unified'
    )
    
    return fig


def create_performance_donut(processed, delivered, opened, bounced, title="Email Distribution"):
    """
    Create a donut chart showing email performance distribution
    
    Args:
        processed (int): Total processed emails
        delivered (int): Total delivered emails
        opened (int): Total opened emails
        bounced (int): Total bounced emails
        title (str): Chart title
    
    Returns:
        plotly.graph_objects.Figure: Donut chart
    """
    if processed == 0:
        return go.Figure().add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    # Calculate segments
    not_delivered = processed - delivered - bounced
    
    fig = go.Figure(data=[go.Pie(
        labels=['Delivered', 'Opened', 'Bounced', 'Not Delivered'],
        values=[delivered, opened, bounced, max(0, not_delivered)],
        hole=0.4,
        marker_colors=[
            COLORS['delivered'], 
            COLORS['open'], 
            COLORS['bounce'], 
            '#95a5a6'
        ]
    )])
    
    fig.update_layout(
        title=title,
        showlegend=True,
        height=400,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig


def create_rate_comparison_chart(data, title="Performance Rates Over Time"):
    """
    Create a chart comparing different rates over time
    
    Args:
        data (pd.DataFrame): DataFrame with daily rates
        title (str): Chart title
    
    Returns:
        plotly.graph_objects.Figure: Rate comparison chart
    """
    if data.empty or 'Delivery Rate' not in data.columns:
        return go.Figure().add_annotation(
            text="No rate data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    fig = go.Figure()
    
    # Add delivery rate
    fig.add_trace(go.Scatter(
        x=data['processed_date'],
        y=data['Delivery Rate'],
        mode='lines+markers',
        name='Delivery Rate (%)',
        line=dict(color=COLORS['delivered'], width=3),
        marker=dict(size=6)
    ))
    
    # Add open rate
    if 'Open Rate' in data.columns:
        fig.add_trace(go.Scatter(
            x=data['processed_date'],
            y=data['Open Rate'],
            mode='lines+markers',
            name='Open Rate (%)',
            line=dict(color=COLORS['open'], width=3),
            marker=dict(size=6)
        ))
    
    # Add bounce rate
    if 'Bounce Rate' in data.columns:
        fig.add_trace(go.Scatter(
            x=data['processed_date'],
            y=data['Bounce Rate'],
            mode='lines+markers',
            name='Bounce Rate (%)',
            line=dict(color=COLORS['bounce'], width=3),
            marker=dict(size=6)
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Rate (%)',
        height=CHART_CONFIG['height'],
        margin=CHART_CONFIG['margin'],
        plot_bgcolor=CHART_CONFIG['plot_bgcolor'],
        hovermode='x unified',
        showlegend=True
    )
    
    return fig


def create_metric_gauge(value, title, max_value=100, color=None):
    """
    Create a gauge chart for a single metric
    
    Args:
        value (float): Current value
        title (str): Gauge title
        max_value (float): Maximum value for the gauge
        color (str): Color for the gauge
    
    Returns:
        plotly.graph_objects.Figure: Gauge chart
    """
    if color is None:
        color = COLORS['primary']
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title},
        delta={'reference': max_value * 0.8},
        gauge={
            'axis': {'range': [None, max_value]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, max_value * 0.5], 'color': "lightgray"},
                {'range': [max_value * 0.5, max_value * 0.8], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_value * 0.9
            }
        }
    ))
    
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig


def create_volume_bar_chart(data, title="Daily Email Volume"):
    """
    Create a bar chart showing daily email volumes
    
    Args:
        data (pd.DataFrame): DataFrame with daily data
        title (str): Chart title
    
    Returns:
        plotly.graph_objects.Figure: Bar chart
    """
    if data.empty:
        return go.Figure().add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    fig = go.Figure()
    
    # Add bars for each event type
    fig.add_trace(go.Bar(
        x=data['processed_date'],
        y=data['processed'],
        name='Processed',
        marker_color=COLORS['processed']
    ))
    
    fig.add_trace(go.Bar(
        x=data['processed_date'],
        y=data['delivered'],
        name='Delivered',
        marker_color=COLORS['delivered']
    ))
    
    fig.add_trace(go.Bar(
        x=data['processed_date'],
        y=data['open'],
        name='Opened',
        marker_color=COLORS['open']
    ))
    
    if 'bounce' in data.columns:
        fig.add_trace(go.Bar(
            x=data['processed_date'],
            y=data['bounce'],
            name='Bounced',
            marker_color=COLORS['bounce']
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Number of Emails',
        height=CHART_CONFIG['height'],
        margin=CHART_CONFIG['margin'],
        plot_bgcolor=CHART_CONFIG['plot_bgcolor'],
        barmode='group',
        showlegend=True
    )
    
    return fig


def create_comparison_chart(current_metrics, comparison_metrics, title="Performance Comparison"):
    """
    Create a comparison chart between two sets of metrics
    
    Args:
        current_metrics (dict): Current period metrics
        comparison_metrics (dict): Comparison period metrics
        title (str): Chart title
    
    Returns:
        plotly.graph_objects.Figure: Comparison chart
    """
    metrics = ['delivery_rate', 'open_rate', 'bounce_rate']
    metric_labels = ['Delivery Rate (%)', 'Open Rate (%)', 'Bounce Rate (%)']
    
    current_values = [current_metrics.get(m, 0) for m in metrics]
    comparison_values = [comparison_metrics.get(m, 0) for m in metrics]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=metric_labels,
        y=current_values,
        name='Current',
        marker_color=COLORS['primary']
    ))
    
    fig.add_trace(go.Bar(
        x=metric_labels,
        y=comparison_values,
        name='Comparison',
        marker_color=COLORS['secondary']
    ))
    
    fig.update_layout(
        title=title,
        yaxis_title='Rate (%)',
        height=CHART_CONFIG['height'],
        margin=CHART_CONFIG['margin'],
        plot_bgcolor=CHART_CONFIG['plot_bgcolor'],
        barmode='group',
        showlegend=True
    )
    
    return fig


def create_simple_metric_chart(value, title, format_type="number"):
    """
    Create a simple metric display chart
    
    Args:
        value (float): Value to display
        title (str): Metric title
        format_type (str): How to format the value
    
    Returns:
        plotly.graph_objects.Figure: Simple metric chart
    """
    if format_type == "percentage":
        display_value = f"{value:.1f}%"
    elif format_type == "number":
        display_value = f"{value:,.0f}"
    else:
        display_value = str(value)
    
    fig = go.Figure()
    
    fig.add_annotation(
        text=f"<b>{display_value}</b>",
        x=0.5, y=0.6,
        xref="paper", yref="paper",
        font=dict(size=30, color=COLORS['primary']),
        showarrow=False
    )
    
    fig.add_annotation(
        text=title,
        x=0.5, y=0.3,
        xref="paper", yref="paper",
        font=dict(size=16, color=COLORS['secondary']),
        showarrow=False
    )
    
    fig.update_layout(
        height=150,
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    
    return fig