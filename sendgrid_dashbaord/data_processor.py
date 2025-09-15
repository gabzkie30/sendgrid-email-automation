"""
Data processing module for SendGrid Analytics Dashboard
Handles data loading, cleaning, filtering, and metric calculations
"""

import pandas as pd
from config import VALID_EVENTS, REQUIRED_COLUMNS
from utils import validate_dataframe, clean_column_names, calculate_rate


class SendGridDataProcessor:
    """
    Main class for processing SendGrid email event data
    """
    
    def __init__(self):
        self.raw_data = None
        self.processed_data = None
        self.filtered_data = None
    
    def load_data(self, uploaded_file):
        """
        Load and validate CSV data
        
        Args:
            uploaded_file: Streamlit uploaded file object
        
        Returns:
            tuple: (success, error_message)
        """
        try:
            # Load CSV
            self.raw_data = pd.read_csv(uploaded_file)
            
            # Clean column names
            self.raw_data = clean_column_names(self.raw_data)
            
            # Validate required columns
            is_valid, missing_cols = validate_dataframe(self.raw_data, REQUIRED_COLUMNS)
            
            if not is_valid:
                return False, f"Missing required columns: {missing_cols}"
            
            return True, "Data loaded successfully"
            
        except Exception as e:
            return False, f"Error loading data: {str(e)}"
    
    def process_data(self):
        """
        Process raw data: filter events, clean dates, remove duplicates
        
        Returns:
            bool: Success status
        """
        if self.raw_data is None:
            return False
        
        df = self.raw_data.copy()
        
        # Filter valid events
        df = df[df["event"].isin(VALID_EVENTS)]
        
        # Process datetime
        df["processed_datetime"] = pd.to_datetime(df["processed"], errors='coerce')
        df = df.dropna(subset=["processed_datetime"])
        df["processed_date"] = df["processed_datetime"].dt.date
        
        # Find processed message IDs
        processed_ids = set(df.loc[df["event"] == "processed", "message_id"].unique())
        df = df[df["message_id"].isin(processed_ids)]
        
        # Remove duplicate events per message per date
        df["unique_event"] = (df["message_id"].astype(str) + "_" + 
                             df["event"] + "_" + 
                             df["processed_date"].astype(str))
        df = df.drop_duplicates(subset=["unique_event"])
        
        # Process subjects if available
        if "subject" in df.columns:
            processed_df = df[df["event"] == "processed"][["message_id", "subject"]].drop_duplicates(subset=["message_id"])
            df = df.merge(processed_df, on="message_id", how="left", suffixes=('', '_processed'))
            df["subject"] = df["subject_processed"]
        
        self.processed_data = df
        return True
    
    def get_date_range(self):
        """
        Get the date range of processed data
        
        Returns:
            tuple: (min_date, max_date)
        """
        if self.processed_data is None:
            return None, None
        
        return (self.processed_data["processed_date"].min(), 
                self.processed_data["processed_date"].max())
    
    def get_unique_subjects(self):
        """
        Get list of unique email subjects
        
        Returns:
            list: Sorted list of unique subjects
        """
        if self.processed_data is None or "subject" not in self.processed_data.columns:
            return []
        
        return sorted(self.processed_data["subject"].dropna().unique())
    
    def get_unique_emails(self):
        """
        Get list of unique email addresses
        
        Returns:
            list: Sorted list of unique email addresses
        """
        if self.processed_data is None or "email" not in self.processed_data.columns:
            return []
        
        return sorted(self.processed_data["email"].dropna().unique())
    
    def apply_filters(self, date_range=None, selected_subjects=None, excluded_emails=None):
        """
        Apply filters to processed data
        
        Args:
            date_range (tuple): Start and end date
            selected_subjects (list): List of subjects to include
            excluded_emails (list): List of emails to exclude
        
        Returns:
            pd.DataFrame: Filtered data
        """
        if self.processed_data is None:
            return pd.DataFrame()
        
        df = self.processed_data.copy()
        
        # Apply date filter
        if date_range and isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            mask = (df["processed_date"] >= start_date) & (df["processed_date"] <= end_date)
            df = df[mask]
        
        # Apply subject filter
        if selected_subjects and "subject" in df.columns:
            df = df[df["subject"].isin(selected_subjects)]
        
        # Apply email exclusion filter
        if excluded_emails and "email" in df.columns:
            df = df[~df["email"].isin(excluded_emails)]
        
        self.filtered_data = df
        return df
    
    def calculate_metrics(self, data=None):
        """
        Calculate email metrics from data
        
        Args:
            data (pd.DataFrame): Data to calculate metrics from (uses filtered_data if None)
        
        Returns:
            dict: Dictionary containing all metrics
        """
        if data is None:
            data = self.filtered_data
        
        if data is None or data.empty:
            return {
                "total_processed": 0,
                "total_delivered": 0,
                "total_opened": 0,
                "total_bounced": 0,
                "delivery_rate": 0,
                "open_rate": 0,
                "bounce_rate": 0
            }
        
        # Calculate unique message counts by event type
        processed_set = set(data[data["event"] == "processed"]["message_id"].unique())
        delivered_set = set(data[data["event"] == "delivered"]["message_id"].unique())
        open_set = set(data[data["event"] == "open"]["message_id"].unique())
        bounce_set = set(data[data["event"] == "bounce"]["message_id"].unique())
        
        # Calculate totals
        total_processed = len(processed_set)
        total_delivered = len(delivered_set.intersection(processed_set))
        total_opened = len(open_set.intersection(delivered_set))
        total_bounced = len(bounce_set.intersection(processed_set))
        
        # Calculate rates
        delivery_rate = calculate_rate(total_delivered, total_processed)
        open_rate = calculate_rate(total_opened, total_delivered)
        bounce_rate = calculate_rate(total_bounced, total_processed)
        
        return {
            "total_processed": total_processed,
            "total_delivered": total_delivered,
            "total_opened": total_opened,
            "total_bounced": total_bounced,
            "delivery_rate": delivery_rate,
            "open_rate": open_rate,
            "bounce_rate": bounce_rate
        }
    
    def create_daily_pivot(self, data=None):
        """
        Create daily pivot table with metrics
        
        Args:
            data (pd.DataFrame): Data to pivot (uses filtered_data if None)
        
        Returns:
            pd.DataFrame: Daily pivot table with rates
        """
        if data is None:
            data = self.filtered_data
        
        if data is None or data.empty:
            return pd.DataFrame()
        
        # Create pivot table
        pivot = data.pivot_table(
            index="processed_date",
            columns="event",
            values="message_id",
            aggfunc=lambda x: x.nunique(),
            fill_value=0
        ).reset_index().sort_values("processed_date")
        
        # Ensure all event columns exist
        for col in VALID_EVENTS:
            if col not in pivot.columns:
                pivot[col] = 0
        
        # Calculate rates
        pivot["Delivery Rate"] = pivot.apply(
            lambda row: calculate_rate(row["delivered"], row["processed"]), axis=1
        )
        pivot["Open Rate"] = pivot.apply(
            lambda row: calculate_rate(row["open"], row["delivered"]), axis=1
        )
        pivot["Bounce Rate"] = pivot.apply(
            lambda row: calculate_rate(row["bounce"], row["processed"]), axis=1
        )
        
        return pivot
    
    def get_date_specific_data(self, selected_date):
        """
        Get data for a specific date
        
        Args:
            selected_date: Date to filter by
        
        Returns:
            pd.DataFrame: Data for the specified date
        """
        if self.filtered_data is None:
            return pd.DataFrame()
        
        return self.filtered_data[self.filtered_data["processed_date"] == selected_date]
    
    def create_summary_dataframe(self, metrics):
        """
        Create summary DataFrame for export
        
        Args:
            metrics (dict): Metrics dictionary
        
        Returns:
            pd.DataFrame: Summary DataFrame
        """
        return pd.DataFrame({
            "Metric": [
                "Total Processed", "Total Delivered", "Total Opened", "Total Bounced",
                "Delivery Rate (%)", "Open Rate (%)", "Bounce Rate (%)"
            ],
            "Value": [
                metrics["total_processed"], metrics["total_delivered"], 
                metrics["total_opened"], metrics["total_bounced"],
                round(metrics["delivery_rate"], 2), round(metrics["open_rate"], 2), 
                round(metrics["bounce_rate"], 2)
            ]
        })