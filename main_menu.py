import tkinter as tk
from tkinter import ttk
from gpa_calculator import GPACalculatorApp
from reminder_app import ReminderApp
from notes_organizer import NotesOrganizer

class StudentAssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Assistant App")
        self.root.geometry("1000x800")
        
        # Configure grid so everything expands
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        # Store reference to current app
        self.current_app = None
        self.current_app_frame = None
        
        # Create main menu frame
        self.main_menu_frame = ttk.Frame(self.root)
        self.main_menu_frame.grid(row=0, column=0, sticky="nsew")
        
        self.show_main_menu()

    def show_main_menu(self):
        """Display the main menu"""
        # Clear current app if any
        if self.current_app_frame:
            self.current_app_frame.destroy()
            self.current_app = None
        
        # Recreate main menu frame
        self.main_menu_frame = ttk.Frame(self.root)
        self.main_menu_frame.grid(row=0, column=0, sticky="nsew")
        
        self.main_menu_frame.rowconfigure(0, weight=1)
        self.main_menu_frame.columnconfigure(0, weight=1)

        # Center content
        center_frame = ttk.Frame(self.main_menu_frame)
        center_frame.pack(pady=20)
        
        ttk.Label(center_frame, text="TAR UMT Student Assistant", 
                 font=('Arial', 16, 'bold')).pack(pady=20)
        
        # Using tuple for fixed button texts
        button_texts = ("GPA Calculator", "Reminder App", "Notes Organizer")
        button_commands = (self.open_gpa_calculator, self.open_reminder_app, 
                           self.open_notes_organizer)

        # Using zip with tuples
        for text, command in zip(button_texts, button_commands):
            btn = ttk.Button(center_frame, text=text, command=command, width=25)
            btn.pack(pady=12)
            btn.configure(style="Big.TButton")
        
        # Configure button style
        style = ttk.Style()
        style.configure("Big.TButton", font=('Arial', 12), padding=10)

    def open_gpa_calculator(self):
        """Switch to GPA Calculator"""
        self.switch_to_app("GPA Calculator", GPACalculatorApp)

    def open_reminder_app(self):
        """Switch to Reminder App"""
        self.switch_to_app("Reminder App", ReminderApp)

    def open_notes_organizer(self):
        """Switch to Notes Organizer"""
        self.switch_to_app("Notes Organizer", NotesOrganizer)

    def switch_to_app(self, app_name, app_class):
        """Switch to a specific application"""
        # Clear main menu
        self.main_menu_frame.destroy()
        
        # Create container for the app
        self.current_app_frame = ttk.Frame(self.root)
        self.current_app_frame.grid(row=0, column=0, sticky="nsew")
        self.current_app_frame.rowconfigure(1, weight=1)
        self.current_app_frame.columnconfigure(0, weight=1)
        
        # Add back button
        back_button_frame = ttk.Frame(self.current_app_frame)
        back_button_frame.grid(row=0, column=0, sticky="ew", pady=5, padx=5)
        back_button_frame.columnconfigure(1, weight=1)
        
        
        ttk.Button(back_button_frame, text="← Back to Main Menu",
                   command=self.show_main_menu).grid(row=0, column=0, sticky="w")
        ttk.Label(back_button_frame, text=app_name,
                  font=('Arial', 14, 'bold')).grid(row=0, column=1, sticky="w", padx=20)
        
        # Create app container
        app_container = ttk.Frame(self.current_app_frame)
        app_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Initialize the application
        self.current_app = app_class(app_container)

    def on_closing(self):
        """Handle application closing"""
        if self.current_app:
            # Add any cleanup needed for current app
            pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = StudentAssistantApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()