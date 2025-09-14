import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime, timedelta
import threading
import platform
import os
from base_app import BaseApp
from typing import Dict, List, Set, Tuple, Any, Optional

# Conditionally import winsound
if platform.system() == "Windows":
    import winsound
else:
    winsound = None

class ReminderApp(BaseApp):
    def __init__(self, parent):
        super().__init__("reminder_data.json")
        
        # Store parent reference
        self.parent = parent
        
        # Encapsulation: Make data private
        self._active_reminders = self.load_data()
        self._sound_settings = self._initialize_sound_settings()
        
        self.setup_ui()
        self.update_reminders_list()

        self.reminder_thread = threading.Thread(target=self.check_reminders, daemon=True)
        self.reminder_thread.start()

    def _initialize_sound_settings(self) -> Dict[str, str]:
        """Initialize sound settings using dictionary"""
        return {
            "windows": "MessageBeep",
            "macos": "afplay /System/Library/Sounds/Ping.aiff",
            "linux": "paplay /usr/share/sounds/freedesktop/stereo/complete.oga"
        }

    # Encapsulation: Getter method for reminders
    def get_reminders(self) -> List[Dict]:
        return self._active_reminders.copy()

    # Encapsulation: Setter method for reminders
    def set_reminders(self, reminders: List[Dict]) -> None:
        self._active_reminders = reminders
        self.save_data(self._active_reminders)

#==================================================
# Setup Screen
#==================================================
    def setup_ui(self):
        self.style = ttk.Style()
        self.style.configure('TLabel', font=('Arial', 10))
        self.style.configure('TButton', font=('Arial', 10))
        self.style.configure('Header.TLabel', font=('Arial', 12, 'bold'))

        main = ttk.Frame(self.parent)
        main.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Set a New Reminder", style='Header.TLabel').pack(pady=(0, 10))

        frame = ttk.Frame(main)
        frame.pack(fill=tk.X, pady=5)

        ttk.Label(frame, text="Title:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.title_entry = ttk.Entry(frame, width=60)
        self.title_entry.grid(row=0, column=1, columnspan=3, padx=5, pady=2, sticky=tk.W)

        ttk.Label(frame, text="Message:").grid(row=1, column=0, sticky=tk.NW, padx=5, pady=2)
        
        # Create a frame for the text widget with scrollbar
        text_frame = ttk.Frame(frame)
        text_frame.grid(row=1, column=1, columnspan=3, padx=5, pady=2, sticky=tk.W+tk.E)
        
        # Bigger text area for description with scrollbar
        self.message_text = scrolledtext.ScrolledText(text_frame, width=60, height=4, wrap=tk.WORD)
        self.message_text.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Date (YYYY-MM-DD):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.date_entry = ttk.Entry(frame, width=12)
        self.date_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(frame, text="Time (HH:MM):").grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        self.time_entry = ttk.Entry(frame, width=10)
        self.time_entry.grid(row=2, column=3, sticky=tk.W, padx=5, pady=5)

        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.time_entry.insert(0, (datetime.now() + timedelta(minutes=5)).strftime("%H:%M"))

        ttk.Label(frame, text="Repeat:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.repeat_var = tk.StringVar(value="none")
        for i, val in enumerate(["none", "daily", "weekly"]):
            ttk.Radiobutton(frame, text=val.capitalize(), variable=self.repeat_var, value=val).grid(row=3, column=1+i, padx=5, pady=5)

        bframe = ttk.Frame(main)
        bframe.pack(pady=10)
        ttk.Button(bframe, text="Set Reminder", command=self.set_reminder).pack(side=tk.LEFT, padx=5)
        ttk.Button(bframe, text="Clear Fields", command=self.clear_fields).pack(side=tk.LEFT, padx=5)
        ttk.Button(bframe, text="Show Stats", command=self.show_statistics).pack(side=tk.LEFT, padx=5)

        # Configure treeview columns
        self.tree = ttk.Treeview(main, columns=("title", "message", "time", "repeat"), show="headings", height=8)
        for col, width in [("title", 120), ("message", 200), ("time", 120), ("repeat", 80)]:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=width)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=5)

        # Button frame for bottom buttons
        button_frame = ttk.Frame(main)
        button_frame.pack(pady=5)
        ttk.Button(button_frame, text="Delete Selected", command=self.delete_reminder).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Show Unique Types", command=self.show_unique_reminder_types).pack(side=tk.LEFT, padx=5)

#==================================================
# Main function
#==================================================
    def set_reminder(self):
        # Validate time format
        time_str = self.time_entry.get()
        if not self.validate_time_format(time_str):
            messagebox.showerror("Error", "Invalid time format. Please use HH:MM format (24-hour clock) with 2 digits for both hours and minutes")
            return
        
        try:
            reminder_time = datetime.strptime(self.date_entry.get() + " " + time_str, "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showerror("Error", "Invalid date/time format. Please use YYYY-MM-DD for date and HH:MM for time (24-hour format)")
            return

        if reminder_time < datetime.now():
            messagebox.showerror("Error", "Reminder must be in the future")
            return

        # Using tuple for reminder priority levels
        priority_levels: Tuple[str, ...] = ("low", "medium", "high")
        
        # Get message from text widget instead of entry
        message_content = self.message_text.get("1.0", tk.END).strip()
        
        reminder = {
            "title": self.title_entry.get().strip(),
            "message": message_content,
            "time": reminder_time.strftime("%Y-%m-%d %H:%M"),
            "repeat": self.repeat_var.get(),
            "priority": priority_levels[1]  # Default to medium priority
        }

        if not reminder["title"]:
            messagebox.showerror("Error", "Title required")
            return

        self._active_reminders.append(reminder)
        self.save_data(self._active_reminders)
        self.update_reminders_list()
        self.clear_fields()
        messagebox.showinfo("Success", "Reminder set successfully!")

    def validate_time_format(self, time_str):
        """Validate that time is in HH:MM format with 2 digits each"""
        try:
            if len(time_str) != 5 or time_str[2] != ":":
                return False
            
            hours, minutes = time_str.split(":")
            if not (hours.isdigit() and minutes.isdigit()):
                return False
            
            hours_num = int(hours)
            minutes_num = int(minutes)
            
            return 0 <= hours_num <= 23 and 0 <= minutes_num <= 59
        except:
            return False
        
    def update_reminders_list(self):
        self.tree.delete(*self.tree.get_children())
        for r in self._active_reminders:
            # Truncate long messages for display
            display_message = r["message"][:50] + "..." if len(r["message"]) > 50 else r["message"]
            self.tree.insert("", tk.END, values=(r["title"], display_message, r["time"], r["repeat"]))

    def clear_fields(self):
        """Clear all input fields - FIXED THIS FUNCTION"""
        self.title_entry.delete(0, tk.END)
        self.message_text.delete("1.0", tk.END)  # Clear text widget
        self.date_entry.delete(0, tk.END)
        self.time_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.time_entry.insert(0, (datetime.now() + timedelta(minutes=5)).strftime("%H:%M"))
        self.repeat_var.set("none")
        self.title_entry.focus()  # Set focus to title field

    def delete_reminder(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a reminder to delete")
            return
        
        # Using set for selected indices
        selected_indices: Set[int] = {self.tree.index(item) for item in selected}
        
        # Remove reminders in reverse order to avoid index issues
        for index in sorted(selected_indices, reverse=True):
            if index < len(self._active_reminders):
                del self._active_reminders[index]
        
        self.save_data(self._active_reminders)
        self.update_reminders_list()
        messagebox.showinfo("Success", f"Deleted {len(selected_indices)} reminder(s)")

    def check_reminders(self):
        while True:
            now = datetime.now()
            updated = False
            new_list = []

            for r in self._active_reminders:
                r_time = datetime.strptime(r["time"], "%Y-%m-%d %H:%M")
                if now >= r_time:
                    # Show notification directly instead of using after()
                    self.show_notification(r["title"], r["message"])
                    
                    # Using match expression for repeat handling (Python 3.10+)
                    match r["repeat"]:
                        case "daily":
                            r["time"] = (r_time + timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
                            new_list.append(r)
                        case "weekly":
                            r["time"] = (r_time + timedelta(weeks=1)).strftime("%Y-%m-%d %H:%M")
                            new_list.append(r)
                        case "none":
                            pass  # Don't readd one-time reminders
                        case _:
                            new_list.append(r)  # Keep unknown repeat types
                    
                    updated = True
                else:
                    new_list.append(r)

            if updated:
                self._active_reminders = new_list
                self.save_data(self._active_reminders)
                # Update the GUI in the main thread
                if hasattr(self, 'parent') and self.parent.winfo_exists():
                    self.parent.after(0, self.update_reminders_list)
            
            threading.Event().wait(10)  # Check every 10 seconds

    def show_notification(self, title: str, message: str):
        """Play sound based on platform using match expression"""
        # Using match expression for platform-specific sound handling
        match platform.system():
            case "Windows" if winsound:
                winsound.MessageBeep()
            case "Darwin":
                os.system(self._sound_settings["macos"])
            case "Linux":
                os.system(self._sound_settings["linux"])
            case _:
                print("Notification sound not supported on this platform")
        
        # Show the notification directly
        messagebox.showinfo(title, message)

    def show_unique_reminder_types(self):
        """Demonstrate set usage - show unique reminder types"""
        if not self._active_reminders:
            messagebox.showinfo("Info", "No reminders to analyze.")
            return
        
        # Using set to get unique reminder types
        unique_repeats: Set[str] = {reminder["repeat"] for reminder in self._active_reminders}
        unique_titles: Set[str] = {reminder["title"] for reminder in self._active_reminders}
        
        stats_text = f"Unique Repeat Types: {', '.join(unique_repeats)}\n"
        stats_text += f"Unique Titles: {len(unique_titles)} out of {len(self._active_reminders)} reminders"
        
        messagebox.showinfo("Unique Reminder Types", stats_text)

    def show_statistics(self):
        """Demonstrate tuple and dictionary usage - show reminder statistics"""
        if not self._active_reminders:
            messagebox.showinfo("Info", "No reminders to analyze.")
            return
        
        # Using tuple for statistics and dictionary for distribution
        total_reminders = len(self._active_reminders)
        
        # Repeat type distribution using dictionary
        repeat_distribution: Dict[str, int] = {}
        for reminder in self._active_reminders:
            repeat_type = reminder["repeat"]
            repeat_distribution[repeat_type] = repeat_distribution.get(repeat_type, 0) + 1
        
        # Create statistics tuple
        stats: Tuple[int, Dict[str, int]] = (total_reminders, repeat_distribution)
        
        # Display statistics
        stats_text = f"Total Reminders: {stats[0]}\n\nRepeat Type Distribution:\n"
        for repeat_type, count in stats[1].items():
            stats_text += f"{repeat_type.capitalize()}: {count} reminder(s)\n"
        
        messagebox.showinfo("Reminder Statistics", stats_text)

    # Override base class method to demonstrate inheritance
    def load_data(self) -> List[Dict]:
        """Enhanced load_data method with additional validation"""
        data = super().load_data()
        
        # Validate loaded data structure using match
        valid_data = []
        for item in data:
            match item:
                case {"title": str(), "message": str(), "time": str(), "repeat": str()}:
                    valid_data.append(item)
                case _:
                    print(f"Skipping invalid reminder data: {item}")
        
        return valid_data

    # Implement abstract method from BaseApp
    def get_statistics(self) -> Dict[str, Any]:
        """Return comprehensive statistics about the reminders"""
        if not self._active_reminders:
            return {"message": "No reminders available"}
        
        # Using dictionary for comprehensive statistics
        return {
            "total_reminders": len(self._active_reminders),
            "repeat_types": list({r["repeat"] for r in self._active_reminders}),
            "upcoming_reminders": [r for r in self._active_reminders 
                                  if datetime.strptime(r["time"], "%Y-%m-%d %H:%M") > datetime.now()],
            "repeat_distribution": {r["repeat"]: sum(1 for rem in self._active_reminders 
                                                   if rem["repeat"] == r["repeat"]) 
                                   for r in self._active_reminders}
        }

# if __name__ == "__main__":
#     root = tk.Tk()
#     app = ReminderApp(root)
#     root.mainloop()