import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from base_app import BaseApp
from typing import Dict, Set, Tuple, List, Any

class GPACalculatorApp(BaseApp):
    def __init__(self, parent):
        super().__init__("gpa_data.json")
        
        # Store parent reference
        self.parent = parent
        
        # Encapsulation to make the data private
        self._courses = self.load_data()
        self._grade_scales = self._initialize_grade_scales()
        
        self.setup_ui()
        self.update_courses_list()
        self.calculate_gpa()

    def _initialize_grade_scales(self) -> Dict[str, Dict[str, float]]:
        """Initialize grade scale dictionaries for different grading systems"""
        return {
            "4.0": {
                'A+': 4.00, 'A': 4.00, 'A-': 3.67,
                'B+': 3.33, 'B': 3.00, 'B-': 2.67,
                'C+': 2.33, 'C': 2.00, 'C-': 1.67,
                'D+': 1.33, 'D': 1.00, 'D-': 0.67,
                'F': 0.00
            },
            "100": {}  # Handled separately with match statement
        }

    # Encapsulation which is getter method for courses
    def get_courses(self) -> List[Dict]:
        return self._courses.copy()  # Return copy to prevent direct modification

    # Encapsulation for Setter method for courses
    def set_courses(self, courses: List[Dict]) -> None:
        self._courses = courses
        self.save_data(self._courses)
#==================================================
# Setup Screen
#==================================================
    def setup_ui(self):
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        self.style.configure('TButton', font=('Arial', 10))
        self.style.configure('Header.TLabel', font=('Arial', 12, 'bold'))

        # Use parent instead of creating new root
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.scale_frame = ttk.LabelFrame(self.main_frame, text="Grading Scale")
        self.scale_frame.pack(fill=tk.X, pady=5)

        self.scale_var = tk.StringVar(value="4.0")
        ttk.Radiobutton(self.scale_frame, text="4.0 Scale (A=4, B=3, C=2, D=1, F=0)", 
                       variable=self.scale_var, value="4.0").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(self.scale_frame, text="100 Scale (Percentage)", 
                       variable=self.scale_var, value="100").pack(side=tk.LEFT, padx=5)

        self.entry_frame = ttk.LabelFrame(self.main_frame, text="Add Course")
        self.entry_frame.pack(fill=tk.X, pady=5)

        ttk.Label(self.entry_frame, text="Course Name:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.course_entry = ttk.Entry(self.entry_frame, width=80)
        self.course_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.entry_frame, text="Grade:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.grade_entry = ttk.Entry(self.entry_frame, width=10)
        self.grade_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(self.entry_frame, text="Credit Hours:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.credit_entry = ttk.Entry(self.entry_frame, width=10)
        self.credit_entry.grid(row=0, column=5, padx=5, pady=5)

        self.add_button = ttk.Button(self.entry_frame, text="Add Course", command=self.add_course)
        self.add_button.grid(row=0, column=6, padx=5, pady=5)

        # Configure column weights for responsive layout
        self.entry_frame.columnconfigure(1, weight=1)  # Course name entry expands
        
        self.courses_frame = ttk.LabelFrame(self.main_frame, text="Your Courses")
        self.courses_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.courses_tree = ttk.Treeview(self.courses_frame, 
                                       columns=("course", "grade", "credits", "points"), 
                                       show="headings")
        for col in ["course", "grade", "credits", "points"]:
            self.courses_tree.heading(col, text=col.capitalize())
        self.courses_tree.pack(fill=tk.BOTH, expand=True)

        self.button_frame = ttk.Frame(self.courses_frame)
        self.button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(self.button_frame, text="Calculate GPA", command=self.calculate_gpa).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Delete Selected", command=self.delete_course).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Clear All", command=self.clear_courses).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Show Chart", command=self.show_chart).pack(side=tk.LEFT, padx=5)
        
        #buttons for collection demonstration
        ttk.Button(self.button_frame, text="Show Unique Courses", 
                  command=self.show_unique_courses).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Course Statistics", 
                  command=self.show_course_statistics).pack(side=tk.LEFT, padx=5)

        self.results_frame = ttk.LabelFrame(self.main_frame, text="Results")
        self.results_frame.pack(fill=tk.X, pady=5)

        self.total_credits_label = ttk.Label(self.results_frame, text="0")
        self.total_points_label = ttk.Label(self.results_frame, text="0")
        self.gpa_label = ttk.Label(self.results_frame, text="0.00", font=('Arial', 10, 'bold'))

        for i, text in enumerate(["Total Credits:", "Total Grade Points:", "GPA:"]):
            ttk.Label(self.results_frame, text=text).grid(row=0, column=2*i, padx=5, pady=5, sticky=tk.W)
            [self.total_credits_label, self.total_points_label, self.gpa_label][i].grid(row=0, column=2*i+1, padx=5, pady=5, sticky=tk.W)

#==================================================
# Main function
#==================================================
    
    def add_course(self):
        name = self.course_entry.get().strip()
        grade = self.grade_entry.get().upper().strip()
        credit = self.credit_entry.get().strip()

        if not name or not grade or not credit:
            messagebox.showerror("Error", "Please fill all fields")
            return

        try:
            credit = float(credit)
            if credit <= 0: 
                raise ValueError("Credit must be positive")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid credit: {e}")
            return

        points = self.calculate_grade_points(grade, self.scale_var.get())
        if points is None:
            messagebox.showerror("Error", "Invalid grade")
            return

        # Using tuple for course data structure
        course_data = (name, grade, credit, points)
        course_dict = {"name": name, "grade": grade, "credits": credit, "points": points}
        
        self._courses.append(course_dict)
        self.save_data(self._courses)
        self.update_courses_list()
        self.clear_entry_fields()

    def delete_course(self):
        selected = self.courses_tree.selection()
        if not selected:
            return
        index = self.courses_tree.index(selected[0])
        del self._courses[index]
        self.save_data(self._courses)
        self.update_courses_list()
        self.calculate_gpa()

    def clear_courses(self):
        # Add confirmation dialog
        if not messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all courses?"):
            return
        self._courses = []
        self.save_data(self._courses)
        self.update_courses_list()
        self.calculate_gpa()

    def update_courses_list(self):
        self.courses_tree.delete(*self.courses_tree.get_children())
        for c in self._courses:
            self.courses_tree.insert("", tk.END, 
                                   values=(c["name"], c["grade"], c["credits"], f"{c['points']:.2f}"))

    def clear_entry_fields(self):
        self.course_entry.delete(0, tk.END)
        self.grade_entry.delete(0, tk.END)
        self.credit_entry.delete(0, tk.END)
        self.course_entry.focus()

    def calculate_grade_points(self, grade: str, scale: str) -> float:
        """Calculate grade points using different collection types"""
        if scale == "4.0":
            # Using dictionary for grade mapping
            return self._grade_scales["4.0"].get(grade, None)
        elif scale == "100":
            try:
                grade_val = float(grade)
                # Using match statement (Python 3.10+)
                match grade_val:
                    case g if g >= 80: return 4.0
                    case g if g >= 75: return 3.67
                    case g if g >= 70: return 3.33
                    case g if g >= 65: return 3.00
                    case g if g >= 60: return 2.67
                    case g if g >= 55: return 2.33
                    case g if g >= 50: return 2.00
                    case _: return 0.0
            except ValueError:
                return None

    def calculate_gpa(self):
        total_credits = sum(c["credits"] for c in self._courses)
        total_points = sum(c["points"] * c["credits"] for c in self._courses)
        gpa = total_points / total_credits if total_credits else 0
        
        self.total_credits_label.config(text=f"{total_credits:.1f}")
        self.total_points_label.config(text=f"{total_points:.2f}")
        self.gpa_label.config(text=f"{gpa:.2f}")

    def show_unique_courses(self):
        """Demonstrate set usage - show unique course names"""
        if not self._courses:
            messagebox.showinfo("Info", "No courses to analyze.")
            return
        
        # Using set to get unique course names
        unique_courses: Set[str] = {course["name"] for course in self._courses}
        
        if len(unique_courses) == len(self._courses):
            messagebox.showinfo("Unique Courses", "All courses have unique names!")
        else:
            messagebox.showinfo("Unique Courses", 
                              f"Found {len(unique_courses)} unique courses out of {len(self._courses)} total courses.")

#==================================================
# Statistics
#==================================================            

    def show_course_statistics(self):
        """Demonstrate tuple and dictionary usage - show course statistics"""
        if not self._courses:
            messagebox.showinfo("Info", "No courses to analyze.")
            return
        
        # Using tuple for fixed statistics and dictionary for grade distribution
        total_courses = len(self._courses)
        total_credits = sum(c["credits"] for c in self._courses)
        
        # Grade distribution using dictionary
        grade_distribution: Dict[str, int] = {}
        for course in self._courses:
            grade = course["grade"]
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
        
        # Create statistics tuple
        stats: Tuple[int, float, Dict[str, int]] = (total_courses, total_credits, grade_distribution)
        
        # Display statistics
        stats_text = f"Total Courses: {stats[0]}\nTotal Credits: {stats[1]:.1f}\n\nGrade Distribution:\n"
        for grade, count in stats[2].items():
            stats_text += f"{grade}: {count} course(s)\n"
        
        messagebox.showinfo("Course Statistics", stats_text)

    def show_chart(self):
        if not self._courses:
            messagebox.showinfo("Info", "No data to display.")
            return
        
        names = [c["name"] for c in self._courses]
        points = [c["points"] for c in self._courses]
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(names, points, color='skyblue')
        plt.ylim(0, 4.1)
        plt.title("Grade Points by Course")
        plt.xlabel("Courses")
        plt.ylabel("Grade Points")
        
        for bar, val in zip(bars, points):
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05, 
                    f"{val:.2f}", ha='center')
        
        plt.tight_layout()
        plt.show()

    # Override base class method to demonstrate inheritance
    def load_data(self) -> List[Dict]:
        """Enhanced load_data method with additional validation"""
        data = super().load_data()
        
        # Validate loaded data structure
        valid_data = []
        for item in data:
            if (isinstance(item, dict) and 
                all(key in item for key in ['name', 'grade', 'credits', 'points'])):
                valid_data.append(item)
        
        return valid_data

    # Implement abstract method from BaseApp
    def get_statistics(self) -> Dict[str, Any]:
        """Return comprehensive statistics about the courses"""
        if not self._courses:
            return {"message": "No courses available"}
        
        total_credits = sum(c["credits"] for c in self._courses)
        total_points = sum(c["points"] * c["credits"] for c in self._courses)
        gpa = total_points / total_credits if total_credits else 0
        
        # Using dictionary for comprehensive statistics
        return {
            "total_courses": len(self._courses),
            "total_credits": total_credits,
            "total_points": total_points,
            "gpa": gpa,
            "course_names": [c["name"] for c in self._courses],
            "grade_distribution": {c["grade"]: sum(1 for course in self._courses if course["grade"] == c["grade"]) 
                                  for c in self._courses}
        }

#====================================
# Able this if want run independent
#====================================
# if __name__ == "__main__":
#     root = tk.Tk()
#     app = GPACalculatorApp(root)
#     root.mainloop()