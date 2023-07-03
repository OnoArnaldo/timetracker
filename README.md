# timetracker
Simple time tracker with GUI

> The idea is to analyse the design,
> No automated test was created here.

## Installation

```shell
cd <THE-PROJECT-DIR>
python3.11 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

## Run the application

```shell
cd <THE-PROJECT-DIR>
./venv/bin/python main.py
```


## Todo:

* Propagate changes made in the models to all the forms
* OnError decorator


# TKinter Design

* the class should extend Frame or TopLevel (or anything that works as a "box").
* add the class decorator `with_modifiers` and use the function decorators 
  `bind`, `command` and `menu`.

example:
```python
import tkinter as tk
from tkinter import ttk
from gui.modifiers import with_modifiers, bind, command, menu

@with_modifiers  # This decorator makes the magic!
class MainForm(ttk.Frame):  # extending ttk Widgets avoid issues with grid
    NAME = 'NAME'
    BT_OK = 'BT_OK'
    MN_MAIN = 'MN_MAIN'
    MN_DOCUMENT = 'MN_DOCUMENT'
    
    def __init__(self, root, **kwargs):
        super().__init__(root, **kwargs)
        
        self._variables: dict[str, tk.Variable] = {}
        self._controls: dict[str, ttk.Widget] = {}  # Needed for `@command` and `@bind`
        self._menus: dict[str, tk.Menu] = {}  # Needed for `@menu`
        
        self.build()
        self.build_menu()
        self.init_position()
        self.refresh()

    def build(self):
        self._variables[self.NAME] = name = tk.StringVar()
        self._controls[self.NAME] = ttk.Entry(self, textvariable=name)
        
        self._controls[self.BT_OK] = ttk.Button(self, text='OK')
    
    def build_menu(self):
        self.master.option_add('*tearOff', tk.FALSE)

        self._menus[self.MN_MAIN] = menubar = tk.Menu(self.master)
        self._menus[self.MN_DOCUMENT] = menu_document = tk.Menu(menubar)
        menu_document.add_command(label='New')
        menu_document.add_separator()
        menu_document.add_command(label='Edit')
        menu_document.add_command(label='Delete')

        self.master['menu'] = menubar
    
    def init_position(self):
        self.grid_columnconfigure(0, weight=1)
        
        self._controls[self.NAME].grid(row=0, column=0)
        self._controls[self.BT_OK].grid(row=0, column=1)

    def refresh(self):
        pass

    @menu(MN_DOCUMENT, 'new')
    def clicked_menu_document(self):
        print('Menu New Document was pressed')

    @command(BT_OK)
    def clicked_bt_ok(self):
        print('Button OK was pressed')

    @bind('<FocusIn>', NAME)
    def focus_in_name(self, event: tk.Event):
        print(f'{event.widget._name} was pressed')
```
