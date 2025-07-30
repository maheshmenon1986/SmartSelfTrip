from pathlib import Path
import streamlit as st


class FileUploader:
    def __init__(self):
        # Resolve project root based on current file location
        self.project_root = Path(__file__).resolve().parent.parent  # Points to .../reconciliationwithai
        self.data_folder = self.project_root / "data"              # Points to .../reconciliationwithai/data

        # Ensure data folder exists
        self.data_folder.mkdir(parents=True, exist_ok=True)

        # Optional: Show resolved path in Streamlit for debugging
        st.write(f"📁 Upload folder resolved to: {self.data_folder}")

    def show_file_uploader(self):
        uploaded_file = st.file_uploader(
            "Excel file missing for validation. Please upload the Excel file to proceed:",
            type=["xlsx"],
            key="upload_excel"
        )

        if uploaded_file is not None:
            # Save the uploaded file into the /data folder
            new_file_path = self.data_folder / uploaded_file.name

            # Write uploaded content to disk
            with open(new_file_path, "wb") as f:
                f.write(uploaded_file.read())

            # Save file path to session state
            st.session_state["excel_path"] = str(new_file_path)

            # Show success message
            st.success(f"✅ File `{uploaded_file.name}` uploaded successfully!")

            # Add message to session history
            if "history" not in st.session_state:
                st.session_state["history"] = []

            st.session_state.history.append({
                "role": "bot",
                "message": f"📄 File `{uploaded_file.name}` uploaded successfully. Please select the date for validation."
            })

            st.session_state.needs_upload = False
            st.write(f"📝 File saved to: {new_file_path}")

            # ✅ Return file so it can be processed further in app.py
            return uploaded_file

        return None