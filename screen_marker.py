import tkinter as tk
import win32gui

MASK = "#ff00ff"

class ScreenMarker:
    def __init__(self, x=0, y=0, w=1920, h=1080):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.window = tk.Toplevel()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.attributes("-transparentcolor", MASK)
        self.window.geometry(f"{w}x{h}+{x}+{y}")
        self.window.configure(bg=MASK)
        self.canvas = tk.Canvas(self.window, width=w, height=h, bg=MASK,
                                highlightthickness=0, bd=0)
        self.canvas.pack()
        self._click_through()

    def _click_through(self):
        self.window.update_idletasks()
        hwnd = win32gui.GetParent(self.window.winfo_id())
        ex_style = win32gui.GetWindowLong(hwnd, -20)
        ex_style |= 0x20 | 0x80000 | 0x08000000 | 0x80
        win32gui.SetWindowLong(hwnd, -20, ex_style)

    def draw(self, points, highlight=None):
        self.canvas.delete("all")
        for i, (px, py) in enumerate(points):
            ax, ay = px - self.x, py - self.y
            if i == highlight:
                r = 18
                self.canvas.create_oval(ax - r, ay - r, ax + r, ay + r,
                                        outline="#00ff00", width=3)
                self.canvas.create_oval(ax - 2, ay - 2, ax + 2, ay + 2,
                                        fill="#00ff00", outline="")
            else:
                self.canvas.create_rectangle(ax - 4, ay - 4, ax + 4, ay + 4,
                                             fill="#ff0000", outline="")

    def hide(self):
        self.canvas.delete("all")