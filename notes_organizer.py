import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from tkinter.scrolledtext import ScrolledText
from tkinter import font as tkfont
import json
import os
import webbrowser
from datetime import datetime
from PIL import Image, ImageTk
import shutil
import base64
from io import BytesIO
from typing import Dict, List, Set, Tuple, Any, Optional
import platform
# Import from base_app
from base_app import BaseNotesApp

# Conditionally import winsound
if platform.system() == "Windows":
    import winsound
else:
    winsound = None

class NotesOrganizer(BaseNotesApp):  # Changed inheritance
    def __init__(self, parent):
        super().__init__("notes_data.json")
        
        # Store parent reference
        self.parent = parent
        
        # Encapsulation: Make data private
        self._notes = self.load_notes_data()
        self._image_dir = "notes_images"
        
        self.setup_ui()
        self.current_note_id = None
        self.current_folder = None
        self._last_clicked_tag = None

        # Image storage setup
        self.setup_image_storage()

    # Encapsulation: Getter for notes
    def get_notes(self) -> Dict[str, Any]:
        return self._notes.copy()
    
    # Encapsulation: Setter for notes
    def set_notes(self, notes: Dict[str, Any]) -> None:
        self._notes = notes
        self.save_notes_data(self._notes)  # Use parent method

    def load_data(self) -> Dict[str, Any]:
        """Override parent method for compatibility"""
        return self.load_notes_data()

    def save_data(self, data: Dict[str, Any]) -> None:
        """Override parent method for compatibility"""
        self.save_notes_data(data)

#==================================================
# Setup Screen
#==================================================
    def setup_ui(self):
        """Set up the main UI components with improved layout."""
        # Configure styles
        style = ttk.Style()
        style.configure("TButton", padding=5)
        style.configure("TLabel", padding=5)
        style.configure("Header.TLabel", font=("Arial", 14, "bold"))
        style.configure("Subheader.TLabel", font=("Arial", 12, "bold"))

        main_container = ttk.Frame(self.parent)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="Notes Organizer", style="Header.TLabel").pack(side=tk.LEFT)
        ttk.Button(header_frame, text="Backup", command=self.create_backup).pack(side=tk.RIGHT, padx=5)
        ttk.Button(header_frame, text="Statistics", command=self.show_note_statistics).pack(side=tk.RIGHT, padx=5)

        # Main content area
        content_pane = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        content_pane.pack(fill=tk.BOTH, expand=True)

        # Left Panel (Folders & Tags)
        left_panel = ttk.Frame(content_pane, width=250)
        content_pane.add(left_panel, weight=1)

        # Folder Management
        folder_frame = ttk.LabelFrame(left_panel, text="Folders", padding=10)
        folder_frame.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)

        # Folder buttons
        folder_btn_frame = ttk.Frame(folder_frame)
        folder_btn_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(folder_btn_frame, text="+ Add Folder", command=self.add_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(folder_btn_frame, text="- Delete", command=self.delete_folder).pack(side=tk.LEFT, padx=2)

        self.folder_tree = ttk.Treeview(folder_frame, selectmode="browse", height=8)
        folder_scroll = ttk.Scrollbar(folder_frame, orient=tk.VERTICAL, command=self.folder_tree.yview)
        self.folder_tree.configure(yscrollcommand=folder_scroll.set)
        
        self.folder_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        folder_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.folder_tree.bind("<<TreeviewSelect>>", self.load_folder_notes)

        # Tag Management
        tag_frame = ttk.LabelFrame(left_panel, text="Tags", padding=10)
        tag_frame.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)

        # Tag buttons
        tag_btn_frame = ttk.Frame(tag_frame)
        tag_btn_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(tag_btn_frame, text="+ Add Tag", command=self.add_tag).pack(side=tk.LEFT, padx=2)
        ttk.Button(tag_btn_frame, text="Apply", command=self.apply_tags).pack(side=tk.LEFT, padx=2)
        ttk.Button(tag_btn_frame, text="Unapply", command=self.unapply_tags).pack(side=tk.LEFT, padx=2)
        ttk.Button(tag_btn_frame, text="- Delete", command=self.delete_tag).pack(side=tk.LEFT, padx=2)

        self.tag_listbox = tk.Listbox(tag_frame, selectmode=tk.MULTIPLE, height=6)
        tag_scroll = ttk.Scrollbar(tag_frame, orient=tk.VERTICAL, command=self.tag_listbox.yview)
        self.tag_listbox.configure(yscrollcommand=tag_scroll.set)
        
        self.tag_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tag_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tag_listbox.configure(exportselection=False)  # keeps selection even if focus changes
        self.tag_listbox.bind("<ButtonRelease-1>", self._on_tag_click)

        # Right Panel (Notes & Editor)
        right_panel = ttk.Frame(content_pane)
        content_pane.add(right_panel, weight=3)

        # Notes list section
        notes_section = ttk.Frame(right_panel)
        notes_section.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(notes_section, text="Notes in Folder:", style="Subheader.TLabel").pack(side=tk.LEFT)
        
        # Search and note actions
        search_note_frame = ttk.Frame(notes_section)
        search_note_frame.pack(side=tk.RIGHT)
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_note_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=2)
        ttk.Button(search_note_frame, text="Search", command=self.search_notes).pack(side=tk.LEFT, padx=2)
        ttk.Button(search_note_frame, text="+ New Note", command=self.new_note).pack(side=tk.LEFT, padx=2)
        ttk.Button(search_note_frame, text="- Delete", command=self.delete_note).pack(side=tk.LEFT, padx=2)

        # Notes list with improved visibility
        notes_list_frame = ttk.Frame(right_panel)
        notes_list_frame.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)

        self.notes_listbox = tk.Listbox(notes_list_frame, font=("Arial", 10), height=8)
        notes_scroll = ttk.Scrollbar(notes_list_frame, orient=tk.VERTICAL, command=self.notes_listbox.yview)
        self.notes_listbox.configure(yscrollcommand=notes_scroll.set)
        
        self.notes_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        notes_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.notes_listbox.bind("<<ListboxSelect>>", self.load_note)

        # Note Editor section
        editor_section = ttk.LabelFrame(right_panel, text="Note Editor", padding=10)
        editor_section.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)

        # Toolbar with clearer icons
        toolbar_frame = ttk.Frame(editor_section)
        toolbar_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(toolbar_frame, text="💾 Save", command=self.save_note).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="B", command=lambda: self.format_text("bold")).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="I", command=lambda: self.format_text("italic")).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="📷 Image", command=self.insert_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="🔗 Link", command=self.insert_link).pack(side=tk.LEFT, padx=2)

        # Text Editor with improved visibility
        self.note_editor = ScrolledText(
            editor_section,
            wrap=tk.WORD,
            font=tkfont.Font(family="Arial", size=12),
            padx=10,
            pady=10,
            width=60,
            height=15
        )
        self.note_editor.pack(fill=tk.BOTH, expand=True)

        # Status Bar with more information
        status_frame = ttk.Frame(right_panel)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_bar = ttk.Label(status_frame, text="Ready | Select a folder and note to begin", relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X)
        
        # Load initial data
        self.refresh_folders()
        self.refresh_tags()

    def create_backup(self):
        """Create a backup of the notes data"""
        backup_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if backup_path:
            try:
                # Copy the current data file to the backup location
                if os.path.exists("notes_data.json"):
                    import shutil
                    shutil.copy2("notes_data.json", backup_path)
                    messagebox.showinfo("Success", f"Backup created at: {backup_path}")
                else:
                    # If no data file exists, create an empty backup with notes structure
                    with open(backup_path, 'w') as f:
                        json.dump({
                            "folders": {"General": []},
                            "tags": ["Important", "Work", "Personal"],
                            "images": {}
                        }, f, indent=4)
                    messagebox.showinfo("Success", f"Empty backup created at: {backup_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Backup failed: {str(e)}")

    def _on_tag_click(self, event):
        try:
            idx = self.tag_listbox.nearest(event.y)
            self._last_clicked_tag = self.tag_listbox.get(idx)
        except Exception:
            self._last_clicked_tag = None

    # ======================
    # FOLDER MANAGEMENT
    # ======================
    def refresh_folders(self):
        """Reload folders into the Treeview."""
        self.folder_tree.delete(*self.folder_tree.get_children())
        for folder in self._notes["folders"]:
            self.folder_tree.insert("", tk.END, text=folder, values=(len(self._notes["folders"][folder]),))
        
        # Configure column if not already configured
        if not self.folder_tree['columns']:
            self.folder_tree['columns'] = ('count',)
            self.folder_tree.heading('count', text='Notes')
            self.folder_tree.column('count', width=50, anchor='center')
        
        # Select first folder by default
        if self.folder_tree.get_children():
            self.folder_tree.selection_set(self.folder_tree.get_children()[0])
            self.load_folder_notes()

    def add_folder(self):
        """Add a new folder."""
        folder_name = simpledialog.askstring("New Folder", "Enter folder name:")
        if folder_name and folder_name not in self._notes["folders"]:
            self._notes["folders"][folder_name] = []
            self.save_data(self._notes)
            self.refresh_folders()
            self.status_bar.config(text=f"Created new folder: {folder_name}")

    def delete_folder(self):
        """Delete selected folder."""
        selected = self.folder_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a folder to delete")
            return
        
        # Using match expression for folder operations 
        folder = self.folder_tree.item(selected)["text"]
        
        match folder:
            case "General":
                messagebox.showerror("Error", "Cannot delete the General folder!")
            case _:
                if messagebox.askyesno("Confirm", f"Delete folder '{folder}' and all {len(self._notes['folders'][folder])} notes inside?"):
                    # Using set to track affected images for cleanup
                    images_to_remove: Set[str] = set()
                    
                    for note in self._notes["folders"][folder]:
                        images_to_remove.update(note.get("images", []))
                    
                    # Remove images from storage
                    for img_id in images_to_remove:
                        if img_id in self._notes["images"]:
                            try:
                                os.remove(self._notes["images"][img_id])
                            except:
                                pass
                            del self._notes["images"][img_id]
                    
                    del self._notes["folders"][folder]
                    self.save_data(self._notes)
                    self.refresh_folders()
                    self.status_bar.config(text=f"Deleted folder: {folder}")

    def load_folder_notes(self, event=None):
        """Load notes from selected folder."""
        selected = self.folder_tree.selection()
        if not selected:
            return
        self.current_folder = self.folder_tree.item(selected)["text"]
        self.notes_listbox.delete(0, tk.END)
        
        folder_notes = self._notes["folders"][self.current_folder]
        for note in folder_notes:
            # Show note title with modification date
            mod_date = note.get("last_modified", "").split()[0]  # Get just the date part
            display_text = f"{note['title']} ({mod_date})"
            self.notes_listbox.insert(tk.END, display_text)
        
        # Reset current note selection
        self.current_note_id = None
        
        # Clear editor
        self.note_editor.delete(1.0, tk.END)
        
        # Clear tag selection
        self.tag_listbox.selection_clear(0, tk.END)
        
        self.status_bar.config(text=f"Folder: {self.current_folder} | {len(folder_notes)} notes")

    # ======================
    # TAG MANAGEMENT
    # ======================
    def refresh_tags(self):
        """Reload tags into the Listbox."""
        self.tag_listbox.delete(0, tk.END)
        for tag in self._notes["tags"]:
            self.tag_listbox.insert(tk.END, tag)

    def add_tag(self):
        """Add a new tag."""
        tag = simpledialog.askstring("New Tag", "Enter tag name:")
        if tag and tag not in self._notes["tags"]:
            self._notes["tags"].append(tag)
            self.save_data(self._notes)
            self.refresh_tags()
            self.status_bar.config(text=f"Added new tag: {tag}")

    def apply_tags(self):
        """Apply selected tags to current note."""
        if self.current_note_id is None or not self.current_folder:
            messagebox.showinfo("Info", "Please select a note first")
            return
        
        # Using set for selected tags to avoid duplicates
        selected_tags: Set[str] = {self.tag_listbox.get(i) for i in self.tag_listbox.curselection()}
        note = self._notes["folders"][self.current_folder][self.current_note_id]
        
        # Add selected tags to note (avoid duplicates)
        current_tags = set(note.get("tags", []))
        note["tags"] = list(current_tags.union(selected_tags))
        
        self.save_data(self._notes)
        self.status_bar.config(text=f"Applied {len(selected_tags)} tags to current note")

    def unapply_tags(self):
        """Remove selected tags from current note, preferring the last clicked tag if toggled off."""
        if self.current_note_id is None or not self.current_folder:
            messagebox.showinfo("Info", "Please select a note first")
            return

        note = self._notes["folders"][self.current_folder][self.current_note_id]
        note_tags = set(note.get("tags", []))

        # What the UI currently reports as selected
        selected_indices = self.tag_listbox.curselection()
        selected_set = {self.tag_listbox.get(i) for i in selected_indices}

        # Also consider the active item (keyboard/mouse focus) and our last clicked tag
        active_idx = self.tag_listbox.index(tk.ACTIVE) if self.tag_listbox.size() else None
        active_tag = self.tag_listbox.get(active_idx) if active_idx is not None else None
        last_clicked = getattr(self, "_last_clicked_tag", None)

        # Default: remove selected tags that are actually on the note
        tags_to_remove = selected_set & note_tags

        # If user clicked a tag to toggle it OFF, it won't be in selected_set.
        # Prefer removing that single clicked tag.
        if last_clicked and (last_clicked in note_tags) and (last_clicked not in selected_set):
            tags_to_remove = {last_clicked}
        elif active_tag and (active_tag in note_tags) and (active_tag not in selected_set):
            tags_to_remove = {active_tag}

        if not tags_to_remove:
            self.status_bar.config(text="No matching tags to remove.")
            return

        note["tags"] = list(note_tags - tags_to_remove)
        self.save_data(self._notes)
        self.update_tag_selection()
        self.status_bar.config(text=f"Removed: {', '.join(sorted(tags_to_remove))}")


    def delete_tag(self):
        """Delete selected tag from all notes."""
        selected_indices = self.tag_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("Info", "Please select a tag to delete")
            return
        
        tags_to_delete = [self.tag_listbox.get(i) for i in selected_indices]
        
        if messagebox.askyesno("Confirm", f"Delete {len(tags_to_delete)} tag(s) from all notes?"):
            # Remove tag from global tag list
            for tag in tags_to_delete:
                if tag in self._notes["tags"]:
                    self._notes["tags"].remove(tag)
            
            # Remove tag from all notes
            for folder in self._notes["folders"]:
                for note in self._notes["folders"][folder]:
                    if "tags" in note:
                        note["tags"] = [t for t in note["tags"] if t not in tags_to_delete]
            
            self.save_data(self._notes)
            self.refresh_tags()
            
            # Update tag selection for current note
            if self.current_note_id is not None:
                self.update_tag_selection()
            
            self.status_bar.config(text=f"Deleted {len(tags_to_delete)} tag(s)")

    def update_tag_selection(self):
        """Update tag listbox selection based on current note's tags."""
        if self.current_note_id is None or not self.current_folder:
            return
        
        note = self._notes["folders"][self.current_folder][self.current_note_id]
        note_tags = set(note.get("tags", []))
        
        # Clear current selection
        self.tag_listbox.selection_clear(0, tk.END)
        
        # Select tags that are applied to the current note
        for i, tag in enumerate(self._notes["tags"]):
            if tag in note_tags:
                self.tag_listbox.selection_set(i)

    def show_unique_stats(self):
        """Demonstrate set usage - show unique statistics"""
        if not self._notes["folders"]:
            messagebox.showinfo("Info", "No data to analyze.")
            return
        
        # Using sets for unique operations
        all_tags: Set[str] = set(self._notes["tags"])
        used_tags: Set[str] = set()
        total_notes = 0
        
        for folder_notes in self._notes["folders"].values():
            total_notes += len(folder_notes)
            for note in folder_notes:
                used_tags.update(note.get("tags", []))
        
        unused_tags = all_tags - used_tags
        
        stats_text = f"Total Notes: {total_notes}\n"
        stats_text += f"Total Folders: {len(self._notes['folders'])}\n"
        stats_text += f"Total Tags: {len(all_tags)}\n"
        stats_text += f"Used Tags: {len(used_tags)}\n"
        stats_text += f"Unused Tags: {len(unused_tags)}\n"
        
        if unused_tags:
            stats_text += f"\nUnused Tags: {', '.join(sorted(unused_tags))}"
        
        messagebox.showinfo("Unique Statistics", stats_text)

    # ======================
    # NOTE MANAGEMENT
    # ======================
    def new_note(self):
        """Create a new note."""
        if not self.current_folder:
            messagebox.showerror("Error", "Select a folder first!")
            return
        
        title = simpledialog.askstring("New Note", "Enter note title:")
        if title:
            new_note = {
                "title": title,
                "content": "",
                "tags": [],
                "images": [],
                "links": [],
                "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "last_modified": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            self._notes["folders"][self.current_folder].append(new_note)
            self.save_data(self._notes)
            self.refresh_folders()
            self.load_folder_notes()
            self.notes_listbox.selection_clear(0, tk.END)
            self.notes_listbox.selection_set(tk.END)
            self.notes_listbox.activate(tk.END)
            self.load_note()
            self.status_bar.config(text=f"Created new note: {title}")

    def load_note(self, event=None):
        """Load selected note into editor."""
        selected = self.notes_listbox.curselection()
        if not selected or not self.current_folder:
            return
        
        self.current_note_id = selected[0]
        note = self._notes["folders"][self.current_folder][self.current_note_id]
        
        # Clear editor and reset formatting tags
        self.note_editor.delete(1.0, tk.END)
        
        # Clear all existing tags
        for tag in self.note_editor.tag_names():
            self.note_editor.tag_delete(tag)
        
        # Set up text formatting tags
        self.setup_formatting_tags()
        
        # Insert content
        content = note.get("content", "")
        self.note_editor.insert(tk.END, note["content"])

        # Restore format (convert back to Text index using saved character offsets)
        for fmt in note.get("formats", []):
            tag = fmt.get("tag")
            try:
                start = int(fmt.get("start", 0))
                end = int(fmt.get("end", 0))
            except Exception:
                continue

        # Check and trim the range to prevent out-of-bounds or invalidity
            if start >= len(content) or start >= end:
                continue
            end = min(end, len(content))

            start_index = self.offset_to_text_index(start)
            end_index = self.offset_to_text_index(end)

            try:
                self.note_editor.tag_add(tag, start_index, end_index)
            except Exception:
                pass
        
        # Display images and links as visual elements (not in content)
        self.display_media_elements(note)
        
        # Update tag selection based on current note
        self.update_tag_selection()
        
        # Update status
        self.status_bar.config(text=f"Editing: {note['title']} | Last modified: {note['last_modified']}")

    def setup_formatting_tags(self):
        base_font = tkfont.Font(self.note_editor, self.note_editor.cget("font"))

        # Bold only
        bold_font = base_font.copy()
        bold_font.configure(weight="bold")
        self.note_editor.tag_configure("bold", font=bold_font)

        # Italic only
        italic_font = base_font.copy()
        italic_font.configure(slant="italic")
        self.note_editor.tag_configure("italic", font=italic_font)

        # Bold + Italic
        bold_italic_font = base_font.copy()
        bold_italic_font.configure(weight="bold", slant="italic")
        self.note_editor.tag_configure("bold_italic", font=bold_italic_font)

        # Link tag (color and underline fixed)
        self.note_editor.tag_configure("link", foreground="blue", underline=1)


    def display_media_elements(self, note):
        """Display images and links as visual elements below the content."""
        
        # 1. Delete the old media elements (from --- Media Elements --- to the end of the article)
        full_text = self.note_editor.get("1.0", tk.END)
        if "--- Media Elements ---" in full_text:
            start_index = self.note_editor.search("--- Media Elements ---", "1.0", tk.END)
            if start_index:
                self.note_editor.delete(start_index, tk.END)

        # Add a separator
        if note.get("images") or note.get("links"):
            self.note_editor.insert(tk.END, "\n\n--- Media Elements ---\n")
        
        # Display images
        for img_id in note.get("images", []):
            if img_id in self._notes["images"]:
                img_path = self._notes["images"][img_id]
                self.note_editor.insert(tk.END, f"\n[Image: {os.path.basename(img_path)}]", "image")
        
        # Display links
        for link in note.get("links", []):
            self.note_editor.insert(tk.END, f"\n[Link: {link}]", "link")
            # Make links clickable
            self.note_editor.tag_bind("link", "<Button-1>", 
                                    lambda e, url=link: webbrowser.open(url))

    def save_note(self):
        """Save current note with formatting."""
        if self.current_note_id is None or not self.current_folder:
            messagebox.showinfo("Info", "No note selected to save")
            return
        
        note = self._notes["folders"][self.current_folder][self.current_note_id]
        
        # Get content but exclude media elements (everything after the separator)
        content = self.note_editor.get(1.0, tk.END)
        if "--- Media Elements ---" in content:
            content = content.split("--- Media Elements ---")[0].strip()
        
        content_length = len(content)
        # Collect formatting information (bold, italic, etc.) as character offsets
        formats = []
        for tag in ("bold", "italic", "bold_italic"):
            ranges = self.note_editor.tag_ranges(tag)
            for i in range(0, len(ranges), 2):
                start_idx = ranges[i]
                end_idx = ranges[i + 1]

            # Convert a Text index to a character offset
                start_offset = self.text_index_to_offset(start_idx)
                end_offset = self.text_index_to_offset(end_idx)

            # If the starting position is after media, skip
                if start_offset >= content_length:
                    continue

            # Truncate to the end of content (to ensure the range does not exceed the limit)
                end_offset = min(end_offset, content_length)

                if start_offset < end_offset:
                    formats.append({
                        "tag": tag,
                        "start": start_offset,
                        "end": end_offset
                    })
        # Save the text content only (without media elements)
        note["content"] = content
        note["formats"] = formats
        note["last_modified"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.save_data(self._notes)
        self.status_bar.config(text=f"Note saved at {note['last_modified']}")

    def delete_note(self):
        """Delete selected note."""
        if self.current_note_id is None or not self.current_folder:
            messagebox.showinfo("Info", "Please select a note to delete")
            return
        
        note = self._notes["folders"][self.current_folder][self.current_note_id]
        if messagebox.askyesno("Confirm", f"Delete note '{note['title']}'?"):
            # Remove associated images
            for img_id in note["images"]:
                if img_id in self._notes["images"]:
                    img_path = self._notes["images"][img_id]
                    try:
                        os.remove(img_path)
                    except:
                        pass
                    del self._notes["images"][img_id]
            
            del self._notes["folders"][self.current_folder][self.current_note_id]
            self.save_data(self._notes)
            self.refresh_folders()
            self.load_folder_notes()
            self.note_editor.delete(1.0, tk.END)
            self.current_note_id = None
            self.status_bar.config(text=f"Deleted note: {note['title']}")

    def show_note_statistics(self):
        """Demonstrate tuple and dictionary usage - show note statistics"""
        if not self._notes["folders"]:
            messagebox.showinfo("Info", "No notes to analyze.")
            return
        
        # Using tuple for statistics and dictionary for detailed info
        total_notes = sum(len(notes) for notes in self._notes["folders"].values())
        total_images = len(self._notes["images"])
        
        # Using set for unique tags across all notes
        all_used_tags: Set[str] = set()
        for folder_notes in self._notes["folders"].values():
            for note in folder_notes:
                all_used_tags.update(note.get("tags", []))
        
        stats_text = f"Total Notes: {total_notes}\n"
        stats_text += f"Total Folders: {len(self._notes['folders'])}\n"
        stats_text += f"Total Tags: {len(self._notes['tags'])}\n"
        stats_text += f"Used Tags: {len(all_used_tags)}\n"
        stats_text += f"Total Images: {total_images}\n"
        
        # Add folder breakdown
        stats_text += "\nNotes by Folder:\n"
        for folder, notes in self._notes["folders"].items():
            stats_text += f"  {folder}: {len(notes)} notes\n"
        
        messagebox.showinfo("Notes Statistics", stats_text)

    # ======================
    # SEARCH FUNCTIONALITY
    # ======================
    def search_notes(self):
        """Search notes across all folders."""
        query = self.search_var.get().lower()
        if not query:
            messagebox.showinfo("Info", "Please enter a search term")
            return
        
        results = []
        for folder in self._notes["folders"]:
            for note in self._notes["folders"][folder]:
                if (query in note["title"].lower() or 
                    query in note["content"].lower() or 
                    any(query in tag.lower() for tag in note["tags"])):
                    results.append(f"{folder} > {note['title']}")
        
        # Using match expression for search results handling
        match len(results):
            case 0:
                messagebox.showinfo("Search Results", "No matching notes found.")
            case 1:
                messagebox.showinfo("Search Results", f"Found 1 note:\n{results[0]}")
            case count if count <= 10:
                messagebox.showinfo("Search Results", f"Found {count} notes:\n" + "\n".join(results))
            case _:
                messagebox.showinfo("Search Results", f"Found {len(results)} notes. First 10:\n" + "\n".join(results[:10]))

    # ======================
    # RICH TEXT FEATURES
    # ======================
    def format_text(self, style):
        try:
            start = "sel.first"
            end = "sel.last"
            tags = self.note_editor.tag_names(start)

            is_bold = "bold" in tags or "bold_italic" in tags
            is_italic = "italic" in tags or "bold_italic" in tags

            # Switch the selected style
            if style == "bold":
                is_bold = not is_bold
            elif style == "italic":
                is_italic = not is_italic

            # Save the link tag to avoid deletion
            has_link = "link" in tags

            # Remove old tags
            self.note_editor.tag_remove("bold", start, end)
            self.note_editor.tag_remove("italic", start, end)
            self.note_editor.tag_remove("bold_italic", start, end)

            # Apply the correct tag
            if is_bold and is_italic:
                self.note_editor.tag_add("bold_italic", start, end)
            elif is_bold:
                self.note_editor.tag_add("bold", start, end)
            elif is_italic:
                self.note_editor.tag_add("italic", start, end)

            # Restore link tag
            if has_link:
                self.note_editor.tag_add("link", start, end)

        except tk.TclError:
            pass

    def setup_image_storage(self):
        """Create image directory if it doesn't exist."""
        if not os.path.exists(self._image_dir):
            os.makedirs(self._image_dir)

    def text_index_to_offset(self, index) -> int:
        """Convert a Text widget index ('1.0' / ​​'2.5' etc.) to a character offset (int) from the beginning. """
        try:
            # Length of text from the beginning to index = offset
            return len(self.note_editor.get("1.0", index))
        except Exception:
            return 0

    def offset_to_text_index(self, offset: int) -> str:
        """Convert a character offset into an index string recognizable by Text (e.g. '1.0 + 15 chars')."""
        return self.note_editor.index(f"1.0 + {int(offset)} chars")
        
    def insert_image(self):
        """Insert an image into the note with automatic storage."""
        if self.current_note_id is None:
            messagebox.showerror("Error", "Select or create a note first!")
            return
        
        filepath = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        
        if not filepath:
            return
            
        try:
            # Generate unique filename
            filename = f"img_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(filepath)}"
            save_path = os.path.join(self._image_dir, filename)
            
            # Copy image to application's image directory
            shutil.copy2(filepath, save_path)
            
            # Store relative path in JSON
            image_id = f"img_{len(self._notes['images']) + 1}"
            self._notes['images'][image_id] = save_path
            
            # Add to current note
            note = self._notes["folders"][self.current_folder][self.current_note_id]
            note["images"].append(image_id)
            
            # Save the note
            self.save_data(self._notes)
            
            # Display Media Elements directly at the end of the current editor
            self.display_media_elements(note)
            
            self.status_bar.config(text=f"Image added: {os.path.basename(save_path)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to insert image: {str(e)}")
            
    def insert_link(self):
        """Insert a hyperlink into the note."""
        url = simpledialog.askstring("Insert Link", "Enter URL:")
        if not url:
            return
        
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        # Add to current note
        if self.current_note_id is not None:
            note = self._notes["folders"][self.current_folder][self.current_note_id]
            note["links"].append(url)
            self.save_data(self._notes)
            
            # Display Media Elements directly at the end of the current editor
            self.display_media_elements(note)
            
            self.status_bar.config(text=f"Link added: {url}")

    def get_statistics(self) -> Dict[str, Any]:
        """Override abstract method with detailed notes statistics"""
        if not self._notes:
            return {"message": "No notes available"}
        
        # Using dictionary for comprehensive statistics
        total_notes = sum(len(notes) for notes in self._notes["folders"].values())
        total_images = len(self._notes["images"])
        
        # Using set for unique tags across all notes
        all_used_tags: Set[str] = set()
        for folder_notes in self._notes["folders"].values():
            for note in folder_notes:
                all_used_tags.update(note.get("tags", []))
        
        return {
            "total_folders": len(self._notes["folders"]),
            "total_notes": total_notes,
            "total_tags": len(self._notes["tags"]),
            "used_tags": len(all_used_tags),
            "unused_tags": len(set(self._notes["tags"]) - all_used_tags),
            "total_images": total_images,
            "folders_list": list(self._notes["folders"].keys())
        }
    
#====================================
# Able this if want run independent
#====================================
# if __name__ == "__main__":
#     root = tk.Tk()
#     app = NotesOrganizer(root)
#     root.mainloop()