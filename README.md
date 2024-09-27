# Family Tree Tracker

## Description

Family Tree Tracker is a comprehensive Python application designed to help users manage and visualize their familial relationships. Utilizing a user-friendly graphical interface built with Tkinter, the tool allows users to add, update, and delete family members, define relationships between them, and view the entire family tree interactively. The application ensures data persistence through an SQLite database, making it easy to maintain and retrieve family information over time.

## Features

- **Add Family Members:** Easily input and store detailed information about each family member, including names, birth and death dates, burial places, and additional notes.
- **Update and Delete Members:** Modify existing family member details or remove members from the database as needed.
- **Define Relationships:** Establish various types of relationships (e.g., parent, sibling, spouse) between family members to build a comprehensive family tree.
- **Interactive Family Tree Visualization:** Visualize the entire family tree on a scalable and pannable canvas, with nodes representing family members and lines depicting their relationships.
- **Zoom and Pan:** Navigate through large family trees effortlessly using intuitive zooming and panning functionalities.
- **Detailed Member Views:** Click on any family member node to view detailed information and manage their relationships directly from the details window.
- **Persistent Data Storage:** All family data and relationships are stored in an SQLite database (`family_tree.db`), ensuring that your information is saved and accessible across sessions.
- **User-Friendly Interface:** Intuitive menus and dialogs make it easy to interact with the application, even for users with minimal technical expertise.

## Algorithms and Data Structures

### Generation Assignment

To effectively layout the family tree, the application assigns generation numbers to each family member. This hierarchical organization ensures that ancestors appear at higher levels and descendants at lower levels, providing a clear and structured visualization of familial relationships.

- **Root Members Identification:** Members without parents are identified as root members and assigned the initial generation number.
- **Recursive Generation Assignment:** Starting from root members, the application recursively assigns generation numbers to their descendants, incrementing the generation level with each subsequent generation.

### Canvas Drawing and Layout

The family tree is rendered on a Tkinter canvas, where each family member is represented as a node. The layout algorithm positions nodes based on their generation, ensuring an organized and visually appealing tree structure.

- **Node Positioning:** Members are arranged horizontally within their generation level, with equal spacing to prevent overlap and maintain readability.
- **Relationship Lines:** Lines with arrows are drawn between nodes to represent relationships, providing a clear depiction of familial connections.

### Event Handling

The application incorporates various event handlers to facilitate user interactions, making the family tree dynamic and responsive.

- **Node Selection:** Left-clicking on a member node opens a detailed view of that member, allowing for information updates and relationship management.
- **Panning and Zooming:** Right-click and drag to pan across the canvas, while the mouse wheel controls zooming in and out, enabling users to navigate large family trees seamlessly.
- **Menu Actions:** Menu options trigger dialogs for adding members or relationships, ensuring that all actions are accessible through an organized menu system.

### Database Operations

Family data and relationships are managed using an SQLite database, ensuring efficient storage and retrieval of information.

- **Tables Structure:**
  - **family_member:** Stores detailed information about each family member, including personal details and notes.
  - **relationships:** Captures the connections between family members, specifying the type of relationship (e.g., parent, sibling).
- **CRUD Operations:** The `Database` class provides methods to create, read, update, and delete records in both tables, ensuring data integrity and consistency.
- **Relationship Management:** Specialized methods handle the addition and deletion of relationships, maintaining the accurate representation of familial connections.

### Data Structures

- **Dictionaries:** Utilized to store and manage family members and their corresponding details for quick access and manipulation.
- **Lists:** Manage collections of relationships, facilitating easy iteration and processing during tree visualization.
- **Canvas Items Mapping:** Maintains a mapping between family member IDs and their visual representations on the canvas, enabling efficient updates and event handling.