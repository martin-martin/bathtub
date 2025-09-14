#!/usr/bin/env python3
"""
Bathtub Database Manager CLI
A command-line interface for managing bathtub database entries.
Allows searching, viewing, and updating bathtub records.
"""

import sqlite3
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


class BathtubDatabaseManager:
    """CLI manager for bathtub database operations."""
    
    # Field definitions with their types and descriptions
    FIELDS = {
        'name': {'type': str, 'description': 'Bathtub name', 'required': True},
        'top_length': {'type': float, 'description': 'Top length (cm)', 'required': True},
        'bottom_length': {'type': float, 'description': 'Bottom length (cm)', 'required': True},
        'width': {'type': float, 'description': 'Width (cm)', 'required': True},
        'height': {'type': float, 'description': 'Height (cm)', 'required': True},
        'side_incline_degrees': {'type': float, 'description': 'Side incline (degrees)', 'required': True},
        'liters': {'type': str, 'description': 'Capacity in liters', 'required': False},
        'created_at': {'type': str, 'description': 'Creation timestamp', 'required': False, 'readonly': True}
    }
    
    def __init__(self, db_path: str = "bathtubs.db"):
        """Initialize the database manager."""
        self.db_path = db_path
        self._check_database()
    
    def _check_database(self) -> None:
        """Check if database exists and is accessible."""
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"Database file '{self.db_path}' not found!")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("SELECT 1 FROM bathtubs LIMIT 1")
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Cannot access database: {e}")
    
    def search_entries(self, search_term: str = None, search_by_id: bool = False) -> List[Dict[str, Any]]:
        """
        Search for bathtub entries.
        
        Args:
            search_term: Term to search for
            search_by_id: If True, search by ID; otherwise search by name
            
        Returns:
            List of matching entries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if search_term is None:
                # Return all entries
                cursor = conn.execute("""
                    SELECT id, name, top_length, bottom_length, width, height, 
                           side_incline_degrees, liters, created_at
                    FROM bathtubs 
                    ORDER BY name
                """)
            elif search_by_id:
                # Search by ID
                try:
                    entry_id = int(search_term)
                    cursor = conn.execute("""
                        SELECT id, name, top_length, bottom_length, width, height, 
                               side_incline_degrees, liters, created_at
                        FROM bathtubs 
                        WHERE id = ?
                    """, (entry_id,))
                except ValueError:
                    return []
            else:
                # Search by name (case-insensitive)
                cursor = conn.execute("""
                    SELECT id, name, top_length, bottom_length, width, height, 
                           side_incline_degrees, liters, created_at
                    FROM bathtubs 
                    WHERE name LIKE ?
                    ORDER BY name
                """, (f"%{search_term}%",))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_entry_by_id(self, entry_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific entry by ID."""
        entries = self.search_entries(str(entry_id), search_by_id=True)
        return entries[0] if entries else None
    
    def update_field(self, entry_id: int, field: str, new_value: Any) -> bool:
        """
        Update a specific field for an entry.
        
        Args:
            entry_id: ID of the entry to update
            field: Field name to update
            new_value: New value for the field
            
        Returns:
            True if update was successful, False otherwise
        """
        if field not in self.FIELDS:
            raise ValueError(f"Unknown field: {field}")
        
        if self.FIELDS[field].get('readonly', False):
            raise ValueError(f"Field '{field}' is read-only")
        
        # Validate the value type
        expected_type = self.FIELDS[field]['type']
        try:
            if expected_type == float:
                new_value = float(new_value)
            elif expected_type == int:
                new_value = int(new_value)
            elif expected_type == str:
                new_value = str(new_value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid value for field '{field}': {e}")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    f"UPDATE bathtubs SET {field} = ? WHERE id = ?",
                    (new_value, entry_id)
                )
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Database error: {e}")
    
    def display_entries(self, entries: List[Dict[str, Any]], show_all: bool = False) -> None:
        """Display entries in a formatted table."""
        if not entries:
            print("No entries found.")
            return
        
        if show_all:
            # Full display with all fields
            print(f"\n{'ID':<4} {'Name':<20} {'Top':<8} {'Bottom':<8} {'Width':<8} {'Height':<8} {'Incline':<8} {'Liters':<10} {'Created':<12}")
            print("-" * 100)
            
            for entry in entries:
                created_dt = datetime.fromisoformat(entry['created_at'])
                print(f"{entry['id']:<4} {entry['name']:<20} "
                      f"{entry['top_length']:<8.1f} {entry['bottom_length']:<8.1f} "
                      f"{entry['width']:<8.1f} {entry['height']:<8.1f} "
                      f"{entry['side_incline_degrees']:<8.2f} {entry['liters']:<10} "
                      f"{created_dt.strftime('%Y-%m-%d'):<12}")
        else:
            # Compact display
            print(f"\n{'ID':<4} {'Name':<25} {'Liters':<10}")
            print("-" * 40)
            
            for entry in entries:
                print(f"{entry['id']:<4} {entry['name']:<25} {entry['liters']:<10}")
    
    def interactive_search(self) -> Optional[Dict[str, Any]]:
        """Interactive search and selection of an entry."""
        print("\n🔍 Search for bathtub entry")
        print("1. Search by name")
        print("2. Search by ID")
        print("3. Show all entries")
        
        while True:
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == '1':
                search_term = input("Enter name to search for: ").strip()
                if not search_term:
                    print("❌ Please enter a search term.")
                    continue
                entries = self.search_entries(search_term)
                break
            elif choice == '2':
                try:
                    entry_id = int(input("Enter ID: ").strip())
                    entries = self.search_entries(str(entry_id), search_by_id=True)
                    break
                except ValueError:
                    print("❌ Please enter a valid ID number.")
                    continue
            elif choice == '3':
                entries = self.search_entries()
                break
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
        
        if not entries:
            print("❌ No entries found.")
            return None
        
        self.display_entries(entries, show_all=True)
        
        if len(entries) == 1:
            return entries[0]
        
        # Multiple entries found, let user choose
        while True:
            try:
                entry_id = int(input(f"\nEnter ID of the entry to modify (1-{max(e['id'] for e in entries)}): "))
                selected_entry = next((e for e in entries if e['id'] == entry_id), None)
                if selected_entry:
                    return selected_entry
                else:
                    print(f"❌ No entry found with ID {entry_id}")
            except ValueError:
                print("❌ Please enter a valid ID number.")
    
    def interactive_field_selection(self, entry: Dict[str, Any]) -> Tuple[str, Any]:
        """Interactive field selection and value input."""
        print(f"\n�� Editing entry: {entry['name']} (ID: {entry['id']})")
        print("\nAvailable fields to modify:")
        
        # Show editable fields
        editable_fields = [(name, info) for name, info in self.FIELDS.items() 
                          if not info.get('readonly', False)]
        
        for i, (field_name, field_info) in enumerate(editable_fields, 1):
            current_value = entry.get(field_name, 'N/A')
            print(f"{i:2d}. {field_name:<20} - {field_info['description']:<30} (Current: {current_value})")
        
        while True:
            try:
                choice = int(input(f"\nSelect field to modify (1-{len(editable_fields)}): "))
                if 1 <= choice <= len(editable_fields):
                    field_name, field_info = editable_fields[choice - 1]
                    break
                else:
                    print(f"❌ Please enter a number between 1 and {len(editable_fields)}")
            except ValueError:
                print("❌ Please enter a valid number.")
        
        # Get new value
        current_value = entry.get(field_name, '')
        field_type = field_info['type']
        
        print(f"\nCurrent value: {current_value}")
        
        while True:
            new_value = input(f"Enter new value for {field_name}: ").strip()
            
            if not new_value and not field_info.get('required', False):
                new_value = 'N/A'
                break
            
            if not new_value and field_info.get('required', False):
                print("❌ This field is required. Please enter a value.")
                continue
            
            # Validate the value
            try:
                if field_type == float:
                    new_value = float(new_value)
                elif field_type == int:
                    new_value = int(new_value)
                elif field_type == str:
                    new_value = str(new_value)
                break
            except ValueError:
                print(f"❌ Invalid value. Expected type: {field_type.__name__}")
        
        return field_name, new_value
    
    def run_interactive(self) -> None:
        """Run the interactive CLI."""
        print("�� Bathtub Database Manager")
        print("=" * 50)
        
        while True:
            print("\nOptions:")
            print("1. Search and modify entry")
            print("2. View all entries")
            print("3. Exit")
            
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == '1':
                entry = self.interactive_search()
                if entry:
                    try:
                        field, new_value = self.interactive_field_selection(entry)
                        
                        # Confirm the change
                        print(f"\n📋 Change summary:")
                        print(f"   Entry: {entry['name']} (ID: {entry['id']})")
                        print(f"   Field: {field}")
                        print(f"   Old value: {entry.get(field, 'N/A')}")
                        print(f"   New value: {new_value}")
                        
                        confirm = input("\nConfirm this change? (y/N): ").strip().lower()
                        if confirm in ['y', 'yes']:
                            if self.update_field(entry['id'], field, new_value):
                                print("✅ Entry updated successfully!")
                            else:
                                print("❌ Failed to update entry.")
                        else:
                            print("❌ Change cancelled.")
                    except Exception as e:
                        print(f"❌ Error: {e}")
            
            elif choice == '2':
                entries = self.search_entries()
                self.display_entries(entries, show_all=True)
            
            elif choice == '3':
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")


def main():
    """Main function with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Bathtub Database Manager CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Interactive mode
  %(prog)s --search "Polypex"        # Search by name
  %(prog)s --id 1                    # Search by ID
  %(prog)s --list                    # List all entries
  %(prog)s --update 1 liters "N/A"   # Update specific field
        """
    )
    
    parser.add_argument('--db', default='bathtubs.db', 
                       help='Database file path (default: bathtubs.db)')
    parser.add_argument('--search', help='Search entries by name')
    parser.add_argument('--id', type=int, help='Search entry by ID')
    parser.add_argument('--list', action='store_true', help='List all entries')
    parser.add_argument('--update', nargs=3, metavar=('ID', 'FIELD', 'VALUE'),
                       help='Update field: ID FIELD VALUE')
    
    args = parser.parse_args()
    
    try:
        manager = BathtubDatabaseManager(args.db)
        
        if args.update:
            # Direct update mode
            entry_id, field, value = args.update
            try:
                if manager.update_field(entry_id, field, value):
                    print(f"✅ Updated entry {entry_id}, field '{field}' to '{value}'")
                else:
                    print(f"❌ No entry found with ID {entry_id}")
            except Exception as e:
                print(f"❌ Error: {e}")
                sys.exit(1)
        
        elif args.search:
            # Search mode
            entries = manager.search_entries(args.search)
            manager.display_entries(entries, show_all=True)
        
        elif args.id:
            # ID search mode
            entries = manager.search_entries(str(args.id), search_by_id=True)
            manager.display_entries(entries, show_all=True)
        
        elif args.list:
            # List all mode
            entries = manager.search_entries()
            manager.display_entries(entries, show_all=True)
        
        else:
            # Interactive mode
            manager.run_interactive()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()