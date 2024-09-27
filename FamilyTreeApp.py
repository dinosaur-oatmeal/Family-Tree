import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter import ttk  # Ensure ttk is imported
import sqlite3
import math

class Database:
    """
    This class handles all interactions with the SQLite database,
    including creating tables, and performing Create, Read, Update, Deleter (CRUD)
    operations for family members and their relationships.
    """
    def __init__(self, db_name='family_tree.db'):
        """
        Initialize the Database object by connecting to the SQLite database
        and creating necessary tables if they don't exist.
        """
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self):
        """
        Create the 'family_member' and 'relationships' tables if they don't exist.
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS family_member (
                member_id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                middle_name TEXT,
                last_name TEXT NOT NULL,
                maiden_name TEXT,
                birth_date TEXT,
                death_date TEXT,
                burial_place TEXT,
                links TEXT,
                notes TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS relationships (
                relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER,
                relative_id INTEGER,
                relationship_type TEXT,
                FOREIGN KEY(member_id) REFERENCES family_member(member_id),
                FOREIGN KEY(relative_id) REFERENCES family_member(member_id)
            )
        ''')
        self.conn.commit()

    def add_member(self, member_data):
        """
        Add a new family member to the 'family_member' table.

        Parameters:
            member_data (dict): Dictionary containing member details.

        Returns:
            int: The member_id of the newly added member.
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO family_member 
            (first_name, middle_name, last_name, maiden_name, birth_date, death_date, burial_place, links, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            member_data.get('first_name'),
            member_data.get('middle_name'),
            member_data.get('last_name'),
            member_data.get('maiden_name'),
            member_data.get('birth_date'),
            member_data.get('death_date'),
            member_data.get('burial_place'),
            member_data.get('links'),
            member_data.get('notes')
        ))
        self.conn.commit()
        return cursor.lastrowid

    def update_member(self, member_id, member_data):
        """
        Update an existing family member's details.

        Parameters:
            member_id (int): The ID of the member to update.
            member_data (dict): Dictionary containing updated member details.
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE family_member
            SET first_name=?, middle_name=?, last_name=?, maiden_name=?, birth_date=?, death_date=?, burial_place=?, links=?, notes=?
            WHERE member_id=?
        ''', (
            member_data.get('first_name'),
            member_data.get('middle_name'),
            member_data.get('last_name'),
            member_data.get('maiden_name'),
            member_data.get('birth_date'),
            member_data.get('death_date'),
            member_data.get('burial_place'),
            member_data.get('links'),
            member_data.get('notes'),
            member_id
        ))
        self.conn.commit()

    def delete_member(self, member_id):
        """
        Delete a family member and all associated relationships from the database.

        Parameters:
            member_id (int): The ID of the member to delete.
        """
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM family_member WHERE member_id=?', (member_id,))
        cursor.execute('DELETE FROM relationships WHERE member_id=? OR relative_id=?', (member_id, member_id))
        self.conn.commit()

    def get_all_members(self):
        """
        Retrieve all family members from the database.

        Returns:
            list: A list of tuples representing each family member.
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM family_member')
        return cursor.fetchall()

    def get_member(self, member_id):
        """
        Retrieve a specific family member by their ID.

        Parameters:
            member_id (int): The ID of the member to retrieve.

        Returns:
            tuple: A tuple containing the member's details.
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM family_member WHERE member_id=?', (member_id,))
        return cursor.fetchone()

    def add_relationship(self, member_id, relative_id, relationship_type):
        """
        Add a new relationship between two family members.

        Parameters:
            member_id (int): The ID of the first member.
            relative_id (int): The ID of the relative member.
            relationship_type (str): The type of relationship (e.g., parent, sibling).
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO relationships (member_id, relative_id, relationship_type)
            VALUES (?, ?, ?)
        ''', (member_id, relative_id, relationship_type))
        self.conn.commit()

    def get_relationships(self):
        """
        Retrieve all relationships from the database.

        Returns:
            list: A list of tuples representing each relationship.
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM relationships')
        return cursor.fetchall()

    def get_member_relationships(self, member_id):
        """
        Retrieve all relationships involving a specific member.

        Parameters:
            member_id (int): The ID of the member.

        Returns:
            list: A list of tuples representing each relationship involving the member.
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT relationship_id, member_id, relative_id, relationship_type
            FROM relationships
            WHERE member_id=? OR relative_id=?
        ''', (member_id, member_id))
        return cursor.fetchall()

    def delete_relationship(self, relationship_id):
        """
        Delete a specific relationship by its ID.

        Parameters:
            relationship_id (int): The ID of the relationship to delete.
        """
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM relationships WHERE relationship_id=?', (relationship_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()

class FamilyTreeApp:
    """
    This class manages the Tkinter GUI for the Family Tree Tracker application.
    It handles user interactions, displays the family tree, and interfaces with the Database class.
    """
    def __init__(self, root):
        """
        Initialize the FamilyTreeApp with the main Tkinter window.

        Parameters:
            root (tk.Tk): The main Tkinter window.
        """
        self.root = root
        self.root.title("Family Tree Tracker")
        self.db = Database()
        self.members = {}
        self.relationships = []
        self.node_radius = 40
        self.offset_x = 0
        self.offset_y = 0
        self.scale = 1.0
        self.selected_member_id = None
        self.node_positions = {}
        self.canvas_items = {}
        self.setup_ui()
        self.load_data()
        self.draw_tree()

    def setup_ui(self):
        """
        Set up the user interface, including menus, canvas, and scrollbars.
        """
        # Create Menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Add Member", command=self.add_member_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Relationship Menu
        rel_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Relationships", menu=rel_menu)
        rel_menu.add_command(label="Add Relationship", command=self.add_relationship_dialog)

        # Create a frame to hold the Canvas and Scrollbars
        self.canvas_frame = tk.Frame(self.root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        # Create Canvas where the family tree will be drawn
        self.canvas = tk.Canvas(self.canvas_frame, bg="white", scrollregion=(0, 0, 2000, 2000))
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbars
        self.h_scroll = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scroll = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.config(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)

        # Bind events for panning
        self.canvas.bind("<ButtonPress-3>", self.on_pan_start)  # Right mouse button press
        self.canvas.bind("<B3-Motion>", self.on_pan_move)       # Right mouse button drag
        self.canvas.bind("<MouseWheel>", self.on_zoom)          # Windows mouse wheel
        self.canvas.bind("<Button-4>", self.on_zoom)            # Linux scroll up
        self.canvas.bind("<Button-5>", self.on_zoom)            # Linux scroll down

        # Bind left-click event for selecting nodes
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    def load_data(self):
        """
        Load family members and relationships from the database into the application's data structures.
        """
        members = self.db.get_all_members()
        self.members = {member[0]: member for member in members}

        # Load all relationships
        self.relationships = self.db.get_relationships()

    def draw_tree(self):
        """
        Draw the family tree on the canvas by positioning nodes and drawing relationships.
        """
        # Clear any existing drawings
        self.canvas.delete("all")
        self.node_positions = {}
        self.canvas_items = {}

        # Assign generations to members (layout)
        generations = self.assign_generations()
        if generations:
            max_generation = max(generations.values())
        else:
            max_generation = 0
        gen_spacing_y = 200     # Vertical spacing between generations
        gen_spacing_x = 150     # Horizontal spacing between members

        # Organize members by their generations
        gen_members = {}
        for member_id, gen in generations.items():
            gen_members.setdefault(gen, []).append(member_id)

        # Assign positions to each member based on their generation
        for gen, members in gen_members.items():
            num = len(members)
            spacing = gen_spacing_x
            start_x = 1000 - ((num - 1) / 2) * spacing
            y = 100 + gen * gen_spacing_y
            for i, member_id in enumerate(members):
                x = start_x + i * spacing
                self.node_positions[member_id] = (x, y)

        # Draw relationships first (lines between nodes)
        for rel in self.relationships:
            _, member_id, relative_id, relationship_type = rel
            if member_id in self.node_positions and relative_id in self.node_positions:
                x1, y1 = self.node_positions[member_id]
                x2, y2 = self.node_positions[relative_id]
                self.canvas.create_line(x1, y1, x2, y2, arrow=tk.LAST, fill="gray")

        # Draw family members (nodes)
        for member_id, pos in self.node_positions.items():
            x, y = pos
            self.draw_node(member_id, x, y)

        # Update the scrollable region of the canvas based on the drawn items
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def assign_generations(self):
        """
        Assign generation numbers to each family member to aid in layout.

        Returns:
            dict: A dictionary mapping member_id to their generation number.
        """
        generations = {}
        # Identify parents by collecting members who are referenced as 'parent', 'father', or 'mother' in relationships
        parents = set()
        for rel in self.relationships:
            _, member_id, relative_id, relationship_type = rel
            if relationship_type.lower() in ['parent', 'father', 'mother']:
                parents.add(relative_id)

        # Identify root members (members without parents)
        root_members = [m_id for m_id in self.members if m_id not in parents]
        for m_id in root_members:
            self.assign_generation_recursive(m_id, 0, generations)

        return generations

    def assign_generation_recursive(self, member_id, generation, generations):
        """
        Recursively assign generation numbers to members.

        Parameters:
            member_id (int): The ID of the current member.
            generation (int): The generation number to assign.
            generations (dict): The dictionary mapping member IDs to generations.
        """
        if member_id in generations:
            if generation < generations[member_id]:
                generations[member_id] = generation
            else:
                return
        else:
            generations[member_id] = generation

        # Find children of the current member
        children = []
        for rel in self.relationships:
            _, m_id, rel_id, rel_type = rel
            if m_id == member_id and rel_type.lower() in ['parent', 'father', 'mother']:
                children.append(rel_id)

        # Recursively assign generations to children
        for child_id in children:
            self.assign_generation_recursive(child_id, generation + 1, generations)

    def draw_node(self, member_id, x, y):
        """
        Draw a single family member as a node on the canvas.

        Parameters:
            member_id (int): The ID of the member.
            x (float): The x-coordinate of the node's center.
            y (float): The y-coordinate of the node's center.
        """
        r = self.node_radius
        tag = f"node_{member_id}"
        
        # Create oval representing the node
        oval = self.canvas.create_oval(
            x - r, y - r, x + r, y + r,
            fill="lightblue", outline="black", width=2,
            tags=(tag,)
        )
        
        # Create text inside the oval with the member's name
        name = f"{self.members[member_id][1]} {self.members[member_id][3]}"
        text = self.canvas.create_text(
            x, y, text=name, font=("Arial", 10, "bold"),
            tags=(tag,)
        )
        
        # Store the canvas items for potential future reference
        self.canvas_items[member_id] = (oval, text)
        
        # Bind the left-click event to the node's tag (shows details)
        self.canvas.tag_bind(tag, "<Button-1>", lambda event, m_id=member_id: self.show_member_details(m_id))

    def on_pan_start(self, event):
        """
        Handle the start of a panning action when the right mouse button is pressed.

        Parameters:
            event (tk.Event): The event object.
        """
        self.canvas.scan_mark(event.x, event.y)

    def on_pan_move(self, event):
        """
        Handle the movement during panning when the right mouse button is dragged.

        Parameters:
            event (tk.Event): The event object.
        """
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def on_zoom(self, event):
        """
        Handle zooming in and out of the canvas using the mouse wheel.

        Parameters:
            event (tk.Event): The event object.
        """
        if event.delta:
            if event.delta > 0:
                scale = 1.1      # Zoom In
            else:
                scale = 0.9      # Zoom Out
        elif event.num == 4:
            scale = 1.1          # Zoom In (Linux)
        elif event.num == 5:
            scale = 0.9          # Zoom Out (Linux)
        else:
            scale = 1.0          # No Scaling

        # Calculate the new scale and limit it to prevent excessive zooming
        new_scale = self.scale * scale
        if 0.1 < new_scale < 10:
            self.scale = new_scale
            # Get the mouse position on the canvas
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)

            # Apply scaling to all items on the canvas
            self.canvas.scale("all", x, y, scale, scale)

            # Optionally, adjust the scroll region
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_click(self, event):
        """
        Handle left-click events on the canvas background.
        Currently, this method is a placeholder and can be expanded if needed.

        Parameters:
            event (tk.Event): The event object.
        """
        pass

    def show_member_details(self, member_id):
        """
        Display a detailed view of a family member in a new window.

        Parameters:
            member_id (int): The ID of the member whose details are to be shown.
        """
        member = self.db.get_member(member_id)
        if not member:
            messagebox.showerror("Error", "Member not found.")
            return

        # Create a new top-level window for member details
        details_window = tk.Toplevel(self.root)
        details_window.title("Member Details")

        # Labels for member attributes
        labels = ["First Name", "Middle Name", "Last Name", "Maiden Name",
                  "Birth Date", "Death Date", "Burial Place", "Links", "Notes"]
        for idx, label in enumerate(labels):
            tk.Label(details_window, text=f"{label}: ", font=("Arial", 10, "bold")).grid(row=idx, column=0, sticky='e', padx=5, pady=2)
            value = member[idx+1] if member[idx+1] else ""
            tk.Label(details_window, text=value, wraplength=300, justify='left').grid(row=idx, column=1, sticky='w', padx=5, pady=2)

        # Display Relationships
        tk.Label(details_window, text="Relationships:", font=("Arial", 10, "bold")).grid(row=len(labels), column=0, sticky='ne', padx=5, pady=5)
        
        relationships_frame = tk.Frame(details_window)
        relationships_frame.grid(row=len(labels), column=1, sticky='w', padx=5, pady=5)

        # Fetch relationships where the member is either member_id or relative_id
        relationships = self.db.get_member_relationships(member_id)

        if relationships:
            for idx, rel in enumerate(relationships):
                rel_id, rel_member_id, rel_relative_id, rel_type = rel
                # Determine other member in the relationship
                if rel_member_id == member_id:
                    other_member = self.db.get_member(rel_relative_id)
                else:
                    other_member = self.db.get_member(rel_member_id)
                if other_member:
                    other_member_name = f"{other_member[1]} {other_member[3]}"
                else:
                    other_member_name = "Unknown"

                rel_label = f"{rel_type} - {other_member_name}"
                tk.Label(relationships_frame, text=rel_label).grid(row=idx, column=0, sticky='w')

                # Delete button for each relationship
                tk.Button(relationships_frame, text="Delete", command=lambda r_id=rel_id: self.delete_relationship(r_id, details_window)).grid(row=idx, column=1, padx=5, pady=2)
        else:
            tk.Label(relationships_frame, text="No relationships found.").grid(row=0, column=0, sticky='w')

        # Buttons for updating, deleting, and adding relationships
        button_frame = tk.Frame(details_window)
        button_frame.grid(row=len(labels)+1, column=0, columnspan=2, pady=10)

        tk.Button(button_frame, text="Update Member", command=lambda: self.update_member_dialog(member_id, details_window)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Delete Member", command=lambda: self.delete_member(member_id, details_window)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Add Relationship", command=lambda: self.add_relationship_dialog(member_id)).pack(side=tk.LEFT, padx=5)

    def add_member_dialog(self):
        """
        Open a dialog to add a new family member.
        """
        dialog = MemberDialog(self.root, "Add Family Member")
        self.root.wait_window(dialog.top)  # Wait until dialog is closed
        if dialog.result:
            member_id = self.db.add_member(dialog.result)  # Add member to database
            self.load_data()   # Reload data
            self.draw_tree()   # Redraw tree to include new member

    def update_member_dialog(self, member_id, parent_window):
        """
        Open a dialog to update an existing family member's details.

        Parameters:
            member_id (int): The ID of the member to update.
            parent_window (tk.Toplevel): The parent window to close after updating.
        """
        member = self.db.get_member(member_id)
        if not member:
            messagebox.showerror("Error", "Member not found.")
            return
        dialog = MemberDialog(self.root, "Update Family Member", member)
        self.root.wait_window(dialog.top)
        if dialog.result:
            self.db.update_member(member_id, dialog.result)   # Update member in database
            parent_window.destroy()   # Close details window
            self.load_data()   # Reload data
            self.draw_tree()   # Redraw tree to include updates

    def delete_member(self, member_id, parent_window):
        """
        Delete a family member after user confirmation.

        Parameters:
            member_id (int): The ID of the member to delete.
            parent_window (tk.Toplevel): The parent window to close after deletion.
        """
        confirm = messagebox.askyesno("Delete Member", "Are you sure you want to delete this member?")
        if confirm:
            self.db.delete_member(member_id)   # Delete member from database
            parent_window.destroy()   # Close details window
            self.load_data()   # Reload data
            self.draw_tree()   # Redraw tree to reflect deletion

    def add_relationship_dialog(self, member_id=None):
        """
        Open a dialog to add a new relationship. If member_id is provided,
        it will pre-select that member.

        Parameters:
            member_id (int, optional): The ID of the member to associate with a new relationship.
        """
        dialog = RelationshipDialog(self.root, self.db, member_id)
        self.root.wait_window(dialog.top)
        if dialog.result:
            member_id, relative_id, relationship_type = dialog.result
            self.db.add_relationship(member_id, relative_id, relationship_type)   # Add relationship to database
            self.load_data()   # Reload data
            self.draw_tree()   # Redraw tree to include updates

    def delete_relationship(self, relationship_id, parent_window):
        """
        Delete a relationship after user confirmation.

        Parameters:
            relationship_id (int): The ID of the relationship to delete.
            parent_window (tk.Toplevel): The parent window to close after deletion.
        """
        confirm = messagebox.askyesno("Delete Relationship", "Are you sure you want to delete this relationship?")
        if confirm:
            self.db.delete_relationship(relationship_id)   # Delete relationship from database
            parent_window.destroy()   # Close details window
            self.load_data()   # Reload data
            self.draw_tree()   # Redraw tree to reflect deletion

class MemberDialog:
    """
    This class creates a dialog window for adding or updating a family member.
    """
    def __init__(self, parent, title, member=None):
        """
        Initialize the MemberDialog.

        Parameters:
            parent (tk.Widget): The parent widget.
            title (str): The title of the dialog window.
            member (tuple, optional): Existing member data for updating. None for adding a new member.
        """
        self.result = None
        self.top = tk.Toplevel(parent)
        self.top.title(title)
        self.top.grab_set()  # Make the dialog modal
        self.create_widgets(member)

    def create_widgets(self, member):
        """
        Create the input fields and buttons for the dialog.

        Parameters:
            member (tuple, optional): Existing member data for updating.
        """
        # Labels for member attributes
        labels = ["First Name*", "Middle Name", "Last Name*", "Maiden Name",
                  "Birth Date", "Death Date", "Burial Place", "Links", "Notes"]
        self.entries = {}

        # Create entry fields for each attribute
        for idx, label in enumerate(labels):
            tk.Label(self.top, text=label).grid(row=idx, column=0, padx=10, pady=5, sticky='e')
            entry = tk.Entry(self.top, width=40)
            entry.grid(row=idx, column=1, padx=10, pady=5)
            self.entries[label] = entry

        # If updating an existing member, pre-fill the fields with current data
        if member:
            self.entries["First Name*"].insert(0, member[1] or "")
            self.entries["Middle Name"].insert(0, member[2] or "")
            self.entries["Last Name*"].insert(0, member[3] or "")
            self.entries["Maiden Name"].insert(0, member[4] or "")
            self.entries["Birth Date"].insert(0, member[5] or "")
            self.entries["Death Date"].insert(0, member[6] or "")
            self.entries["Burial Place"].insert(0, member[7] or "")
            self.entries["Links"].insert(0, member[8] or "")
            self.entries["Notes"].insert(0, member[9] or "")

        # Save button to submit the form
        tk.Button(self.top, text="Save", command=self.on_save).grid(row=len(labels), column=0, columnspan=2, pady=10)

    def on_save(self):
        """
        Validate input and set the result when the Save button is clicked.
        """
        # Retrieve and strip input values
        first_name = self.entries["First Name*"].get().strip()
        last_name = self.entries["Last Name*"].get().strip()

        # Check for required fields
        if not first_name or not last_name:
            messagebox.showerror("Input Error", "First Name and Last Name are required.")
            return

        # Collect all input data into a dictionary
        self.result = {
            'first_name': first_name,
            'middle_name': self.entries["Middle Name"].get().strip(),
            'last_name': last_name,
            'maiden_name': self.entries["Maiden Name"].get().strip(),
            'birth_date': self.entries["Birth Date"].get().strip(),
            'death_date': self.entries["Death Date"].get().strip(),
            'burial_place': self.entries["Burial Place"].get().strip(),
            'links': self.entries["Links"].get().strip(),
            'notes': self.entries["Notes"].get().strip()
        }
        self.top.destroy()

class RelationshipDialog:
    """
    This class creates a dialog window for adding a new relationship between family members.
    """
    def __init__(self, parent, db, member_id=None):
        """
        Initialize the RelationshipDialog.

        Parameters:
            parent (tk.Widget): The parent widget.
            db (Database): The Database object for fetching members.
            member_id (int, optional): Pre-selected member ID if adding a relationship from a member's detail view.
        """
        self.result = None
        self.db = db
        self.member_id = member_id
        self.top = tk.Toplevel(parent)
        self.top.title("Add Relationship")
        self.top.grab_set()  # Make the dialog modal
        self.create_widgets()

    def create_widgets(self):
        """
        Create the input fields and buttons for the dialog.
        """
        # Labels for relationship attributes
        tk.Label(self.top, text="Member:").grid(row=0, column=0, padx=10, pady=5, sticky='e')
        tk.Label(self.top, text="Relative:").grid(row=1, column=0, padx=10, pady=5, sticky='e')
        tk.Label(self.top, text="Relationship Type:").grid(row=2, column=0, padx=10, pady=5, sticky='e')

        # Fetch all family members for selection
        members = self.db.get_all_members()
        if not members:
            messagebox.showerror("Error", "No members available.")
            self.top.destroy()
            return

        # Create options for the Comboboxes
        self.member_options = [f"{m[0]}: {m[1]} {m[3]}" for m in members]
        self.member_ids = {f"{m[0]}: {m[1]} {m[3]}": m[0] for m in members}

        if self.member_id:
            # If a member_id is provided, pre-select and disable the Member field
            member_info = self.db.get_member(self.member_id)
            member_option = f"{member_info[0]}: {member_info[1]} {member_info[3]}"
            self.member_var = tk.StringVar(value=member_option)
            member_combobox = ttk.Combobox(self.top, textvariable=self.member_var, values=[member_option], state="disabled")
            member_combobox.grid(row=0, column=1, padx=10, pady=5)
        else:
            # Otherwise, allow the user to select any member
            self.member_var = tk.StringVar()
            member_combobox = ttk.Combobox(self.top, textvariable=self.member_var, values=self.member_options, state="readonly")
            member_combobox.current(0)
            member_combobox.grid(row=0, column=1, padx=10, pady=5)

        # Combobox for selecting the relative
        self.relative_var = tk.StringVar()
        relative_combobox = ttk.Combobox(self.top, textvariable=self.relative_var, values=self.member_options, state="readonly")
        if len(self.member_options) > 1:
            relative_combobox.current(1)
        else:
            relative_combobox.current(0)
        relative_combobox.grid(row=1, column=1, padx=10, pady=5)

        # Entry field for specifying the type of relationship
        self.relationship_entry = tk.Entry(self.top, width=40)
        self.relationship_entry.grid(row=2, column=1, padx=10, pady=5)

        # Save button to submit the form
        tk.Button(self.top, text="Save", command=self.on_save).grid(row=3, column=0, columnspan=2, pady=10)

    def on_save(self):
        """
        Validate input and set the result when the Save button is clicked.
        """
        if self.member_id:
            member_id = self.member_id
        else:
            member_selection = self.member_var.get()
            member_id = self.member_ids.get(member_selection)

        relative_selection = self.relative_var.get()
        relative_id = self.member_ids.get(relative_selection)

        relationship_type = self.relationship_entry.get().strip()
        if not relationship_type:
            messagebox.showerror("Input Error", "Relationship Type is required.")
            return

        # Prevent a member from having a relationship with themselves
        if member_id == relative_id:
            messagebox.showerror("Input Error", "A member cannot have a relationship with themselves.")
            return

        # Set the result as a tuple of (member_id, relative_id, relationship_type)
        self.result = (member_id, relative_id, relationship_type)
        self.top.destroy()

def main():
    """
    The main function to run the Family Tree Tracker application.
    """
    root = tk.Tk()
    root.geometry("1200x800")   # Set initial window size
    app = FamilyTreeApp(root)   # Initialize application
    root.mainloop()             # Start the Tkinter event loop

if __name__ == "__main__":
    main()
