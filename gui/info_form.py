import typing as _
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import models as m
import utils
from db import get_db
from .modifiers import with_modifiers, command, bind
from .helpers import on_error, ServiceResult, OnErrorResult

ListenerType = _.Callable[[str, 'TaskRow'], None]


@with_modifiers
class EntryRow(tk.Frame):
    MANUAL = 'MANUAL'
    START_DATE = 'START_DATE'
    START_TIME = 'START_TIME'
    STOP_DATE = 'STOP_DATE'
    STOP_TIME = 'STOP_TIME'
    TIME = 'TIME'
    BT_SAVE = 'BT_SAVE'
    BT_DELETE = 'BT_DELETE'

    ALL_KEYS = (MANUAL, START_DATE, START_TIME, STOP_DATE, STOP_TIME, TIME, BT_SAVE, BT_DELETE)

    def __init__(self, root: ttk.Widget, model: m.TaskEntry, listener: ListenerType, **kwargs) -> None:
        super().__init__(root, **kwargs)

        self.root = root
        self.model = model
        self.listener = listener

        self._controls: dict[str, ttk.Widget] = {}
        self._variables: dict[str, tk.Variable] = {}
        self._changed: list[str] = []

        self.build()
        self.init_position()
        self.refresh()
        self.refresh_values()

    # region Build
    def build(self) -> None:
        style = ttk.Style(self)
        style.map(
            "EntryRow.TButton",
            foreground=[("disabled", "DarkGrey")]
        )

        defaults = {'width': 1}
        self._variables[self.MANUAL] = manual = tk.BooleanVar()
        self._controls[self.MANUAL] = ttk.Checkbutton(self, variable=manual, state='disabled', **defaults)

        defaults = {'width': 10}
        self._variables[self.START_DATE] = start_date = tk.StringVar()
        self._controls[self.START_DATE] = ttk.Entry(self, textvariable=start_date, name=self.START_DATE.lower(), **defaults)

        self._variables[self.START_TIME] = start_time = tk.StringVar()
        self._controls[self.START_TIME] = ttk.Entry(self, textvariable=start_time, name=self.START_TIME.lower(), **defaults)

        self._variables[self.STOP_DATE] = stop_date = tk.StringVar()
        self._controls[self.STOP_DATE] = ttk.Entry(self, textvariable=stop_date, name=self.STOP_DATE.lower(), **defaults)

        self._variables[self.STOP_TIME] = stop_time = tk.StringVar()
        self._controls[self.STOP_TIME] = ttk.Entry(self, textvariable=stop_time, name=self.STOP_TIME.lower(), **defaults)

        self._variables[self.TIME] = time = tk.StringVar()
        self._controls[self.TIME] = ttk.Label(self, textvariable=time, **defaults)

        # defaults = {'width': 1}
        defaults = {'width': 1, 'style': 'EntryRow.TButton'}
        self._controls[self.BT_SAVE] = ttk.Button(self, text='V', **defaults)
        self._controls[self.BT_DELETE] = ttk.Button(self, text='X', **defaults)

    def init_position(self) -> None:
        defaults = {'pady': 1, 'padx': 1, 'row': 0, 'sticky': tk.EW}
        self._controls[self.MANUAL].grid(column=0, **defaults)
        self._controls[self.START_DATE].grid(column=1, **defaults)
        self._controls[self.START_TIME].grid(column=2, **defaults)
        self._controls[self.STOP_DATE].grid(column=3, **defaults)
        self._controls[self.STOP_TIME].grid(column=4, **defaults)
        self._controls[self.TIME].grid(column=5, **defaults)
        self._controls[self.BT_SAVE].grid(column=6, **defaults)
        self._controls[self.BT_DELETE].grid(column=7, **defaults)

    def refresh(self) -> None:
        if self.model is None:
            self._controls[self.START_DATE].configure({'state': 'disabled'})
            self._controls[self.START_TIME].configure({'state': 'disabled'})
            self._controls[self.STOP_DATE].configure({'state': 'disabled'})
            self._controls[self.STOP_TIME].configure({'state': 'disabled'})
            self._controls[self.BT_SAVE].configure({'state': 'disabled'})
            self._controls[self.BT_DELETE].configure({'state': 'disabled'})
        else:
            bt_save = 'enabled' if len(self._changed) != 0 else 'disabled'
            self._controls[self.START_DATE].configure({'state': 'enabled'})
            self._controls[self.START_TIME].configure({'state': 'enabled'})
            self._controls[self.STOP_DATE].configure({'state': 'enabled'})
            self._controls[self.STOP_TIME].configure({'state': 'enabled'})
            self._controls[self.BT_SAVE].configure({'state': bt_save})
            self._controls[self.BT_DELETE].configure({'state': 'enabled'})

    def refresh_values(self) -> None:
        self._changed.clear()

        if self.model is None:
            self._variables[self.MANUAL].set(value=False)
            self._variables[self.START_DATE].set(value='01-01-2000')
            self._variables[self.START_TIME].set(value='00:00:00')
            self._variables[self.STOP_DATE].set(value='01-01-2000')
            self._variables[self.STOP_TIME].set(value='00:00:00')
            self._variables[self.TIME].set(value='00:00:00')
        else:
            with get_db().session():
                self._variables[self.MANUAL].set(value=self.model.manual)
                self._variables[self.START_DATE].set(value=self.model.start.strftime('%d-%m-%Y'))
                self._variables[self.START_TIME].set(value=self.model.start.strftime('%H:%M:%S'))
                self._variables[self.STOP_DATE].set(value=self.model.stop.strftime('%d-%m-%Y'))
                self._variables[self.STOP_TIME].set(value=self.model.stop.strftime('%H:%M:%S'))
                self._variables[self.TIME].set(value=self.model.elapsed_time)
    # endregion

    # region Services
    @on_error('Failed to delete the entry')
    def delete_entry(self, entry_id: int) -> OnErrorResult:
        with get_db().session() as session:
            if entry := m.TaskEntry.find(entry_id):
                session.delete(entry)
                return entry_id

        return False, entry_id, 'Failed to delete the entry.'

    @on_error('Failed to save the entry.')
    def save_entry(self, entry_id: int, task_id: int, start: datetime, stop: datetime) -> OnErrorResult:
        with get_db().session() as session:
            entry = m.TaskEntry.find(entry_id) or m.TaskEntry(task_id=task_id)
            entry.manual = True
            entry.start = start
            entry.stop = stop

            session.add(entry)
            return entry.id
    # endregion

    # region Events
    @command(BT_SAVE)
    def clicked_save(self) -> None:
        with get_db().session():
            entry_id: int = self.model.id
            task_id: int = self.model.task_id

        date = self._variables[self.START_DATE].get()
        time = self._variables[self.START_TIME].get()
        start = datetime.strptime(f'{date} {time}', '%d-%m-%Y %H:%M:%S')

        date = self._variables[self.STOP_DATE].get()
        time = self._variables[self.STOP_TIME].get()
        stop = datetime.strptime(f'{date} {time}', '%d-%m-%Y %H:%M:%S')

        result: ServiceResult
        if result := self.save_entry(entry_id, task_id, start, stop):
            with get_db().session():
                self.model = m.TaskEntry.find(result.record_id)

            self.refresh_values()
            self.refresh()

        result.show_message()

        if callable(self.listener):
            self.listener('save', self)

    @command(BT_DELETE)
    def clicked_delete(self) -> None:
        with get_db().session():
            entry_id = self.model.id

        if messagebox.askyesno('Delete row', 'Do you want to delete the entry?'):
            result: ServiceResult
            if result := self.delete_entry(entry_id):
                self.model = None
                self.refresh_values()
                self.refresh()

            result.show_message()

        if callable(self.listener):
            self.listener('delete', self)

    @bind('<FocusIn>', START_DATE)
    @bind('<FocusIn>', START_TIME)
    @bind('<FocusIn>', STOP_DATE)
    @bind('<FocusIn>', STOP_TIME)
    def focus_in(self, event: tk.Event) -> None:
        event.widget.select_range(0, tk.END)

    @bind('<FocusOut>', START_DATE)
    @bind('<FocusOut>', STOP_DATE)
    def focus_out_date(self, event: tk.Event) -> None:
        name: str = event.widget._name
        if name in self._changed:
            value: tk.Variable = self._variables[name.upper()]

            date = value.get()
            value.set(utils.dateformat(date))

    @bind('<FocusOut>', START_TIME)
    @bind('<FocusOut>', STOP_TIME)
    def focus_out_time(self, event: tk.Event) -> None:
        name: str = event.widget._name
        if name in self._changed:
            value: tk.Variable = self._variables[name.upper()]

            date = value.get()
            value.set(utils.timeformat(date))

    @bind('<KeyRelease>', START_DATE)
    @bind('<KeyRelease>', START_TIME)
    @bind('<KeyRelease>', STOP_DATE)
    @bind('<KeyRelease>', STOP_TIME)
    def changed(self, event: tk.Event):
        if event.keysym != 'Tab':
            self._changed.append(event.widget._name)
            self.refresh()
    # endregion


@with_modifiers
class TaskInfoForm(tk.Toplevel):
    PROJECT_NAME = 'PROJECT_NAME'
    NAME = 'NAME'
    FR_TOP = 'FR_TOP'
    FR_BOTTOM = 'FR_BOTTOM'
    BT_SAVE_TASK = 'BT_SAVE_TASK'
    BT_ADD_ENTRY = 'BT_ADD_ENTRY'
    BT_REFRESH = 'BT_REFRESH'

    def __init__(self, root: tk.Tk | ttk.Frame, model: m.Task, **kwargs) -> None:
        super().__init__(root, **kwargs)

        self.root = root
        self.model = model

        self._controls: dict[str, ttk.Widget] = {}
        self._variables: dict[str, tk.Variable] = {}
        self._grid: list[EntryRow] = []

        self.build()
        self.init_position()
        self.refresh_grid()
        self.refresh_values()

    # region Build
    def build(self) -> None:
        with get_db().session():
            self.title(f'Information: {self.model.project.name} - {self.model.name}')

        self._controls[self.FR_TOP] = top = ttk.Frame(self)
        self._controls[self.FR_BOTTOM] = ttk.Frame(self)

        self._variables[self.PROJECT_NAME] = proj_name = tk.StringVar()
        self._controls[self.PROJECT_NAME] = ttk.Label(top, textvariable=proj_name, font=("Arial", 25))

        self._variables[self.NAME] = name = tk.StringVar()
        self._controls[self.NAME] = ttk.Entry(top, textvariable=name)

        self._controls[self.BT_SAVE_TASK] = ttk.Button(top, text='Save')
        self._controls[self.BT_ADD_ENTRY] = ttk.Button(top, text='Add')
        self._controls[self.BT_REFRESH] = ttk.Button(top, text='Refresh')

    def init_position(self) -> None:
        # Bring to top
        self.attributes("-topmost", True)
        self.attributes("-topmost", False)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)

        self._controls[self.FR_TOP].grid(row=0, column=1, sticky=tk.NSEW)
        self._controls[self.FR_BOTTOM].grid(row=1, column=1, sticky=tk.NSEW)

        defaults = {'pady': 5, 'padx': 5, 'sticky': tk.EW}
        self._controls[self.PROJECT_NAME].grid(row=0,column=0, columnspan=3, **defaults)

        self._controls[self.NAME].grid(row=1,column=0, **defaults)
        self._controls[self.BT_SAVE_TASK].grid(row=1,column=1, **defaults)
        self._controls[self.BT_ADD_ENTRY].grid(row=1,column=2, **defaults)
        self._controls[self.BT_REFRESH].grid(row=1,column=3, **defaults)

    def refresh(self) -> None:
        pass

    def refresh_grid(self) -> None:
        self.clean_grid()
        self.populate_grid()
        self.refresh()

    def clean_grid(self) -> None:
        for row in self._grid:
            row.destroy()
        self._grid.clear()

    def populate_grid(self) -> None:
        with get_db().session():
            for idx, entry in enumerate(self.model.entries):
                entry_row = EntryRow(self._controls[self.FR_BOTTOM], model=entry, listener=self.listener)
                entry_row.grid(row=idx, column=0, sticky=tk.EW)
                self._grid.append(entry_row)

    def refresh_values(self) -> None:
        with get_db().session():
            self._variables[self.PROJECT_NAME].set(self.model.project.name)
            self._variables[self.NAME].set(self.model.name)
    # endregion

    # region Helpers
    def listener(self, event: str, row: EntryRow) -> None:
        if event == 'delete':
            row.destroy()
            self.refresh_grid()
        else:
            print(f'Info: {event}: {row}')
    # endregion

    # region Services
    def add_entry(self) -> bool:
        with get_db().session():
            entry = m.TaskEntry(task_id=self.model.id, manual=True)
            entry.set_start()
            entry.set_stop()

        entry_row = EntryRow(self._controls[self.FR_BOTTOM], entry, self.listener)
        entry_row.grid(row=len(self._grid), column=0, sticky=tk.EW)
        self._grid.append(entry_row)
        return True

    def save_task(self, task_id: int, task_name: str) -> bool:
        with get_db().session() as session:
            if entry := m.Task.find(task_id):
                entry.name = task_name
                session.add(entry)
                return True

        messagebox.showerror('Failed to save task', 'Failed to save the task.')
        return False
    # endregion

    # region Events
    @command(BT_REFRESH)
    def clicked_refresh(self) -> None:
        self.refresh_grid()

    @command(BT_ADD_ENTRY)
    def clicked_add_entry(self) -> None:
        self.add_entry()

    @command(BT_SAVE_TASK)
    def clicked_save_task(self) -> None:
        with get_db().session():
            task_id = self.model.id

        task_name = self._variables[self.NAME].get()

        if self.save_task(task_id, task_name):
            self.refresh_values()
    # endregion
