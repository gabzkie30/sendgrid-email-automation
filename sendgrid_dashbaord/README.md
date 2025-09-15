# SendGrid Email Analytics Dashboard

A clean, professional Streamlit dashboard for analyzing SendGrid email performance data with interactive visualizations and comprehensive reporting.

## 🚀 Features

- **Performance Overview**: Key metrics including delivery rates, open rates, and bounce rates
- **Trend Analysis**: Interactive charts showing email performance over time
- **Daily Breakdown**: Detailed daily performance data with filtering options
- **Data Export**: Excel reports for summary and detailed data
- **Clean UI**: Modern, minimalist interface focused on usability

## 📁 Project Structure

```
sendgrid_dashboard/
├── app.py                 # Main Streamlit application
├── config.py             # Configuration and constants
├── data_processor.py      # Data loading and processing logic
├── visualizations.py      # Chart creation and visualization functions
├── utils.py              # Helper functions and utilities
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🛠️ Installation

1. **Clone or download the project files**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   streamlit run app.py
   ```

4. **Open your browser** and navigate to the displayed URL (usually `http://localhost:8501`)

## 📊 Usage

### Data Upload
1. Export your SendGrid events data as CSV
2. Use the sidebar file uploader to upload your CSV file
3. The dashboard will automatically process and validate the data

### Required CSV Columns
Your SendGrid events CSV should contain these columns:
- `event`: Event type (processed, delivered, open, bounce)
- `message_id`: Unique identifier for each email
- `processed`: Timestamp when email was processed
- `subject` (optional): Email subject line
- `email` (optional): Recipient email address

### Filtering Options
- **Date Range**: Filter data by specific date range
- **Email Subjects**: Include only specific email campaigns
- **Exclude Emails**: Remove specific email addresses from analysis

### Dashboard Sections

#### 📊 Daily View
- View day-by-day performance metrics
- See processed, delivered, opened, and bounced email counts
- Review delivery rates, open rates, and bounce rates for each day

#### 📈 Trends
- Interactive line charts showing email volume trends
- Performance rate trends over time
- Daily volume breakdown with bar charts

#### 📥 Export
- Download summary reports in Excel format
- Export detailed daily data
- Timestamped filenames for easy organization

## 📈 Metrics Explained

### Key Performance Indicators (KPIs)
- **Delivery Rate**: Percentage of emails successfully delivered (Target: >95%)
- **Open Rate**: Percentage of delivered emails that were opened (Target: >15-25%)
- **Bounce Rate**: Percentage of emails that bounced (Target: <5%)

### Performance Benchmarks
The dashboard includes industry-standard benchmarks:
- 🟢 **Excellent**: Delivery >95%, Open >25%, Bounce <2%
- 🟡 **Good**: Delivery >90%, Open >15%, Bounce <5%
- 🔴 **Needs Improvement**: Below good thresholds

## 🔧 Customization

### Modifying Colors
Edit `config.py` to change the color scheme:
```python
COLORS = {
    'processed': '#3498db',    # Blue
    'delivered': '#2ecc71',    # Green
    'open': '#f39c12',         # Orange
    'bounce': '#e74c3c',       # Red
    # ... more colors
}
```

### Adding New Visualizations
Add new chart functions to `visualizations.py` and import them in `app.py`.

### Changing Benchmarks
Modify performance benchmarks in `config.py`:
```python
BENCHMARKS = {
    'delivery_rate': {'excellent': 95, 'good': 90},
    'open_rate': {'excellent': 25, 'good': 15},
    'bounce_rate': {'excellent': 2, 'acceptable': 5}
}
```

## 🐛 Troubleshooting

### Common Issues

**"Missing required columns" error**
- Ensure your CSV has `event`, `message_id`, and `processed` columns
- Check that column names don't have extra spaces

**No data showing after upload**
- Verify your CSV contains valid SendGrid events (processed, delivered, open, bounce)
- Check that the `processed` column contains valid timestamps

**Charts not displaying**
- Ensure you have data for multiple days to show trends
- Check that your date filters aren't too restrictive

### Data Quality Tips
- Remove any test emails before analysis
- Ensure consistent date formatting in your CSV
- Verify message_id values are unique per email

## 📝 File Descriptions

### `app.py`
Main Streamlit application containing:
- Page configuration and layout
- User interface components
- Tab management and navigation
- Session state management

### `config.py`
Configuration constants including:
- Valid event types and required columns
- Color schemes for charts
- Performance benchmarks
- UI settings

### `data_processor.py`
Data processing logic including:
- CSV loading and validation
- Data cleaning and filtering
- Metric calculations
- Pivot table creation

### `visualizations.py`
Chart creation functions including:
- Trend line charts
- Performance donut charts
- Rate comparison charts
- Volume bar charts

### `utils.py`
Helper functions including:
- Excel export functionality
- Number formatting
- Performance status evaluation
- File naming utilities

## 🤝 Contributing

To extend the dashboard:
1. Add new functions to appropriate modules
2. Update `config.py` for new constants
3. Import and use new functions in `app.py`
4. Test thoroughly with sample data

## 📄 License

This project is open source and available under the MIT License.

## 🔗 Dependencies

- **Streamlit**: Web app framework
- **Pandas**: Data manipulation and analysis
- **Plotly**: Interactive visualizations
- **XlsxWriter**: Excel file creation
- **OpenPyXL**: Excel file handling

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify your data format matches requirements
3. Ensure all dependencies are properly installed
4. Test with a small sample dataset first