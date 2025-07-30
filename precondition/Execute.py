import subprocess
import sys

def install_or_upgrade(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package])
    except subprocess.CalledProcessError:
        print(f"Failed to install/upgrade {package}. Please install it manually.")

packages = [
    "streamlit",
    "pandas",
    "openpyxl",
    "sqlalchemy",
    "rapidfuzz",
    "streamlit-date-picker",
    "folium"  # Added folium to the list
]

for pkg in packages:
    install_or_upgrade(pkg)

print("All packages checked and upgraded if needed.")

# Now you can import folium after running this script
try:
    import folium
    print("Folium imported successfully!")
except ImportError:
    print("Folium could not be imported. Please check your installation.")