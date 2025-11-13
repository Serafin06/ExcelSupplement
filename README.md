# ExcelSupplement

A desktop tool written in **Python** that automates the process of updating or supplementing Excel files with production data.  
The application supports both **command-line** and **graphical user interface (GUI)** modes.

---

## 🚀 Features

- Reads and supplements Excel files with data from the database.  
- Filters data by a **user-selected date range**.  
- Excludes records produced **before** the selected period.  
- Supports **index search** using the `LIKE %index%` pattern.  
- Allows adding a **custom description** about how the Excel file should look.  
- Simple **GUI** – no technical knowledge required.  
- Optionally runs from the command line for automation or scripting.  
- Can be converted into a standalone `.exe` file for easy distribution.

---

## 🖥️ GUI Overview

The GUI provides a user-friendly interface for non-technical users.

**Functions:**
1. Select the Excel file to process.  
2. Choose a start and end date for the data range.  
3. Enter a short text or description of how the final Excel file should look.  
4. Click **Run** to execute the process.

The script then loads data for the selected period, fills the Excel file accordingly, and saves the updated result.

---

## ⚙️ Configuration

You can adjust the following parameters in the script:
- **Database connection** (if applicable):  
  update your credentials and connection string in the configuration section or `.env` file.
- **Default date range**:  
  change the default start and end dates used by the GUI.
- **Excel output path**:  
  modify the export directory or output file name.
- **Search behavior**:  
  the script uses `LIKE %index%` for flexible searching.  
  You can adjust this query if you need exact matches or case sensitivity.

---

## ▶️ Running the Application

### 🧩 Option 1: Run from Python

Make sure Python 3.9+ is installed.

pip install -r requirements.txt
python main.py
If you want to use the GUI:

python excel_gui.py
### 💾 Option 2: Build a Standalone EXE
If you want to distribute the tool as a Windows executable:

pip install pyinstaller
pyinstaller --onefile --noconsole excel_gui.py
This will create an .exe file inside the dist/ directory.

---
## 🧰 Requirements
Python 3.9+

pandas

openpyxl

tkcalendar

tkinter (included with Python)

pyinstaller (optional, for building an .exe)

Install all dependencies with:

pip install -r requirements.txt

---
## 🧑‍💻 Customization
To adapt the tool to your own setup:

Replace database queries in the script with your own logic.

Modify the Excel formatting section to match your preferred layout.

Adjust the default paths and filenames.

Customize the GUI text and labels if needed.

---
## 📂 Example Workflow
Launch the GUI:

nginx
python excel_gui.py
Choose the Excel file you want to supplement.

Select a start and end date for the data.

Add an optional description (e.g., "Monthly report layout – columns reordered").

Click Run.

The script updates the file and saves it in the same folder or export directory.

---
## 📄 License
MIT License — feel free to use and modify for personal or commercial purposes.

---
## ✨ Author
ExcelSupplement by Serafin06
For issues or contributions, please open a ticket in the Issues tab.

ExcelSupplement – a simple but powerful tool for synchronizing Excel data with SQL production databases and generating automated analytical reports.
