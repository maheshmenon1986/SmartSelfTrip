import streamlit as st
import pandas as pd
import sys

# Add these lines at the very beginning of your script, after imports
st.write(f"Python executable: {sys.executable}")
st.write(f"Streamlit version (reported by Streamlit itself): {st.__version__}")
try:
    # Attempt to access MarkdownColumn to confirm if it's there
    _ = st.column_config.MarkdownColumn
    st.write("`st.column_config.MarkdownColumn` is available!")
except AttributeError:
    st.error("`st.column_config.MarkdownColumn` is NOT available in this Streamlit version.")
# End of temporary diagnostic code

# ... rest of your Streamlit application code ...

# For example, your dataframe definition and st.dataframe call
# itinerary_df = pd.DataFrame(itinerary_details)
# ...
# st.dataframe(
#     styled_df,
#     use_container_width=True,
#     column_config={
#         "Instructions": st.column_config.MarkdownColumn( # This line is causing the error
#             "Instructions",
#             width="large",
#         ),
#         # ... other column configs
#     }
# )