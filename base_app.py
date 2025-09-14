import json
import os
from typing import List, Dict, Any
from abc import ABC, abstractmethod

class BaseApp(ABC):
    def __init__(self, filename: str):
        self.filename = filename

    def save_data(self, data: List[Dict[str, Any]]) -> None:
        """Save data to JSON file with error handling"""
        try:
            with open(self.filename, 'w') as f:
                json.dump(data, f, indent=4)
        except IOError as e:
            raise Exception(f"Error saving data: {e}")

    def load_data(self) -> List[Dict[str, Any]]:
        """Load data from JSON file with error handling"""
        if not os.path.exists(self.filename):
            return []
        try:
            with open(self.filename, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading data: {e}")
            return []

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Abstract method to be implemented by child classes"""
        pass

    def backup_data(self, backup_filename: str) -> bool:
        """Additional method to demonstrate inheritance"""
        data = self.load_data()
        backup_file = f"backup_{backup_filename}"
        try:
            with open(backup_file, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            print(f"Backup failed: {e}")
            return False

class BaseNotesApp(BaseApp):
    """Extended base class for notes applications"""
    def __init__(self, filename: str):
        super().__init__(filename)
    
    def load_notes_data(self) -> Dict[str, Any]:
        """Load notes-specific data structure"""
        if not os.path.exists(self.filename):
            return {
                "folders": {"General": []},
                "tags": ["Important", "Work", "Personal"],
                "images": {}
            }
        try:
            with open(self.filename, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading notes data: {e}")
            return {
                "folders": {"General": []},
                "tags": ["Important", "Work", "Personal"],
                "images": {}
            }
    
    def save_notes_data(self, data: Dict[str, Any]) -> None:
        """Save notes-specific data structure"""
        try:
            with open(self.filename, 'w') as f:
                json.dump(data, f, indent=4)
        except IOError as e:
            raise Exception(f"Error saving notes data: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Default implementation for notes statistics"""
        data = self.load_notes_data()
        return {
            "total_folders": len(data.get("folders", {})),
            "total_notes": sum(len(notes) for notes in data.get("folders", {}).values()),
            "total_tags": len(data.get("tags", [])),
            "total_images": len(data.get("images", {}))
        }