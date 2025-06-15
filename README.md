# QR-Based Attendance System 🧾📸

A modern **Python desktop application** that allows users to **mark attendance using QR codes**, developed with **Tkinter, OpenCV, and pandas**. It features a user-friendly interface, real-time camera integration, and an admin panel for managing user data and attendance records.

---

## 🚀 Features

- 📷 **QR Code Scanning**: Mark attendance by scanning QR codes through your device's webcam.
- 📁 **CSV Storage**: Attendance and user data are stored in `.csv` files for easy access and portability.
- 📊 **Attendance Records Viewer**: Searchable and filterable attendance records.
- 🔐 **Admin Panel**: Secure admin login to add, update, or delete users.
- 🛠️ **Manage Users**: Add users with details like name, department, blood group, etc.
- 📤 **Export Records**: Print attendance reports to CSV.
- 🔔 **Beep Alerts**: Success or failure tones during scanning.

---

## 🧰 Technologies Used

- **Python 3.x**
- **OpenCV** for QR code detection
- **Tkinter** for GUI
- **pandas** for data handling
- **PIL (Pillow)** for image rendering
- **playsound / winsound** for audio feedback

---

## 🖥️ Screenshots

> _Add screenshots here in your repo for better presentation_
- Main Dashboard
- QR Scan Interface
- Attendance Viewer
- Admin Panel
- User Management

---

## 📦 Installation

1. **Clone the repository**:

```bash
git clone https://github.com/CodeWithVedang/Attendance_Systeam_Using_Python.git
cd Attendance_Systeam_Using_Python

2. Install dependencies:



pip install opencv-python pandas pillow playsound

> On Windows, winsound is built-in and used instead of playsound.



3. Run the application:



python main.py


---

👤 Admin Login

Username	Password

admin	admin123



---

🗂️ File Structure

📁 Attendance_Systeam_Using_Python/
├── main.py                  # Main application
├── users.csv                # Stores registered users
├── attendance.csv           # Stores attendance records
└── README.md                # Project documentation


---

✍️ How It Works

1. Admin adds users from the Manage Users tab.


2. Each user receives a unique registration number (used as QR data).


3. The user scans the QR code using the app to mark In-Time and Out-Time.


4. Admin can view, search, and export attendance records anytime.




---

📌 Notes

Make sure your webcam is connected and accessible.

Each QR code should contain the exact RegNo of a user.

The application does not generate QR codes — use any QR code generator with the RegNo.



---

📜 License

This project is licensed under the MIT License — feel free to use and modify.


---

🙌 Acknowledgements

Developed by Vedang Shelatkar

Guided by inspiration from real-world attendance systems

Thanks to the open-source Python community



---

⭐ Show Your Support

If you found this project helpful, consider giving it a ⭐ on GitHub!

---


