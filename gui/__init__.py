import tkinter as tk


def build_root() -> tk.Tk:
    root = tk.Tk()
    root.grid_columnconfigure(0, weight=1)
    return root

