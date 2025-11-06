import tkinter as tk
from tkinter import messagebox
import copy
from datetime import datetime
import tkinter.font as tkfont
from tkcalendar import DateEntry   # pip install tkcalendar
import json
import os
import sys

def get_save_file():
    """
    Ermittelt einen Speicherort für die Daten im gleichen Ordner wie
    das Script (beim Entwickeln) bzw. die ausführbare Datei (bei PyInstaller).
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller: Pfad zur ausgeführten EXE / .app
        base_dir = os.path.dirname(sys.executable)
    else:
        # Normales Python-Script
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "todo_data.json")

SAVE_FILE = get_save_file()


class ToDoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("To-Do Liste")

        # Daten
        # Jeder Eintrag: { "text": str, "done": bool, "created_at": str, "deadline": str, "list_id": int }
        self.todos = []
        self.history = []              # Zustände für Undo (für alle Listen)
        self.visible_indices = []      # Sichtbare Indizes in aktueller Ansicht
        self.row_widgets = []          # Widgets pro Tabellenzeile (für Markierung)
        self.selected_index = None     # Index in self.todos oder self.lists (je nach Ansicht)
        self.show_history = False      # False = offene To Dos, True = erledigte
        self.current_view = "todos"    # "todos" oder "lists"

        # Listen-Verwaltung (Default-Liste)
        self.lists = []
        self.next_list_id = 1
        default_list = {"id": self.next_list_id, "name": "Standard", "description": ""}
        self.next_list_id += 1
        self.lists.append(default_list)
        self.current_list_id = default_list["id"]

        # Beim Start gespeicherte Daten laden (falls vorhanden)
        self.load_data()
        # next_list_id nach geladenen Daten anpassen
        if self.lists:
            self.next_list_id = max(lst.get("id", 0) for lst in self.lists) + 1
        else:
            self.next_list_id = 1

        # Kontextmenü für Listen
        self.list_menu = tk.Menu(root, tearoff=0)
        self.list_menu.add_command(label="Bearbeiten", command=self.edit_selected_list)
        self.list_menu.add_command(label="Löschen", command=self.delete_selected_list)

        # Header-Font
        base_font = tkfont.nametofont("TkDefaultFont")
        self.header_font = base_font.copy()
        self.header_font.configure(weight="bold")

        # --- Eingabezeile: To Do, Deadline, Liste, Hinzufügen ---
        input_frame = tk.Frame(root)
        input_frame.pack(padx=10, pady=(10, 10), fill="x")

        todo_label = tk.Label(input_frame, text="To do:")
        todo_label.grid(row=0, column=0, sticky="w", padx=(0, 5))

        # To-Do-Eingabefeld: weißer Hintergrund & schwarze Schrift
        self.entry = tk.Entry(input_frame, bg="white", fg="black")
        self.entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        self.entry.bind("<Return>", self.add_todo_event)

        deadline_label = tk.Label(input_frame, text="Deadline:")
        deadline_label.grid(row=0, column=2, sticky="w", padx=(0, 5))

        self.deadline_entry = DateEntry(
            input_frame,
            date_pattern="dd.mm.yyyy"
        )
        self.deadline_entry.grid(row=0, column=3, sticky="w", padx=(0, 10))

        list_label = tk.Label(input_frame, text="Liste:")
        list_label.grid(row=0, column=4, sticky="w", padx=(0, 5))

        # Dropdown für Ziel-Liste
        self.list_selector_var = tk.StringVar()
        self.list_selector = tk.OptionMenu(input_frame, self.list_selector_var, "")
        self.list_selector.grid(row=0, column=5, sticky="w", padx=(0, 10))

        # Hinzufügen-Button ganz rechts
        add_button = tk.Button(input_frame, text="Hinzufügen", command=self.add_todo)
        add_button.grid(row=0, column=6, sticky="e")

        # Spaltenanpassung
        input_frame.columnconfigure(1, weight=3)
        input_frame.columnconfigure(6, weight=0)

        # Anzeige aktuelle Liste / Listenübersicht
        self.current_list_label_var = tk.StringVar()
        self.current_list_label = tk.Label(root, textvariable=self.current_list_label_var)
        self.current_list_label.pack(anchor="w", padx=10, pady=(0, 5))

        # History-Filter (Liste)
        self.history_filter_frame = tk.Frame(root)
        history_filter_label = tk.Label(self.history_filter_frame, text="History-Filter (Liste):")
        history_filter_label.pack(side="left")

        self.history_filter_var = tk.StringVar()
        self.history_filter_menu = tk.OptionMenu(self.history_filter_frame, self.history_filter_var, "")
        self.history_filter_menu.pack(side="left", padx=(5, 0))

        # Standard: Filter-Leiste verstecken (nur in History-Ansicht sichtbar)
        self.history_filter_frame.pack_forget()

        # --- Scrollbarer Bereich für Tabelle ---
        list_container = tk.Frame(root)
        list_container.pack(padx=10, pady=(0, 10), fill="both", expand=True)

        self.canvas = tk.Canvas(list_container)
        self.canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_container, command=self.canvas.yview)
        scrollbar.pack(side="right", fill="y")

        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.table_frame = tk.Frame(self.canvas)
        self.table_window = self.canvas.create_window((0, 0), window=self.table_frame, anchor="nw")

        # Canvas-Größenänderungen behandeln
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        self.default_row_bg = self.table_frame.cget("bg")

        # --- Buttons unten ---
        btn_frame = tk.Frame(root)
        btn_frame.pack(padx=10, pady=10, fill="x")

        button_width = 10

        self.done_btn = tk.Button(btn_frame, text="Done / Undone", width=button_width, command=self.toggle_done)
        self.done_btn.grid(row=0, column=0, padx=5, pady=5)

        self.delete_btn = tk.Button(btn_frame, text="Delete", width=button_width, command=self.delete_todo)
        self.delete_btn.grid(row=0, column=1, padx=5, pady=5)

        self.undo_btn = tk.Button(btn_frame, text="Undo", width=button_width, command=self.undo)
        self.undo_btn.grid(row=0, column=2, padx=5, pady=5)

        self.history_btn = tk.Button(btn_frame, text="History", width=button_width, command=self.toggle_history_view)
        self.history_btn.grid(row=0, column=3, padx=5, pady=5)

        self.lists_btn = tk.Button(btn_frame, text="Lists", width=button_width, command=self.toggle_lists_view)
        self.lists_btn.grid(row=0, column=4, padx=5, pady=5)

        for i in range(5):
            btn_frame.grid_columnconfigure(i, weight=1)

        # Start
        self.update_list_selector()
        self.update_history_filter_options()
        self.update_buttons_for_view()
        self.refresh_view()

        # Wrap-Länge dynamisch anpassen
        self.table_frame.bind("<Configure>", self.on_table_resize)

    # --- Speicherfunktionen ---

    def save_state(self):
        state_copy = copy.deepcopy(self.todos)
        self.history.append(state_copy)
        if len(self.history) > 10:
            self.history.pop(0)

    def save_data(self):
        """Speichert alle Daten (Listen, Todos, aktuelle Liste) in eine JSON-Datei."""
        data = {
            "todos": self.todos,
            "lists": self.lists,
            "current_list_id": self.current_list_id
        }
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Fehler beim Speichern:", e)

    def load_data(self):
        """Lädt gespeicherte Daten aus der JSON-Datei, falls vorhanden."""
        if not os.path.exists(SAVE_FILE):
            return
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.todos = data.get("todos", [])
            loaded_lists = data.get("lists")
            if loaded_lists:
                self.lists = loaded_lists
            self.current_list_id = data.get("current_list_id", self.current_list_id)
        except Exception as e:
            print("Fehler beim Laden:", e)

    # --- Allgemeine Helfer ---

    def clear_table(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        self.row_widgets = []
        self.visible_indices = []
        self.selected_index = None

    def on_canvas_resize(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.itemconfig(self.table_window, width=event.width)

    def on_table_resize(self, event):
        # Nur To-Do-Ansicht
        if self.current_view != "todos":
            return
        total_width = event.width
        reserve = 260 if self.show_history else 80
        text_col_width = max(total_width - reserve, 100)

        for widgets in self.row_widgets:
            if not widgets:
                continue
            todo_label = widgets[0]  # immer erstes Widget = To-Do-Text
            try:
                todo_label.configure(wraplength=text_col_width)
            except tk.TclError:
                pass

    def get_list_name(self, list_id):
        for lst in self.lists:
            if lst["id"] == list_id:
                return lst["name"]
        return "Unbekannt"

    def get_list_id_by_name(self, name):
        for lst in self.lists:
            if lst["name"] == name:
                return lst["id"]
        return None

    def update_list_selector(self):
        names = [lst["name"] for lst in self.lists]
        current_name = self.get_list_name(self.current_list_id)
        self.list_selector_var.set(current_name)
        menu = self.list_selector["menu"]
        menu.delete(0, "end")
        for name in names:
            menu.add_command(label=name, command=lambda n=name: self.list_selector_var.set(n))

    def update_history_filter_options(self):
        """History-Filter-Dropdown mit 'Alle' + allen Listennamen aktualisieren."""
        names = ["Alle"] + [lst["name"] for lst in self.lists]
        current = self.history_filter_var.get()
        if current not in names:
            self.history_filter_var.set("Alle")

        menu = self.history_filter_menu["menu"]
        menu.delete(0, "end")
        for name in names:
            menu.add_command(label=name, command=lambda n=name: self.on_history_filter_change(n))

    def on_history_filter_change(self, name):
        self.history_filter_var.set(name)
        self.refresh_view()

    def parse_deadline_date(self, todo):
        """Hilfsfunktion: Deadline aus ToDo als date-Objekt, sonst sehr großes Datum."""
        datestr = todo.get("deadline", "")
        if not datestr:
            return datetime.max.date()
        try:
            return datetime.strptime(datestr, "%d.%m.%Y").date()
        except ValueError:
            return datetime.max.date()

    # --- Buttons je nach Ansicht (ToDos / Listen) ---

    def update_buttons_for_view(self):
        if self.current_view == "lists":
            # In Listenübersicht: unten gar keine Buttons
            self.done_btn.grid_remove()
            self.delete_btn.grid_remove()
            self.undo_btn.grid_remove()
            self.history_btn.grid_remove()
            self.lists_btn.grid_remove()
        else:
            # To-Do-Ansicht: alle sichtbar
            self.done_btn.grid(row=0, column=0, padx=5, pady=5)
            self.delete_btn.grid(row=0, column=1, padx=5, pady=5)
            self.undo_btn.grid(row=0, column=2, padx=5, pady=5)
            self.history_btn.grid(row=0, column=3, padx=5, pady=5)
            self.lists_btn.grid(row=0, column=4, padx=5, pady=5)
            self.delete_btn.config(text="Delete", command=self.delete_todo)

    # --- View-Umschaltung ---

    def toggle_lists_view(self):
        # Nur von To-Do-Ansicht in Listenansicht wechseln
        if self.current_view == "todos":
            self.current_view = "lists"
            self.update_buttons_for_view()
            self.refresh_view()

    def toggle_history_view(self):
        if self.current_view == "lists":
            messagebox.showinfo("Hinweis", "History ist nur in der To-Do-Ansicht verfügbar.")
            return
        self.show_history = not self.show_history
        self.history_btn.config(text="To Do's" if self.show_history else "History")
        self.refresh_view()

    # --- View-Refresh ---

    def refresh_view(self):
        if self.current_view == "lists":
            # History-Filter ausblenden
            self.history_filter_frame.pack_forget()
            self.refresh_lists_view()
        else:
            self.refresh_todos_view()

    def refresh_lists_view(self):
        self.clear_table()
        self.current_list_label_var.set("Listenübersicht")

        header_list = tk.Label(self.table_frame, text="Liste", font=self.header_font, anchor="w")
        header_list.grid(row=0, column=0, sticky="nw", padx=(0, 5), pady=(0, 5))

        header_desc = tk.Label(self.table_frame, text="Beschreibung", font=self.header_font, anchor="w")
        header_desc.grid(row=0, column=1, sticky="nw", padx=(0, 5), pady=(0, 5))

        plus_btn = tk.Button(self.table_frame, text="+", command=self.open_new_list_dialog)
        plus_btn.grid(row=0, column=2, sticky="ne", padx=(0, 0), pady=(0, 5))

        self.table_frame.grid_columnconfigure(1, weight=1)

        row = 1
        for idx, lst in enumerate(self.lists):
            name_label = tk.Label(self.table_frame, text=lst["name"], anchor="w")
            name_label.grid(row=row, column=0, sticky="nw", padx=(0, 5), pady=2)

            desc_label = tk.Label(self.table_frame, text=lst["description"], anchor="w", justify="left", wraplength=300)
            desc_label.grid(row=row, column=1, sticky="nw", padx=(0, 5), pady=2)

            row_widgets = [name_label, desc_label]
            self.visible_indices.append(idx)
            row_index = len(self.row_widgets)

            # Linksklick: Liste öffnen
            for w in row_widgets:
                w.bind("<Button-1>", lambda e, r=row_index: self.on_list_left_click(r))
                # Rechtsklick / Touchpad (Button-3 & Button-2)
                w.bind("<Button-3>", lambda e, r=row_index: self.on_list_right_click(e, r))
                w.bind("<Button-2>", lambda e, r=row_index: self.on_list_right_click(e, r))

            self.row_widgets.append(row_widgets)
            row += 1

    def refresh_todos_view(self):
        self.clear_table()

        # History-Filter nur in History-Ansicht anzeigen
        if self.show_history:
            self.history_filter_frame.pack(anchor="w", padx=10, pady=(0, 5))
            self.update_history_filter_options()
        else:
            self.history_filter_frame.pack_forget()

        self.current_list_label_var.set(f"Aktuelle Liste: {self.get_list_name(self.current_list_id)}")

        if self.show_history:
            headers = ["Liste", "To Do", "Deadline", "Erstellt am"]
            for c, h in enumerate(headers):
                tk.Label(
                    self.table_frame,
                    text=h,
                    font=self.header_font,
                    anchor="w"
                ).grid(row=0, column=c, sticky="nw", padx=(0, 5), pady=(0, 5))
            self.table_frame.grid_columnconfigure(1, weight=1)
        else:
            tk.Label(self.table_frame, text="Deadline", font=self.header_font, anchor="w").grid(
                row=0, column=0, sticky="nw", padx=(0, 5), pady=(0, 5)
            )
            tk.Label(self.table_frame, text="To Do", font=self.header_font, anchor="w").grid(
                row=0, column=1, sticky="nw", padx=(0, 0), pady=(0, 5)
            )
            self.table_frame.grid_columnconfigure(1, weight=1)

        row = 1

        if self.show_history:
            # --- History: erledigte ToDos, optional nach Liste gefiltert, nach Deadline sortiert ---
            filtered = []
            filter_name = self.history_filter_var.get()
            filter_list_id = None
            if filter_name and filter_name != "Alle":
                filter_list_id = self.get_list_id_by_name(filter_name)

            for idx, todo in enumerate(self.todos):
                if not todo.get("done"):
                    continue
                list_id = todo.get("list_id", self.current_list_id)
                if filter_list_id is not None and list_id != filter_list_id:
                    continue
                filtered.append((idx, todo))

            # Sortieren nach Deadline (aufsteigend)
            filtered.sort(key=lambda it: self.parse_deadline_date(it[1]))

            for idx, todo in filtered:
                text = todo["text"]
                deadline = todo["deadline"]
                created = todo["created_at"]
                list_id = todo.get("list_id", self.current_list_id)
                list_name = self.get_list_name(list_id)

                self.visible_indices.append(idx)
                row_widgets = []

                list_label = tk.Label(self.table_frame, text=list_name, anchor="w")
                list_label.grid(row=row, column=0, sticky="nw", padx=(0, 5), pady=2)

                todo_label = tk.Label(self.table_frame, text=text, anchor="w", justify="left", wraplength=300)
                todo_label.grid(row=row, column=1, sticky="nw", padx=(0, 5), pady=2)

                deadline_label = tk.Label(self.table_frame, text=deadline, anchor="w")
                deadline_label.grid(row=row, column=2, sticky="nw", padx=(0, 5), pady=2)

                created_label = tk.Label(self.table_frame, text=created, anchor="w")
                created_label.grid(row=row, column=3, sticky="nw", padx=(0, 0), pady=2)

                row_widgets = [todo_label, list_label, deadline_label, created_label]

                row_index = len(self.row_widgets)
                for w in row_widgets:
                    w.bind("<Button-1>", lambda e, r=row_index: self.on_row_click(r))

                self.row_widgets.append(row_widgets)
                row += 1

        else:
            # --- Offene ToDos: nur aktuelle Liste, nach Deadline sortiert ---
            filtered = []
            for idx, todo in enumerate(self.todos):
                list_id = todo.get("list_id", self.current_list_id)
                if todo.get("done"):
                    continue
                if list_id != self.current_list_id:
                    continue
                filtered.append((idx, todo))

            filtered.sort(key=lambda it: self.parse_deadline_date(it[1]))

            for idx, todo in filtered:
                text = todo["text"]
                deadline = todo["deadline"]

                self.visible_indices.append(idx)
                row_widgets = []

                deadline_label = tk.Label(self.table_frame, text=deadline, anchor="w")
                deadline_label.grid(row=row, column=0, sticky="nw", padx=(0, 5), pady=2)

                todo_label = tk.Label(self.table_frame, text=text, anchor="w", justify="left", wraplength=300)
                todo_label.grid(row=row, column=1, sticky="nw", padx=(0, 0), pady=2)

                row_widgets = [todo_label, deadline_label]

                row_index = len(self.row_widgets)
                for w in row_widgets:
                    w.bind("<Button-1>", lambda e, r=row_index: self.on_row_click(r))

                self.row_widgets.append(row_widgets)
                row += 1

        self.table_frame.update_idletasks()
        fake_event = type("Event", (), {"width": self.table_frame.winfo_width()})
        self.on_table_resize(fake_event)

    # --- Zeilenauswahl ---

    def select_row(self, row_idx):
        if row_idx < 0 or row_idx >= len(self.visible_indices):
            return
        self.selected_index = self.visible_indices[row_idx]

        for i, widgets in enumerate(self.row_widgets):
            bg = "#d9ead3" if i == row_idx else self.default_row_bg
            for w in widgets:
                try:
                    w.configure(bg=bg)
                except tk.TclError:
                    pass

    def on_row_click(self, row_idx):
        self.select_row(row_idx)

    # --- Listen-spezifische Clicks ---

    def on_list_left_click(self, row_idx):
        """Liste durch Anklicken öffnen."""
        self.select_row(row_idx)
        idx = self.get_selected_list_index()
        if idx is not None and 0 <= idx < len(self.lists):
            self.current_list_id = self.lists[idx]["id"]
            self.current_view = "todos"
            self.update_buttons_for_view()
            self.refresh_view()

    def on_list_right_click(self, event, row_idx):
        """Kontextmenü über Rechtsklick / Touchpad öffnen."""
        self.select_row(row_idx)
        try:
            self.list_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.list_menu.grab_release()

    def get_selected_list_index(self):
        if self.current_view != "lists":
            return None
        return self.selected_index

    # --- To-Do-Aktionen ---

    def add_todo_event(self, event):
        self.add_todo()

    def add_todo(self):
        text = self.entry.get().strip()
        if not text:
            return

        deadline_text = self.deadline_entry.get().strip()
        if deadline_text:
            try:
                datetime.strptime(deadline_text, "%d.%m.%Y")
            except ValueError:
                messagebox.showerror(
                    "Ungültiges Datum",
                    "Bitte die Deadline im Format TT.MM.JJJJ eingeben (z.B. 05.11.2025)."
                )
                return

        list_name = self.list_selector_var.get().strip()
        list_id = self.get_list_id_by_name(list_name) if list_name else self.current_list_id
        if list_id is None:
            list_id = self.current_list_id

        self.save_state()

        self.todos.append({
            "text": text,
            "done": False,
            "created_at": datetime.now().strftime("%d.%m.%Y"),
            "deadline": deadline_text,
            "list_id": list_id
        })

        self.entry.delete(0, tk.END)
        self.deadline_entry.set_date(datetime.today())

        self.current_list_id = list_id
        self.update_list_selector()
        self.update_history_filter_options()
        self.refresh_view()

    def toggle_done(self):
        if self.current_view == "lists":
            return
        idx = self.selected_index
        if idx is None:
            messagebox.showinfo("Hinweis", "Bitte ein To-Do auswählen.")
            return
        self.save_state()
        self.todos[idx]["done"] = not self.todos[idx]["done"]
        self.refresh_view()

    def delete_todo(self):
        if self.current_view == "lists":
            return
        idx = self.selected_index
        if idx is None:
            messagebox.showinfo("Hinweis", "Bitte ein To-Do auswählen.")
            return
        self.save_state()
        del self.todos[idx]
        self.refresh_view()

    def undo(self):
        if not self.history:
            messagebox.showinfo("Hinweis", "Keine Aktionen zum Rückgängig machen.")
            return
        self.todos = self.history.pop()
        self.refresh_view()

    # --- Listenverwaltung ---

    def open_new_list_dialog(self):
        self.open_list_dialog(mode="new")

    def open_list_dialog(self, mode="new"):
        dialog = tk.Toplevel(self.root)
        dialog.title("Neue Liste" if mode == "new" else "Liste bearbeiten")
        dialog.transient(self.root)
        dialog.grab_set()

        name_label = tk.Label(dialog, text="Name:")
        name_label.pack(anchor="w", padx=10, pady=(10, 0))
        name_entry = tk.Entry(dialog, width=40)
        name_entry.pack(fill="x", padx=10, pady=(0, 10))

        desc_label = tk.Label(dialog, text="Beschreibung:")
        desc_label.pack(anchor="w", padx=10, pady=(0, 0))
        desc_entry = tk.Entry(dialog, width=40)
        desc_entry.pack(fill="x", padx=10, pady=(0, 10))

        idx = None
        if mode == "edit":
            idx = self.get_selected_list_index()
            if idx is None or idx < 0 or idx >= len(self.lists):
                messagebox.showinfo("Hinweis", "Bitte eine Liste auswählen.")
                dialog.destroy()
                return
            lst = self.lists[idx]
            name_entry.insert(0, lst["name"])
            desc_entry.insert(0, lst["description"])

        def on_save():
            name = name_entry.get().strip()
            desc = desc_entry.get().strip()
            if not name:
                messagebox.showerror("Fehler", "Bitte einen Listennamen eingeben.")
                return
            if mode == "new":
                new_list = {"id": self.next_list_id, "name": name, "description": desc}
                self.next_list_id += 1
                self.lists.append(new_list)
                self.current_list_id = new_list["id"]
            else:
                self.lists[idx]["name"] = name
                self.lists[idx]["description"] = desc
            dialog.destroy()
            self.update_list_selector()
            self.update_history_filter_options()
            self.refresh_view()

        def on_cancel():
            dialog.destroy()

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Speichern", command=on_save).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Abbrechen", command=on_cancel).pack(side="left", padx=5)

    def edit_selected_list(self):
        self.open_list_dialog(mode="edit")

    def delete_selected_list(self):
        idx = self.get_selected_list_index()
        if idx is None or idx < 0 or idx >= len(self.lists):
            messagebox.showinfo("Hinweis", "Bitte eine Liste auswählen.")
            return
        if len(self.lists) == 1:
            messagebox.showinfo("Hinweis", "Es muss mindestens eine Liste existieren.")
            return

        lst = self.lists[idx]
        if not messagebox.askyesno("Liste löschen", f"Soll die Liste '{lst['name']}' wirklich gelöscht werden?"):
            return

        list_id = lst["id"]
        del self.lists[idx]
        self.todos = [t for t in self.todos if t.get("list_id") != list_id]

        if self.current_list_id == list_id:
            self.current_list_id = self.lists[0]["id"]

        self.update_list_selector()
        self.update_history_filter_options()
        self.refresh_view()


if __name__ == "__main__":
    root = tk.Tk()
    app = ToDoApp(root)

    # Beim Schließen Daten speichern
    def on_close():
        app.save_data()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.geometry("900x550")
    root.mainloop()
