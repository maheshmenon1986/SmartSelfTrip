import streamlit as st

def format_mismatch_messages(mismatches_df):
    """
    Used to display summary of mismatches in a readable format.
    """
    messages = []

    # Iterate through each row in the mismatches DataFrame
    for _, row in mismatches_df.iterrows():
        # Extract branch and transaction details
        branch_name = row['branch_name']
        branch_id = row['branch_id']
        city = row['city']

        # Format transaction totals with currency and comma separators
        excel_total = f"${row['transaction_total_excel']:,.2f}"
        db_total = f"${row['transaction_total_db']:,.2f}"

        # Create a formatted message summarizing the mismatch
        msg = f"Mismatch in **{city} ({branch_name} Branch {branch_id})**: Excel {excel_total} vs DB {db_total}"

        # Append the message to the list
        messages.append(msg)

    # Return the list of formatted mismatch messages
    return messages


def show_mismatch_chart(mismatches_df, full_df):
    """
    Displays either a success message and full table if no mismatches,
    or a warning with a mismatched branch summary.
    """

    # Case: No mismatches found
    if mismatches_df.empty:
        st.success("✅ All branches matched successfully.")
        st.markdown("#### 🔍 Full Table Comparison Report")
        st.dataframe(full_df)  # Show the full comparison data

    # Case: Mismatches found
    else:
        st.warning("⚠️ Mismatches detected")
        st.markdown("#### ⚠️ Mismatched Branches")
        st.dataframe(mismatches_df)  # Show only the mismatches
