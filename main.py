import cv2 
import tkinter as tk 
from tkinter import ttk, messagebox, filedialog 
import pandas as pd 
from datetime import datetime 
import os
from PIL import Image, ImageTk
import platform

# For beep sounds
if platform.system() == "Windows":
    import winsound
else:
    from playsound import playsound  # pip install playsound

# Filenames for data persistence 
USER_FILE = "users.csv" 
ATTENDANCE_FILE = "attendance.csv" 

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def load_users():
    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE) 
    else: 
        df = pd.DataFrame(columns=["RegNo", "FirstName", "LastName", "Mobile", "BloodGroup", "Department", "Position"]) 
        df.to_csv(USER_FILE, index=False) 
        return df

def save_users(users_df):
    users_df.to_csv(USER_FILE, index=False)

def load_attendance():
    if os.path.exists(ATTENDANCE_FILE):
        df = pd.read_csv(ATTENDANCE_FILE) 
        if 'OutTime' in df.columns: 
            df['OutTime'] = df['OutTime'].astype('string') 
        else:
            df['OutTime'] = pd.Series(dtype='string')
        return df 
    else: 
        df = pd.DataFrame(columns=["RegNo", "Date", "InTime", "OutTime"]) 
        df['OutTime'] = df['OutTime'].astype('string') 
        df.to_csv(ATTENDANCE_FILE, index=False) 
        return df 

def save_attendance(att_df): 
    att_df.to_csv(ATTENDANCE_FILE, index=False) 

class AttendanceApp: 
    def __init__(self, root): 
        self.root = root
        self.root.title("QR Based Attendance System")
        self.root.geometry("900x600")
        self.root.resizable(False, False)

        # Apply ttk theme
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", font=("Arial", 10), padding=6)
        style.configure("Green.TButton", background="#4CAF50", foreground="white")
        style.configure("Blue.TButton", background="#2196F3", foreground="white")
        style.configure("Red.TButton", background="#F44336", foreground="white")
        style.configure("TLabel", font=("Arial", 12))
        style.configure("TEntry", padding=5)
        style.configure("Treeview", rowheight=25, font=("Arial", 10))
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"))
        style.map("Treeview", background=[('selected', '#2196F3')])

        self.users = load_users()
        self.attendance = load_attendance()
        self.is_admin_logged_in = False
        self.tab_manage = None

        self.create_widgets()

        self.cap = None
        self.scanning = False
        self.last_scanned_code = None 
        self.qr_cooldown_ms = 2000

    def create_widgets(self):
        self.tabControl = ttk.Notebook(self.root)
        self.tab_scan = ttk.Frame(self.tabControl) 
        self.tab_attendance = ttk.Frame(self.tabControl) 
        self.tab_admin = ttk.Frame(self.tabControl) 

        self.tabControl.add(self.tab_scan, text="Scan QR & Mark Attendance") 
        self.tabControl.add(self.tab_attendance, text="View Attendance Records") 
        self.tabControl.add(self.tab_admin, text="Admin Panel") 
        self.tabControl.pack(expand=1, fill="both", padx=10, pady=10)

        self.create_scan_tab()
        self.create_attendance_tab()
        self.create_admin_tab()

    # ----- Scan Tab -----
    def create_scan_tab(self): 
        frm = self.tab_scan 

        ttk.Label(frm, text="Scan QR to Mark Attendance", font=("Arial", 16, "bold")).pack(pady=15)

        self.scan_btn = ttk.Button(frm, text="Start Scan", command=self.toggle_scan, style="Green.TButton")
        self.scan_btn.pack(pady=10)

        self.scan_status = ttk.Label(frm, text="", font=("Arial", 12), foreground="green")
        self.scan_status.pack(pady=15)

        self.camera_label = ttk.Label(frm)
        self.camera_label.pack(pady=10)

    def toggle_scan(self):
        if self.scanning:
            self.stop_scan() 
        else: 
            self.start_scan() 

    def start_scan(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Cannot open camera")
            return
        self.scanning = True
        self.scan_btn.config(text="Stop Scan", style="Red.TButton")
        self.scan_status.config(text="Starting camera...")
        self.last_scanned_code = None
        self.update_frame()

    def stop_scan(self):
        self.scanning = False
        self.scan_btn.config(text="Start Scan", style="Green.TButton")
        self.scan_status.config(text="Scan stopped.")
        if self.cap:
            self.cap.release() 
        self.camera_label.config(image="") 

    def update_frame(self):
        if not self.scanning:
            return
        ret, frame = self.cap.read()
        if not ret:
            self.scan_status.config(text="Failed to read from camera")
            self.stop_scan()
            return

        detector = cv2.QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(frame)

        if data and data != self.last_scanned_code:
            self.last_scanned_code = data
            if self.mark_attendance(data.strip()):
                self.play_beep(True)
            else:
                self.play_beep(False)
 
            self.root.after(self.qr_cooldown_ms, self.reset_last_code) 

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
        im_pil = Image.fromarray(frame_rgb) 
        imgtk = ImageTk.PhotoImage(image=im_pil)
        self.camera_label.imgtk = imgtk
        self.camera_label.configure(image=imgtk)

        self.root.after(30, self.update_frame)

    def reset_last_code(self):
        self.last_scanned_code = None

    def mark_attendance(self, regno):
        if len(regno.split('-')) < 2:
            self.scan_status.config(text="Invalid QR format")
            return False

        if regno not in self.users['RegNo'].values:
            self.scan_status.config(text="User not registered")
            return False

        user = self.users[self.users['RegNo'] == regno].iloc[0]
        first_name = user['FirstName']
 
        now = datetime.now() 
        today = now.strftime("%Y-%m-%d") 
        current_time = now.strftime("%H:%M:%S") 

        user_today = self.attendance[(self.attendance['RegNo'] == regno) & (self.attendance['Date'] == today)]

        if user_today.empty:
            new_entry = {
                "RegNo": regno,
                "Date": today,
                "InTime": current_time,
                "OutTime": ""
            }
            self.attendance = pd.concat([self.attendance, pd.DataFrame([new_entry])], ignore_index=True)
            self.scan_status.config(text=f"Welcome {first_name} - Time: {current_time}")
        else:
            idxs = user_today[user_today['OutTime'] == ""].index 
            if len(idxs) > 0: 
                idx = idxs[0] 
                self.attendance.at[idx, 'OutTime'] = current_time 
                self.scan_status.config(text=f"Bye {first_name}, have a good day! - Time: {current_time}")
            else:
                self.scan_status.config(text="Attendance already marked twice today.")
                return False

        save_attendance(self.attendance)
        self.load_attendance_records()
        return True

    def play_beep(self, success=True):
        if platform.system() == "Windows":
            if success:
                winsound.Beep(1000, 150)
            else:
                winsound.Beep(400, 400) 
        else: 
            try: 
                if success: 
                    playsound('success.wav')
                else:
                    playsound('error.wav')
            except Exception:
                pass

    # ----- Attendance Records Tab ----- 
    def create_attendance_tab(self): 
        frm = self.tab_attendance

        ttk.Label(frm, text="Attendance Records", font=("Arial", 16, "bold")).pack(pady=15)

        searchfrm = ttk.Frame(frm) 
        searchfrm.pack(pady=10) 

        ttk.Label(searchfrm, text="Search by:").pack(side=tk.LEFT, padx=5)
        self.search_type = ttk.Combobox(searchfrm, values=["RegNo", "FirstName", "LastName", "Mobile"], state="readonly", width=15, font=("Arial", 10))
        self.search_type.current(0)
        self.search_type.pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(searchfrm, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_btn = ttk.Button(searchfrm, text="Search", command=self.search_attendance, style="Blue.TButton") 
        self.search_btn.pack(side=tk.LEFT, padx=5) 
        self.reset_btn = ttk.Button(searchfrm, text="Reset", command=self.load_attendance_records, style="TButton") 
        self.reset_btn.pack(side=tk.LEFT, padx=5)

        cols = ("RegNo", "FirstName", "LastName", "Date", "InTime", "OutTime") 
        self.att_tree = ttk.Treeview(frm, columns=cols, show="headings", height=15, selectmode="browse") 
        for c in cols:
            self.att_tree.heading(c, text=c)
            self.att_tree.column(c, width=120, anchor=tk.CENTER)
        self.att_tree.pack(pady=10, fill=tk.X, padx=20)

        # Alternating row colors
        self.att_tree.tag_configure("oddrow", background="#f0f0f0")
        self.att_tree.tag_configure("evenrow", background="#ffffff")

        self.print_btn = ttk.Button(frm, text="Print Attendance", command=self.print_attendance, style="TButton") 
        self.print_btn.pack(pady=10) 

        self.load_attendance_records()

    def load_attendance_records(self): 
        self.att_tree.delete(*self.att_tree.get_children()) 
        self.search_entry.delete(0, tk.END) 

        merged = self.attendance.merge(self.users[['RegNo', 'FirstName', 'LastName']], on='RegNo', how='left')
        merged = merged.sort_values(by=['Date', 'InTime'], ascending=[False, False])
        
        for i, (_, row) in enumerate(merged.iterrows()):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.att_tree.insert("", tk.END, values=(
                row['RegNo'], row['FirstName'], row['LastName'], row['Date'], row['InTime'], row['OutTime']), tags=tag)

    def search_attendance(self): 
        search_type = self.search_type.get()
        search_value = self.search_entry.get().strip() 

        if search_value == "": 
            messagebox.showwarning("Input needed", "Please enter a search value") 
            return 

        merged = self.attendance.merge(self.users[['RegNo', 'FirstName', 'LastName']], on='RegNo', how='left')
        
        if search_type == "RegNo":
            filtered = merged[merged['RegNo'] == search_value]
        elif search_type == "FirstName":
            filtered = merged[merged['FirstName'].str.lower() == search_value.lower()]
        elif search_type == "LastName":
            filtered = merged[merged['LastName'].str.lower() == search_value.lower()]
        elif search_type == "Mobile":
            filtered = merged[merged['RegNo'].isin(self.users[self.users['Mobile'] == search_value]['RegNo'])]

        self.att_tree.delete(*self.att_tree.get_children())

        if filtered.empty:
            messagebox.showinfo("No records", f"No attendance records found for {search_type}: {search_value}")
            return

        filtered = filtered.sort_values(by=['Date', 'InTime'], ascending=[False, False])
        
        for i, (_, row) in enumerate(filtered.iterrows()):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.att_tree.insert("", tk.END, values=(
                row['RegNo'], row['FirstName'], row['LastName'], row['Date'], row['InTime'], row['OutTime']), tags=tag)

    def print_attendance(self):
        items = self.att_tree.get_children()
        if not items:
            messagebox.showwarning("No records", "No attendance records to print")
            return

        records = []
        for item in items:
            values = self.att_tree.item(item, 'values')
            records.append({
                'RegNo': values[0],
                'FirstName': values[1],
                'LastName': values[2],
                'Date': values[3],
                'InTime': values[4],
                'OutTime': values[5]
            })
        
        fname = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save Attendance Records"
        )
        if fname: 
            pd.DataFrame(records).to_csv(fname, index=False) 
            messagebox.showinfo("Saved", f"Attendance records saved to:\n{fname}") 

    # ----- Admin Panel Tab -----
    def create_admin_tab(self):
        frm = self.tab_admin
        ttk.Label(frm, text="Admin Login", font=("Arial", 16, "bold")).pack(pady=15)

        loginfrm = ttk.Frame(frm)
        loginfrm.pack(pady=10)

        ttk.Label(loginfrm, text="Username").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.admin_username = ttk.Entry(loginfrm, width=30)
        self.admin_username.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(loginfrm, text="Password").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.admin_password = ttk.Entry(loginfrm, width=30, show="*")
        self.admin_password.grid(row=1, column=1, padx=10, pady=5)

        login_btn = ttk.Button(loginfrm, text="Login", command=self.admin_login, style="Blue.TButton")
        login_btn.grid(row=2, column=0, columnspan=2, pady=15)

        self.admin_status = ttk.Label(frm, text="Please login to access Manage Users", font=("Arial", 12))
        self.admin_status.pack(pady=15)

    def admin_login(self):
        username = self.admin_username.get().strip()
        password = self.admin_password.get().strip()

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            self.is_admin_logged_in = True
            self.admin_status.config(text="Admin logged in successfully!", foreground="green")
            if self.tab_manage is None:
                self.tab_manage = ttk.Frame(self.tabControl)
                self.tabControl.add(self.tab_manage, text="Manage Users")
                self.create_manage_tab()
            self.tabControl.select(self.tab_manage)
        else:
            self.admin_status.config(text="Invalid username or password", foreground="red")
            messagebox.showerror("Login Failed", "Invalid username or password")

    # ----- Manage Users Tab -----
    def create_manage_tab(self): 
        frm = self.tab_manage 

        ttk.Label(frm, text="Manage Users", font=("Arial", 16, "bold")).pack(pady=15) 

        formfrm = ttk.Frame(frm) 
        formfrm.pack(pady=10, padx=10) 

        labels = ["First Name", "Last Name", "Mobile Number", "Blood Group", "Department", "Position"] 
        self.user_vars = {} 

        for i, label in enumerate(labels):
            ttk.Label(formfrm, text=label).grid(row=i, column=0, sticky=tk.W, padx=10, pady=5)
            entry = ttk.Entry(formfrm, width=30)
            entry.grid(row=i, column=1, padx=10, pady=5)
            self.user_vars[label] = entry

        btnfrm = ttk.Frame(frm)
        btnfrm.pack(pady=10)

        add_btn = ttk.Button(btnfrm, text="Add User", command=self.add_user, style="Green.TButton")
        add_btn.pack(side=tk.LEFT, padx=5)

        modify_btn = ttk.Button(btnfrm, text="Modify User", command=self.modify_user, style="Blue.TButton")
        modify_btn.pack(side=tk.LEFT, padx=5)

        delete_btn = ttk.Button(btnfrm, text="Delete User", command=self.delete_user, style="Red.TButton")
        delete_btn.pack(side=tk.LEFT, padx=5)

        self.user_tree = ttk.Treeview(frm, columns=["RegNo", "FirstName", "LastName", "Mobile", "BloodGroup", "Department", "Position"],
                                      show="headings", height=10, selectmode="browse")
        for col in self.user_tree["columns"]: 
            self.user_tree.heading(col, text=col) 
            self.user_tree.column(col, width=120, anchor=tk.CENTER) 
        self.user_tree.pack(pady=10, fill=tk.X, padx=20)

        # Alternating row colors
        self.user_tree.tag_configure("oddrow", background="#f0f0f0")
        self.user_tree.tag_configure("evenrow", background="#ffffff")

        # Bind double-click to populate fields for modification
        self.user_tree.bind("<Double-1>", self.populate_user_fields)

        self.load_users_table()

    def load_users_table(self): 
        self.user_tree.delete(*self.user_tree.get_children()) 
        for i, (_, row) in enumerate(self.users.iterrows()): 
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.user_tree.insert("", tk.END, values=(
                row["RegNo"], row["FirstName"], row["LastName"], row["Mobile"], row["BloodGroup"], row["Department"], 
                row["Position"]), tags=tag)

    def populate_user_fields(self, event):
        selected = self.user_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a user to modify")
            return

        item = self.user_tree.item(selected[0])
        values = item['values']
        
        self.user_vars["First Name"].delete(0, tk.END)
        self.user_vars["First Name"].insert(0, values[1])
        self.user_vars["Last Name"].delete(0, tk.END)
        self.user_vars["Last Name"].insert(0, values[2])
        self.user_vars["Mobile Number"].delete(0, tk.END)
        self.user_vars["Mobile Number"].insert(0, values[3])
        self.user_vars["Blood Group"].delete(0, tk.END)
        self.user_vars["Blood Group"].insert(0, values[4])
        self.user_vars["Department"].delete(0, tk.END)
        self.user_vars["Department"].insert(0, values[5])
        self.user_vars["Position"].delete(0, tk.END)
        self.user_vars["Position"].insert(0, values[6])

    def add_user(self): 
        if not self.is_admin_logged_in:
            messagebox.showerror("Access Denied", "Admin login required to manage users")
            return

        fn = self.user_vars["First Name"].get().strip() 
        ln = self.user_vars["Last Name"].get().strip()
        mob = self.user_vars["Mobile Number"].get().strip()
        bg = self.user_vars["Blood Group"].get().strip()
        dept = self.user_vars["Department"].get().strip()
        pos = self.user_vars["Position"].get().strip()

        if not (fn and ln and mob and bg and dept and pos): 
            messagebox.showwarning("Input Error", "Please fill all fields") 
            return

        year = datetime.now().year
        regno = f"{year}-{fn}_{ln}_{dept}"

        if regno in self.users['RegNo'].values: 
            messagebox.showerror("Duplicate Entry", "User with this registration number already exists") 
            return 

        new_user = {
            "RegNo": regno,
            "FirstName": fn,
            "LastName": ln, 
            "Mobile": mob, 
            "BloodGroup": bg, 
            "Department": dept, 
            "Position": pos 
        } 

        self.users = pd.concat([self.users, pd.DataFrame([new_user])], ignore_index=True) 
        save_users(self.users) 

        messagebox.showinfo("Success", f"User added with RegNo: {regno}") 

        for var in self.user_vars.values(): 
            var.delete(0, tk.END) 

        self.load_users_table()

    def modify_user(self):
        if not self.is_admin_logged_in:
            messagebox.showerror("Access Denied", "Admin login required to manage users")
            return

        selected = self.user_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a user to modify")
            return

        item = self.user_tree.item(selected[0])
        old_regno = item['values'][0]

        fn = self.user_vars["First Name"].get().strip() 
        ln = self.user_vars["Last Name"].get().strip()
        mob = self.user_vars["Mobile Number"].get().strip()
        bg = self.user_vars["Blood Group"].get().strip()
        dept = self.user_vars["Department"].get().strip()
        pos = self.user_vars["Position"].get().strip()

        if not (fn and ln and mob and bg and dept and pos): 
            messagebox.showwarning("Input Error", "Please fill all fields") 
            return

        year = datetime.now().year
        new_regno = f"{year}-{fn}_{ln}_{dept}"

        # Check for duplicate RegNo (excluding the current user)
        if new_regno != old_regno and new_regno in self.users['RegNo'].values:
            messagebox.showerror("Duplicate Entry", "User with this registration number already exists")
            return

        # Update user details
        idx = self.users.index[self.users['RegNo'] == old_regno].tolist()[0]
        self.users.at[idx, 'RegNo'] = new_regno
        self.users.at[idx, 'FirstName'] = fn
        self.users.at[idx, 'LastName'] = ln
        self.users.at[idx, 'Mobile'] = mob
        self.users.at[idx, 'BloodGroup'] = bg
        self.users.at[idx, 'Department'] = dept
        self.users.at[idx, 'Position'] = pos

        save_users(self.users)
        messagebox.showinfo("Success", f"User with RegNo: {new_regno} updated successfully")

        for var in self.user_vars.values(): 
            var.delete(0, tk.END) 

        self.load_users_table()

    def delete_user(self):
        if not self.is_admin_logged_in:
            messagebox.showerror("Access Denied", "Admin login required to manage users")
            return

        selected = self.user_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a user to delete")
            return

        item = self.user_tree.item(selected[0])
        regno = item['values'][0]

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete user with RegNo: {regno}?"):
            self.users = self.users[self.users['RegNo'] != regno]
            save_users(self.users)
            messagebox.showinfo("Success", f"User with RegNo: {regno} deleted successfully")
            self.load_users_table()
            for var in self.user_vars.values(): 
                var.delete(0, tk.END)

if __name__ == "__main__": 
    root = tk.Tk() 
    app = AttendanceApp(root) 
    root.mainloop()