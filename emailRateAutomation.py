import streamlit as st
import pandas as pd
import io

st.title("📧 SendGrid Email Rates Dashboard")

uploaded_file = st.sidebar.file_uploader("Upload SendGrid events CSV", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()

    # Keep only the relevant events
    valid_events = ["processed", "delivered", "open", "bounce"]
    df = df[df["event"].isin(valid_events)]

    # Ensure processed_datetime exists (from 'processed' column in CSV)
    df["processed_datetime"] = pd.to_datetime(df["processed"], errors='coerce')
    df = df.dropna(subset=["processed_datetime"])
    df["processed_date"] = df["processed_datetime"].dt.date

    # Find all message_ids that have a processed event
    processed_ids = set(df.loc[df["event"] == "processed", "message_id"].unique())

    # Keep only events linked to message_ids that have a processed record
    df = df[df["message_id"].isin(processed_ids)]

    # Remove duplicate events per message_id per date
    df["unique_event"] = df["message_id"].astype(str) + "_" + df["event"] + "_" + df["processed_date"].astype(str)
    df = df.drop_duplicates(subset=["unique_event"])

    # Get processed subjects
    processed_df = df[df["event"] == "processed"][["message_id", "subject"]].drop_duplicates(subset=["message_id"])
    df = df.merge(processed_df, on="message_id", how="left", suffixes=('', '_processed'))
    df["subject"] = df["subject_processed"]

    # Sidebar: Filter by subject
    unique_subjects = sorted(df["subject"].dropna().unique())
    selected_subjects = st.sidebar.multiselect("Filter by Subject", options=unique_subjects, default=unique_subjects)
    df_filtered_subject = df[df["subject"].isin(selected_subjects)]

    # Sidebar: Exclude specific emails
    unique_emails = sorted(df_filtered_subject["email"].dropna().unique())
    excluded_emails = st.sidebar.multiselect(
        "Exclude specific emails (optional):", 
        options=unique_emails,
        default=[]
    )
    if excluded_emails:
        df_filtered = df_filtered_subject[~df_filtered_subject["email"].isin(excluded_emails)]
    else:
        df_filtered = df_filtered_subject

    def to_excel(df_):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_.to_excel(writer, index=False)
        return output.getvalue()

    # ================== TAB 1: OVERALL SUMMARY ==================
    tab1, tab2, tab3 = st.tabs(["📊 Overall Summary", "📅 Daily Pivot & Chart", "🔍 Date Drilldown"])

    with tab1:
        processed_set = set(df_filtered[df_filtered["event"] == "processed"]["message_id"].unique())
        delivered_set = set(df_filtered[df_filtered["event"] == "delivered"]["message_id"].unique())
        open_set = set(df_filtered[df_filtered["event"] == "open"]["message_id"].unique())
        bounce_set = set(df_filtered[df_filtered["event"] == "bounce"]["message_id"].unique())

        total_processed = len(processed_set)
        total_delivered = len(delivered_set.intersection(processed_set))
        total_open = len(open_set.intersection(delivered_set))
        total_bounce = len(bounce_set.intersection(processed_set))

        delivery_rate = (total_delivered / total_processed * 100) if total_processed else 0
        open_rate = (total_open / total_delivered * 100) if total_delivered else 0
        bounce_rate = (total_bounce / total_processed * 100) if total_processed else 0

        st.header("Overall Email Rates Summary")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Total Processed (Sent):** {total_processed}")
            st.markdown(f"**Total Delivered:** {total_delivered}")
            st.markdown(f"**Total Opened:** {total_open}")
        with col2:
            st.markdown(f"**Total Bounced:** {total_bounce}")
            st.markdown(f"**Delivery Rate:** {delivery_rate:.2f}%")
            st.markdown(f"**Open Rate:** {open_rate:.2f}%")
            st.markdown(f"**Bounce Rate:** {bounce_rate:.2f}%")

        overall_summary_df = pd.DataFrame({
            "Metric": ["Total Processed", "Total Delivered", "Total Opened", "Total Bounced", "Delivery Rate (%)", "Open Rate (%)", "Bounce Rate (%)"],
            "Value": [total_processed, total_delivered, total_open, total_bounce, round(delivery_rate, 2), round(open_rate, 2), round(bounce_rate, 2)]
        })

        overall_excel_data = to_excel(overall_summary_df)
        st.download_button(
            label="Download Overall Email Rates Summary as Excel",
            data=overall_excel_data,
            file_name="sendgrid_email_rates_overall_summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # ================== TAB 2: DAILY PIVOT ==================
    with tab2:
        st.header("Daily Email Events Pivot Table with Date Range Filter")

        min_date = df_filtered["processed_date"].min()
        max_date = df_filtered["processed_date"].max()

        date_range = st.date_input(
            "Select date range to filter daily email rates",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            mask = (df_filtered["processed_date"] >= start_date) & (df_filtered["processed_date"] <= end_date)
            df_range = df_filtered[mask]
        else:
            df_range = df_filtered

        pivot_range = df_range.pivot_table(
            index="processed_date",
            columns="event",
            values="message_id",
            aggfunc=lambda x: x.nunique(),
            fill_value=0
        ).reset_index().sort_values("processed_date")

        for col in ["processed", "delivered", "open", "bounce"]:
            if col not in pivot_range.columns:
                pivot_range[col] = 0

        pivot_range["Delivery Rate (%)"] = pivot_range.apply(
            lambda row: (row["delivered"] / row["processed"] * 100) if row["processed"] else 0,
            axis=1
        )
        pivot_range["Open Rate (%)"] = pivot_range.apply(
            lambda row: (row["open"] / row["delivered"] * 100) if row["delivered"] else 0,
            axis=1
        )
        pivot_range["Bounce Rate (%)"] = pivot_range.apply(
            lambda row: (row["bounce"] / row["processed"] * 100) if row["processed"] else 0,
            axis=1
        )

        st.dataframe(pivot_range)
        st.bar_chart(pivot_range.set_index("processed_date")[["processed", "delivered", "open", "bounce"]])

        daily_excel_data_range = to_excel(pivot_range)
        st.download_button(
            label=f"Download Daily Email Rates ({start_date} to {end_date}) as Excel",
            data=daily_excel_data_range,
            file_name=f"sendgrid_email_rates_{start_date}_to_{end_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # ================== TAB 3: DATE DRILLDOWN ==================
    with tab3:
        pivot = df_filtered.pivot_table(
            index="processed_date",
            columns="event",
            values="message_id",
            aggfunc=lambda x: x.nunique(),
            fill_value=0
        ).reset_index().sort_values("processed_date")

        st.header("Select a Date to View Email Rates")
        available_dates = pivot["processed_date"].astype(str).tolist()
        selected_date_str = st.selectbox("Select Processed Date", options=available_dates)

        if selected_date_str:
            selected_date = pd.to_datetime(selected_date_str).date()
            df_date = df_filtered[df_filtered["processed_date"] == selected_date]

            processed_set_date = set(df_date[df_date["event"] == "processed"]["message_id"].unique())
            delivered_set_date = set(df_date[df_date["event"] == "delivered"]["message_id"].unique())
            open_set_date = set(df_date[df_date["event"] == "open"]["message_id"].unique())
            bounce_set_date = set(df_date[df_date["event"] == "bounce"]["message_id"].unique())

            total_processed_date = len(processed_set_date)
            total_delivered_date = len(delivered_set_date.intersection(processed_set_date))
            total_open_date = len(open_set_date.intersection(delivered_set_date))
            total_bounce_date = len(bounce_set_date.intersection(processed_set_date))

            delivery_rate_date = (total_delivered_date / total_processed_date * 100) if total_processed_date else 0
            open_rate_date = (total_open_date / total_delivered_date * 100) if total_delivered_date else 0
            bounce_rate_date = (total_bounce_date / total_processed_date * 100) if total_processed_date else 0

            st.subheader(f"Email Rates for {selected_date_str}")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Processed (Sent):** {total_processed_date}")
                st.markdown(f"**Delivered:** {total_delivered_date}")
                st.markdown(f"**Opened:** {total_open_date}")
            with col2:
                st.markdown(f"**Bounced:** {total_bounce_date}")
                st.markdown(f"**Delivery Rate:** {delivery_rate_date:.2f}%")
                st.markdown(f"**Open Rate:** {open_rate_date:.2f}%")
                st.markdown(f"**Bounce Rate:** {bounce_rate_date:.2f}%")

            date_summary_df = pd.DataFrame({
                "Metric": ["Total Processed", "Total Delivered", "Total Opened", "Total Bounced", "Delivery Rate (%)", "Open Rate (%)", "Bounce Rate (%)"],
                "Value": [total_processed_date, total_delivered_date, total_open_date, total_bounce_date, round(delivery_rate_date, 2), round(open_rate_date, 2), round(bounce_rate_date, 2)]
            })

            date_excel_data = to_excel(date_summary_df)
            st.download_button(
                label=f"Download {selected_date_str} Email Rates as Excel",
                data=date_excel_data,
                file_name=f"sendgrid_email_rates_{selected_date_str}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

else:
    st.sidebar.info("Please upload your SendGrid events CSV file to begin analysis.")
    st.info("Upload your SendGrid events CSV file using the sidebar uploader to start.")
