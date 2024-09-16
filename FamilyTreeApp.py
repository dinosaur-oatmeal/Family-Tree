import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter import ttk
import sqlite3
import math

class Database:
    def __init__(self, db_name='family_tree.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self):
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
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM family_member WHERE member_id=?', (member_id,))
        cursor.execute('DELETE FROM relationships WHERE member_id=? OR relative_id=?', (member_id, member_id))
        self.conn.commit()

    def get_all_members(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM family_member')
        return cursor.fetchall()

    def get_member(self, member_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM family_member WHERE member_id=?', (member_id,))
        return cursor.fetchone()

    def add_relationship(self, member_id, relative_id, relationship_type):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO relationships (member_id, relative_id, relationship_type)
            VALUES (?, ?, ?)
        ''', (member_id, relative_id, relationship_type))
        self.conn.commit()

    def get_relationships(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM relationships')
        return cursor.fetchall()

    def close(self):
        self.conn.close()

class FamilyTreeApp:
    def __init__(self, root):
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

        # Create Canvas with Scrollbars
        self.canvas_frame = tk.Frame(self.root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg="white", scrollregion=(0, 0, 2000, 2000))
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbars
        self.h_scroll = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scroll = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.config(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)

        # Bind events for panning and zooming
        self.canvas.bind("<ButtonPress-1>", self.on_pan_start)
        self.canvas.bind("<B1-Motion>", self.on_pan_move)
        self.canvas.bind("<MouseWheel>", self.on_zoom)  # Windows
        self.canvas.bind("<Button-4>", self.on_zoom)    # Linux scroll up
        self.canvas.bind("<Button-5>", self.on_zoom)    # Linux scroll down

        # Bind click event
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    def load_data(self):
        # Load members
        members = self.db.get_all_members()
        self.members = {member[0]: member for member in members}

        # Load relationships
        self.relationships = self.db.get_relationships()

    def draw_tree(self):
        self.canvas.delete("all")
        self.node_positions = {}
        self.canvas_items = {}

        # Simple layout: arrange members in generations
        generations = self.assign_generations()
        if generations:
            max_generation = max(generations.values())
        else:
            max_generation = 0
        gen_spacing_y = 200
        gen_spacing_x = 150

        # Assign positions
        gen_members = {}
        for member_id, gen in generations.items():
            gen_members.setdefault(gen, []).append(member_id)

        for gen, members in gen_members.items():
            num = len(members)
            spacing = gen_spacing_x
            start_x = 1000 - ((num - 1) / 2) * spacing
            y = 100 + gen * gen_spacing_y
            for i, member_id in enumerate(members):
                x = start_x + i * spacing
                self.node_positions[member_id] = (x, y)

        # Draw relationships first (lines)
        for rel in self.relationships:
            _, member_id, relative_id, relationship_type = rel
            if member_id in self.node_positions and relative_id in self.node_positions:
                x1, y1 = self.node_positions[member_id]
                x2, y2 = self.node_positions[relative_id]
                self.canvas.create_line(x1, y1, x2, y2, arrow=tk.LAST, fill="gray")

        # Draw members (nodes)
        for member_id, pos in self.node_positions.items():
            x, y = pos
            self.draw_node(member_id, x, y)

    def assign_generations(self):
        generations = {}
        # Simple algorithm: ancestors have lower generation numbers
        # Start with members without parents
        parents = set()
        for rel in self.relationships:
            _, member_id, relative_id, relationship_type = rel
            if relationship_type.lower() in ['parent', 'father', 'mother']:
                parents.add(relative_id)

        root_members = [m_id for m_id in self.members if m_id not in parents]
        for m_id in root_members:
            self.assign_generation_recursive(m_id, 0, generations)

        return generations

    def assign_generation_recursive(self, member_id, generation, generations):
        if member_id in generations:
            if generation < generations[member_id]:
                generations[member_id] = generation
            else:
                return
        else:
            generations[member_id] = generation

        # Find children
        children = []
        for rel in self.relationships:
            _, m_id, rel_id, rel_type = rel
            if m_id == member_id and rel_type.lower() in ['parent', 'father', 'mother']:
                children.append(rel_id)

        for child_id in children:
            self.assign_generation_recursive(child_id, generation + 1, generations)

    def draw_node(self, member_id, x, y):
        r = self.node_radius
        oval = self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="lightblue", outline="black", width=2)
        name = f"{self.members[member_id][1]} {self.members[member_id][3]}"
        text = self.canvas.create_text(x, y, text=name, font=("Arial", 10, "bold"))
        self.canvas_items[member_id] = (oval, text)

    def on_pan_start(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def on_pan_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def on_zoom(self, event):
        # Determine the zoom direction
        if event.delta:
            if event.delta > 0:
                scale = 1.1
            else:
                scale = 0.9
        elif event.num == 4:
            scale = 1.1
        elif event.num == 5:
            scale = 0.9
        else:
            scale = 1.0

        # Get mouse position
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        # Scale the canvas
        self.canvas.scale("all", x, y, scale, scale)
        self.scale *= scale

    def on_canvas_click(self, event):
        # Convert screen coordinates to canvas coordinates
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        clicked_member = None
        for member_id, pos in self.node_positions.items():
            node_x, node_y = pos
            distance = math.sqrt((x - node_x) ** 2 + (y - node_y) ** 2)
            if distance <= self.node_radius * self.scale:
                clicked_member = member_id
                break
        if clicked_member:
            self.show_member_details(clicked_member)

    def show_member_details(self, member_id):
        member = self.db.get_member(member_id)
        if not member:
            messagebox.showerror("Error", "Member not found.")
            return

        details_window = tk.Toplevel(self.root)
        details_window.title("Member Details")

        labels = ["First Name", "Middle Name", "Last Name", "Maiden Name",
                  "Birth Date", "Death Date", "Burial Place", "Links", "Notes"]
        for idx, label in enumerate(labels):
            tk.Label(details_window, text=f"{label}: ", font=("Arial", 10, "bold")).grid(row=idx, column=0, sticky='e', padx=5, pady=2)
            value = member[idx+1] if member[idx+1] else ""
            tk.Label(details_window, text=value, wraplength=300, justify='left').grid(row=idx, column=1, sticky='w', padx=5, pady=2)

        # Buttons
        button_frame = tk.Frame(details_window)
        button_frame.grid(row=len(labels), column=0, columnspan=2, pady=10)

        tk.Button(button_frame, text="Update Member", command=lambda: self.update_member_dialog(member_id, details_window)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Delete Member", command=lambda: self.delete_member(member_id, details_window)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Add Relationship", command=lambda: self.add_relationship_dialog(member_id)).pack(side=tk.LEFT, padx=5)

    def add_member_dialog(self):
        dialog = MemberDialog(self.root, "Add Family Member")
        self.root.wait_window(dialog.top)
        if dialog.result:
            member_id = self.db.add_member(dialog.result)
            self.load_data()
            self.draw_tree()

    def update_member_dialog(self, member_id, parent_window):
        member = self.db.get_member(member_id)
        if not member:
            messagebox.showerror("Error", "Member not found.")
            return
        dialog = MemberDialog(self.root, "Update Family Member", member)
        self.root.wait_window(dialog.top)
        if dialog.result:
            self.db.update_member(member_id, dialog.result)
            parent_window.destroy()
            self.load_data()
            self.draw_tree()

    def delete_member(self, member_id, parent_window):
        confirm = messagebox.askyesno("Delete Member", "Are you sure you want to delete this member?")
        if confirm:
            self.db.delete_member(member_id)
            parent_window.destroy()
            self.load_data()
            self.draw_tree()

    def add_relationship_dialog(self, member_id=None):
        dialog = RelationshipDialog(self.root, self.db, member_id)
        self.root.wait_window(dialog.top)
        if dialog.result:
            member_id, relative_id, relationship_type = dialog.result
            self.db.add_relationship(member_id, relative_id, relationship_type)
            self.load_data()
            self.draw_tree()

class MemberDialog:
    def __init__(self, parent, title, member=None):
        self.result = None
        self.top = tk.Toplevel(parent)
        self.top.title(title)
        self.top.grab_set()  # Make the dialog modal
        self.create_widgets(member)

    def create_widgets(self, member):
        labels = ["First Name*", "Middle Name", "Last Name*", "Maiden Name",
                  "Birth Date", "Death Date", "Burial Place", "Links", "Notes"]
        self.entries = {}

        for idx, label in enumerate(labels):
            tk.Label(self.top, text=label).grid(row=idx, column=0, padx=10, pady=5, sticky='e')
            entry = tk.Entry(self.top, width=40)
            entry.grid(row=idx, column=1, padx=10, pady=5)
            self.entries[label] = entry

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

        tk.Button(self.top, text="Save", command=self.on_save).grid(row=len(labels), column=0, columnspan=2, pady=10)

    def on_save(self):
        first_name = self.entries["First Name*"].get().strip()
        last_name = self.entries["Last Name*"].get().strip()

        if not first_name or not last_name:
            messagebox.showerror("Input Error", "First Name and Last Name are required.")
            return

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
    def __init__(self, parent, db, member_id=None):
        self.result = None
        self.db = db
        self.member_id = member_id
        self.top = tk.Toplevel(parent)
        self.top.title("Add Relationship")
        self.top.grab_set()  # Make the dialog modal
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.top, text="Member:").grid(row=0, column=0, padx=10, pady=5, sticky='e')
        tk.Label(self.top, text="Relative:").grid(row=1, column=0, padx=10, pady=5, sticky='e')
        tk.Label(self.top, text="Relationship Type:").grid(row=2, column=0, padx=10, pady=5, sticky='e')

        members = self.db.get_all_members()
        if not members:
            messagebox.showerror("Error", "No members available.")
            self.top.destroy()
            return

        member_options = [f"{m[0]}: {m[1]} {m[3]}" for m in members]
        self.member_ids = {f"{m[0]}: {m[1]} {m[3]}": m[0] for m in members}

        if self.member_id:
            # Pre-select the member
            member_info = self.db.get_member(self.member_id)
            member_option = f"{member_info[0]}: {member_info[1]} {member_info[3]}"
            member_var = tk.StringVar(value=member_option)
            member_menu = tk.OptionMenu(self.top, member_var, member_option)
            member_menu.grid(row=0, column=1, padx=10, pady=5)
            member_menu.config(state="disabled")
        else:
            member_var = tk.StringVar()
            member_var.set(member_options[0])
            tk.OptionMenu(self.top, member_var, *member_options).grid(row=0, column=1, padx=10, pady=5)

        relative_var = tk.StringVar()
        if len(member_options) > 1:
            relative_var.set(member_options[1])
        else:
            relative_var.set(member_options[0])
        tk.OptionMenu(self.top, relative_var, *member_options).grid(row=1, column=1, padx=10, pady=5)

        self.relationship_entry = tk.Entry(self.top, width=40)
        self.relationship_entry.grid(row=2, column=1, padx=10, pady=5)

        tk.Button(self.top, text="Save", command=lambda: self.on_save(member_var, relative_var)).grid(row=3, column=0, columnspan=2, pady=10)

    def on_save(self, member_var, relative_var):
        if self.member_id:
            member_id = self.member_id
        else:
            member_selection = member_var.get()
            member_id = self.member_ids.get(member_selection)

        relative_selection = relative_var.get()
        relative_id = self.member_ids.get(relative_selection)

        relationship_type = self.relationship_entry.get().strip()
        if not relationship_type:
            messagebox.showerror("Input Error", "Relationship Type is required.")
            return

        if member_id == relative_id:
            messagebox.showerror("Input Error", "A member cannot have a relationship with themselves.")
            return

        self.result = (member_id, relative_id, relationship_type)
        self.top.destroy()

def main():
    root = tk.Tk()
    root.geometry("1200x800")
    app = FamilyTreeApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
