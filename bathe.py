#!/usr/bin/env python3
"""
Bathtub Measurement CLI App
A Textual-based application for managing bathtub measurements and calculating side inclines.
"""

import sqlite3
import math
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Input, Button, Static, DataTable, Label
from textual.screen import Screen
from textual.binding import Binding
from textual.validation import Number


class Database:
    """SQLite database handler for bathtub measurements."""
    
    def __init__(self, db_path: str = "bathtubs.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize the database with the bathtubs table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bathtubs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    top_length REAL NOT NULL,
                    bottom_length REAL NOT NULL,
                    width REAL NOT NULL,
                    height REAL NOT NULL,
                    side_incline_degrees REAL NOT NULL,
                    liters TEXT DEFAULT 'N/A',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    def add_bathtub(self, name: str, top_length: float, bottom_length: float, 
                    width: float, height: float, side_incline: float, liters: str = "N/A") -> int:
        """Add a new bathtub to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO bathtubs (name, top_length, bottom_length, width, height, side_incline_degrees, liters)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, top_length, bottom_length, width, height, side_incline, liters))
            return cursor.lastrowid
    
    def get_all_bathtubs(self) -> List[Tuple]:
        """Retrieve all bathtubs from the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT id, name, top_length, bottom_length, width, height, 
                       side_incline_degrees, liters, created_at
                FROM bathtubs
                ORDER BY created_at DESC
            """)
            return cursor.fetchall()
    
    def delete_bathtub(self, bathtub_id: int) -> bool:
        """Delete a bathtub by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM bathtubs WHERE id = ?", (bathtub_id,))
            return cursor.rowcount > 0


class AddBathtubScreen(Screen):
    """Screen for adding a new bathtub."""
    
    CSS = """
    AddBathtubScreen {
        align: center middle;
    }
    
    .form-container {
        width: 60;
        height: auto;
        border: solid $primary;
        padding: 2;
        background: $surface;
    }
    
    .form-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        padding: 1;
    }
    
    .input-group {
        height: 3;
        margin: 1 0;
    }
    
    Input {
        width: 100%;
    }
    
    .button-group {
        height: 3;
        align: center middle;
        margin-top: 2;
    }
    
    Button {
        margin: 0 1;
    }
    
    .result-display {
        margin-top: 2;
        padding: 1;
        background: $boost;
        border: solid $success;
        text-align: center;
    }
    
    .error-display {
        margin-top: 2;
        padding: 1;
        background: $boost;
        border: solid $error;
        text-align: center;
        color: $error;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Container(classes="form-container"):
            yield Static("Add New Bathtub", classes="form-title")
            
            with Vertical():
                yield Label("Name:")
                yield Input(placeholder="Enter bathtub name", id="name_input")
                
                yield Label("Top Length (cm):")
                yield Input(placeholder="Enter top length", id="top_length_input", 
                          validators=[Number(minimum=0)])
                
                yield Label("Bottom Length (cm):")
                yield Input(placeholder="Enter bottom length", id="bottom_length_input",
                          validators=[Number(minimum=0)])
                
                yield Label("Width (cm):")
                yield Input(placeholder="Enter width", id="width_input",
                          validators=[Number(minimum=0)])
                
                yield Label("Height (cm):")
                yield Input(placeholder="Enter height", id="height_input",
                          validators=[Number(minimum=0)])
                
                yield Label("Liters (optional):")
                yield Input(placeholder="Enter capacity in liters (leave empty for N/A)", id="liters_input")
                
                with Horizontal(classes="button-group"):
                    yield Button("Calculate & Save", variant="primary", id="save_button")
                    yield Button("Cancel", variant="default", id="cancel_button")
                
                yield Static("", id="result_display", classes="result-display")
        yield Footer()
    
    def calculate_incline(self, top_length: float, bottom_length: float, height: float) -> float:
        """Calculate the side incline angle in degrees."""
        if height == 0:
            return 0
        
        # Calculate the horizontal difference for one side
        horizontal_diff = abs(top_length - bottom_length) / 2
        
        # Calculate angle using arctangent
        angle_radians = math.atan(horizontal_diff / height)
        angle_degrees = math.degrees(angle_radians)
        
        return angle_degrees
    
    @on(Button.Pressed, "#save_button")
    async def save_bathtub(self, event: Button.Pressed) -> None:
        """Save the bathtub to the database."""
        # Get all input values
        name_input = self.query_one("#name_input", Input)
        top_length_input = self.query_one("#top_length_input", Input)
        bottom_length_input = self.query_one("#bottom_length_input", Input)
        width_input = self.query_one("#width_input", Input)
        height_input = self.query_one("#height_input", Input)
        liters_input = self.query_one("#liters_input", Input)
        result_display = self.query_one("#result_display", Static)
        
        # Validate inputs
        if not name_input.value:
            result_display.update("Please enter a name")
            result_display.add_class("error-display")
            result_display.remove_class("result-display")
            return
        
        try:
            top_length = float(top_length_input.value)
            bottom_length = float(bottom_length_input.value)
            width = float(width_input.value)
            height = float(height_input.value)
        except (ValueError, TypeError):
            result_display.update("Please enter valid numeric values")
            result_display.add_class("error-display")
            result_display.remove_class("result-display")
            return
        
        # Handle liters input - default to "N/A" if empty
        liters = liters_input.value.strip() if liters_input.value.strip() else "N/A"
        
        # Calculate incline
        incline = self.calculate_incline(top_length, bottom_length, height)
        
        # Save to database
        db = Database()
        bathtub_id = db.add_bathtub(
            name_input.value,
            top_length,
            bottom_length,
            width,
            height,
            incline,
            liters
        )
        
        # Display result
        result_display.remove_class("error-display")
        result_display.add_class("result-display")
        result_display.update(
            f"✓ Saved '{name_input.value}' with side incline: {incline:.2f}°"
        )
        
        # Clear inputs
        name_input.value = ""
        top_length_input.value = ""
        bottom_length_input.value = ""
        width_input.value = ""
        height_input.value = ""
        liters_input.value = ""
    
    @on(Button.Pressed, "#cancel_button")
    async def cancel(self, event: Button.Pressed) -> None:
        """Return to main menu."""
        self.app.pop_screen()


class ViewBathtubsScreen(Screen):
    """Screen for viewing all bathtubs."""
    
    CSS = """
    ViewBathtubsScreen {
        align: center middle;
    }
    
    .table-container {
        width: 90%;
        height: 80%;
        border: solid $primary;
        background: $surface;
    }
    
    .table-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        padding: 1;
    }
    
    DataTable {
        height: 100%;
    }
    
    .button-group {
        dock: bottom;
        height: 3;
        align: center middle;
        padding: 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Container(classes="table-container"):
            yield Static("Bathtub Measurements", classes="table-title")
            yield DataTable(id="bathtub_table")
            with Horizontal(classes="button-group"):
                yield Button("Refresh", variant="primary", id="refresh_button")
                yield Button("Back", variant="default", id="back_button")
        yield Footer()
    
    def on_mount(self) -> None:
        """Load data when screen mounts."""
        self.load_bathtubs()
    
    def load_bathtubs(self) -> None:
        """Load bathtubs from database into the table."""
        try:
            table = self.query_one("#bathtub_table", DataTable)
        except Exception:
            # Table not ready yet, skip loading
            return
            
        table.clear(columns=True)
        
        # Add columns
        table.add_column("ID", key="id", width=5)
        table.add_column("Name", key="name", width=20)
        table.add_column("Top (cm)", key="top", width=10)
        table.add_column("Bottom (cm)", key="bottom", width=10)
        table.add_column("Width (cm)", key="width", width=10)
        table.add_column("Height (cm)", key="height", width=10)
        table.add_column("Incline (°)", key="incline", width=10)
        table.add_column("Liters", key="liters", width=10)
        table.add_column("Created", key="created", width=20)
        
        # Load data
        db = Database()
        bathtubs = db.get_all_bathtubs()
        
        for bathtub in bathtubs:
            created_dt = datetime.fromisoformat(bathtub['created_at'])
            table.add_row(
                bathtub['id'],
                bathtub['name'],
                f"{bathtub['top_length']:.1f}",
                f"{bathtub['bottom_length']:.1f}",
                f"{bathtub['width']:.1f}",
                f"{bathtub['height']:.1f}",
                f"{bathtub['side_incline_degrees']:.2f}",
                bathtub['liters'],
                created_dt.strftime("%Y-%m-%d %H:%M")
            )
    
    @on(Button.Pressed, "#refresh_button")
    async def on_refresh_button(self, event: Button.Pressed) -> None:
        """Handle refresh button press."""
        self.refresh_table()
    
    def refresh_table(self) -> None:
        """Refresh the table data."""
        try:
            table = self.query_one("#bathtub_table", DataTable)
        except Exception:
            # Table not ready yet, skip loading
            return
            
        table.clear(columns=True)
        
        # Add columns
        table.add_column("ID", key="id", width=5)
        table.add_column("Name", key="name", width=20)
        table.add_column("Top (cm)", key="top", width=10)
        table.add_column("Bottom (cm)", key="bottom", width=10)
        table.add_column("Width (cm)", key="width", width=10)
        table.add_column("Height (cm)", key="height", width=10)
        table.add_column("Incline (°)", key="incline", width=10)
        table.add_column("Liters", key="liters", width=10)
        table.add_column("Created", key="created", width=20)
        
        # Load data
        db = Database()
        bathtubs = db.get_all_bathtubs()
        
        for bathtub in bathtubs:
            created_dt = datetime.fromisoformat(bathtub['created_at'])
            table.add_row(
                bathtub['id'],
                bathtub['name'],
                f"{bathtub['top_length']:.1f}",
                f"{bathtub['bottom_length']:.1f}",
                f"{bathtub['width']:.1f}",
                f"{bathtub['height']:.1f}",
                f"{bathtub['side_incline_degrees']:.2f}",
                bathtub['liters'],
                created_dt.strftime("%Y-%m-%d %H:%M")
            )
    
    @on(Button.Pressed, "#back_button")
    async def go_back(self, event: Button.Pressed) -> None:
        """Return to main menu."""
        self.app.pop_screen()


class BathtubApp(App):
    """Main Textual application for bathtub measurements."""
    
    CSS = """
    .main-menu {
        align: center middle;
    }
    
    .menu-container {
        width: 50;
        height: auto;
        border: solid $primary;
        padding: 2;
        background: $surface;
    }
    
    .app-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        padding: 2;
    }
    
    .menu-button {
        width: 100%;
        margin: 1 0;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("a", "add_bathtub", "Add Bathtub"),
        Binding("v", "view_bathtubs", "View All"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Container(classes="main-menu"):
            with Vertical(classes="menu-container"):
                yield Static("🛁 Bathtub Manager", classes="app-title")
                yield Button("Add New Bathtub", variant="primary", id="add_button", classes="menu-button")
                yield Button("View All Bathtubs", variant="success", id="view_button", classes="menu-button")
                yield Button("Quit", variant="error", id="quit_button", classes="menu-button")
        yield Footer()
    
    @on(Button.Pressed, "#add_button")
    async def action_add_bathtub(self) -> None:
        """Show the add bathtub screen."""
        await self.push_screen(AddBathtubScreen())
    
    @on(Button.Pressed, "#view_button")
    async def action_view_bathtubs(self) -> None:
        """Show the view bathtubs screen."""
        await self.push_screen(ViewBathtubsScreen())
    
    @on(Button.Pressed, "#quit_button")
    async def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


def main():
    """Run the Bathtub Manager application."""
    app = BathtubApp()
    app.run()


if __name__ == "__main__":
    main()