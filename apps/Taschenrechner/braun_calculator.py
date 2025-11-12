import tkinter as tk

# -------------------------
# Farbschema (iPhone-ähnlich)
# -------------------------
COL_BG          = "#000000"   # Fenster
COL_DISPLAY_BG  = "#1c1c1e"   # Display-Hintergrund
COL_DISPLAY_FG  = "#ffffff"   # Display-Schrift

COL_NUM_BG      = "#0a0a0a"   # Zahlen-Buttons: schwarz
COL_NUM_HOVER   = "#1a1a1a"
COL_NUM_ACTIVE  = "#2a2a2a"

COL_OP_BG       = "#a5a5a5"   # Operatoren: dunkelgrau
COL_OP_HOVER    = "#b5b5b5"
COL_OP_ACTIVE   = "#c5c5c5"

COL_EQ_BG       = "#ff9f0a"   # "=": Orange
COL_EQ_HOVER    = "#ffb23f"
COL_EQ_ACTIVE   = "#e68f00"

COL_TEXT        = "#ffffff"   # Button-Schrift

PADDING = 14    # Außenabstand
GAP     = 10    # Abstand zwischen Buttons

FONT_DISPLAY = ("SF Pro Display", 38, "bold")
FONT_BTN     = ("SF Pro Text", 18, "bold")


# -------------------------
# RoundButton: Canvas-basierter runder Button
# -------------------------
class RoundButton(tk.Canvas):
    def __init__(self, master, text, bg, hover, active, command=None, **kwargs):
        super().__init__(master, highlightthickness=0, bd=0, bg=master["bg"], **kwargs)
        self._fill      = bg
        self._hover     = hover
        self._active    = active
        self._command   = command
        self._text      = text
        self._oval_id   = None
        self._text_id   = None
        self._pressed   = False
        self._radiuspad = 2

        self.bind("<Configure>", self._redraw)
        self.bind("<Enter>",     self._on_enter)
        self.bind("<Leave>",     self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _redraw(self, _evt=None):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        # Kreisgröße (Quadrat aus Mitte, mit Padding)
        side = min(w, h)
        x0 = (w - side) // 2 + self._radiuspad
        y0 = (h - side) // 2 + self._radiuspad
        x1 = x0 + side - 2*self._radiuspad
        y1 = y0 + side - 2*self._radiuspad

        self._oval_id = self.create_oval(x0, y0, x1, y1, fill=self._fill, outline=self._fill)
        self._text_id = self.create_text((w//2, h//2), text=self._text, fill=COL_TEXT, font=FONT_BTN)

    def _on_enter(self, _):
        if not self._pressed:
            self._set_fill(self._hover)

    def _on_leave(self, _):
        self._pressed = False
        self._set_fill(self._fill)

    def _on_press(self, _):
        self._pressed = True
        self._set_fill(self._active)

    def _on_release(self, _):
        was_pressed = self._pressed
        self._pressed = False
        self._set_fill(self._hover)
        if was_pressed and self._command:
            self._command()

    def _set_fill(self, color):
        if self._oval_id:
            self.itemconfigure(self._oval_id, fill=color, outline=color)

    def set_text(self, text):
        self._text = text
        if self._text_id:
            self.itemconfigure(self._text_id, text=text)


# -------------------------
# Rechenlogik
# -------------------------
def insert_symbol(symbol):
    display_var.set(display_var.get() + symbol)

def clear_all():
    display_var.set("")

def backspace():
    s = display_var.get()
    if s:
        display_var.set(s[:-1])

def calculate():
    expr = display_var.get().strip()
    if not expr:
        return
    expr = (expr
            .replace("−", "-")
            .replace("x", "*")
            .replace(",", "."))
    try:
        for ch in expr:
            if ch not in "0123456789.+-*/() ":
                raise ValueError("bad char")
        result = eval(expr, {"__builtins__": {}}, {})
        display_var.set(str(result).replace(".", ","))
    except Exception:
        display_var.set("Fehler")

def on_key(event):
    if event.char.isdigit():
        insert_symbol(event.char)
    elif event.char in [",", "."]:
        insert_symbol(",")
    elif event.char in "+-/":
        insert_symbol(event.char)
    elif event.char == "*":
        insert_symbol("x")
    elif event.keysym in ("minus", "KP_Subtract"):
        insert_symbol("−")
    elif event.keysym in ("Return", "KP_Enter"):
        calculate()
    elif event.keysym == "BackSpace":
        backspace()
    elif event.keysym in ("Escape", "Delete"):
        clear_all()


# -------------------------
# UI-Gerüst
# -------------------------
root = tk.Tk()
root.title("Taschenrechner")
root.configure(bg=COL_BG)

# Display
display_var = tk.StringVar(value="")
display = tk.Entry(
    root, textvariable=display_var,
    font=FONT_DISPLAY, bg=COL_DISPLAY_BG, fg=COL_DISPLAY_FG,
    insertbackground=COL_DISPLAY_FG, bd=0, relief="flat", justify="right"
)
display.grid(row=0, column=0, columnspan=4, padx=PADDING, pady=(PADDING, GAP), sticky="nsew")

# Grid
for c in range(4):
    root.grid_columnconfigure(c, weight=1, uniform="c")
for r in range(6):
    root.grid_rowconfigure(r, weight=1, uniform="r")

# Container pro Zelle, damit Canvas runde Buttons sauber platzieren kann
def cell(frame_row, frame_col):
    f = tk.Frame(root, bg=COL_BG)
    f.grid(row=frame_row, column=frame_col, padx=GAP//2, pady=GAP//2, sticky="nsew")
    f.grid_rowconfigure(0, weight=1)
    f.grid_columnconfigure(0, weight=1)
    return f

def make_round_button(parent, label, kind, cmd):
    """kind: 'num' | 'op' | 'eq' | 'fn' """
    if kind == "num":
        bg, hover, active = COL_NUM_BG, COL_NUM_HOVER, COL_NUM_ACTIVE
    elif kind == "op":
        bg, hover, active = COL_OP_BG, COL_OP_HOVER, COL_OP_ACTIVE
    elif kind == "eq":
        bg, hover, active = COL_EQ_BG, COL_EQ_HOVER, COL_EQ_ACTIVE
    else:  # fn
        bg, hover, active = COL_OP_BG, COL_OP_HOVER, COL_OP_ACTIVE

    rb = RoundButton(parent, text=label, bg=bg, hover=hover, active=active, command=cmd)
    rb.grid(row=0, column=0, sticky="nsew")
    return rb

# -------------------------
# Layout gemäß Vorgabe
# Zeile 1:    |     | AC | ⌫
# Zeile 2:  7 | 8 | 9 | /
# Zeile 3:  4 | 5 | 6 | x
# Zeile 4:  1 | 2 | 3 | −
# Zeile 5:  0 | , | = | +
# -------------------------

# Row 1
cell(1, 0)  # leer
cell(1, 1)  # leer
make_round_button(cell(1, 2), "AC", "fn", clear_all)
make_round_button(cell(1, 3), "⌫",  "fn", backspace)

# Row 2
make_round_button(cell(2, 0), "7", "num", lambda: insert_symbol("7"))
make_round_button(cell(2, 1), "8", "num", lambda: insert_symbol("8"))
make_round_button(cell(2, 2), "9", "num", lambda: insert_symbol("9"))
make_round_button(cell(2, 3), "/", "op",  lambda: insert_symbol("/"))

# Row 3
make_round_button(cell(3, 0), "4", "num", lambda: insert_symbol("4"))
make_round_button(cell(3, 1), "5", "num", lambda: insert_symbol("5"))
make_round_button(cell(3, 2), "6", "num", lambda: insert_symbol("6"))
make_round_button(cell(3, 3), "x", "op",  lambda: insert_symbol("x"))

# Row 4
make_round_button(cell(4, 0), "1", "num", lambda: insert_symbol("1"))
make_round_button(cell(4, 1), "2", "num", lambda: insert_symbol("2"))
make_round_button(cell(4, 2), "3", "num", lambda: insert_symbol("3"))
make_round_button(cell(4, 3), "−", "op",  lambda: insert_symbol("−"))

# Row 5
make_round_button(cell(5, 0), "0", "num", lambda: insert_symbol("0"))
make_round_button(cell(5, 1), ",", "num", lambda: insert_symbol(","))
make_round_button(cell(5, 2), "=", "eq",  calculate)
make_round_button(cell(5, 3), "+", "op",  lambda: insert_symbol("+"))

# Keyboard
root.bind("<Key>", on_key)
display.focus_set()

# Startgröße (quadratische Zellen erzeugen kreisförmige Buttons; Fenster ist responsive)
root.geometry("380x600")
root.minsize(340, 520)

root.mainloop()
