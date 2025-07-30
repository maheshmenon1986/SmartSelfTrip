from pathlib import Path

def delete_xls_files(folder_path):
    folder = Path(folder_path)
    print(f"🔍 Checking folder: {folder.resolve()}")

    if not folder.exists():
        print("❌ Folder does not exist!")
        return

    if not folder.is_dir():
        print("❌ Path is not a directory!")
        return

    deleted_any = False
    print("📂 Files in directory:")
    for file in folder.iterdir():
        print(f"   - {file.name} (suffix: {file.suffix})")  # Show all files

        if file.is_file() and file.suffix.lower() == '.xlsx':
            try:
                file.unlink()
                print(f"✅ Deleted: {file.name}")
                deleted_any = True
            except Exception as e:
                print(f"❌ Failed to delete {file.name}: {e}")

    if not deleted_any:
        print("⚠️ No .xlsx files found to delete.")

if __name__ == "__main__":
    # Use absolute path to test folder
    delete_xls_files(r"/data")
