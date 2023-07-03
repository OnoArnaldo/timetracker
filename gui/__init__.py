import typing as _
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import models
import models as m
import db
import utils


def build_root() -> tk.Tk:
    root = tk.Tk()
    root.grid_columnconfigure(0, weight=1)
    return root


class TaskEntryFrame(ttk.Frame):
    def __init__(self, root: tk.Misc | None = ..., *, model: m.TaskEntry, listener: _.Any = None, **kwargs):
        super().__init__(root, **kwargs)

        self.model = model
        self.listener = listener

        self.manual = tk.BooleanVar()
        self.start_date = tk.StringVar()
        self.start_time = tk.StringVar()
        self.stop_date = tk.StringVar()
        self.stop_time = tk.StringVar()
        self.time = tk.StringVar()

        self._cur_col = -1
        self._controls: dict[str, ttk.Widget] = {}

        self.build()
        self.init_position()
        self.refresh()

    @property
    def grid_defaults(self) -> dict:
        self._cur_col += 1
        return {'pady': 1, 'padx': 1, 'row': 0, 'column': self._cur_col, 'sticky': tk.EW}

    def build(self) -> None:
        self.grid_columnconfigure(5, weight=1)

        defaults = {'width': 10}
        self._controls['manual'] = ttk.Checkbutton(self, variable=self.manual, width=1, state='disabled')
        self._controls['start_date'] = ttk.Entry(self, textvariable=self.start_date, name='start_date', **defaults)
        self._controls['start_time'] = ttk.Entry(self, textvariable=self.start_time, name='start_time', **defaults)
        self._controls['stop_date'] = ttk.Entry(self, textvariable=self.stop_date, name='stop_date', **defaults)
        self._controls['stop_time'] = ttk.Entry(self, textvariable=self.stop_time, name='stop_time', **defaults)

        self._controls['time'] = ttk.Label(self, textvariable=self.time)

        defaults = {'width': 1}
        self._controls['bt_save'] = ttk.Button(self, text='V', command=self.clicked_save, **defaults)
        self._controls['bt_delete'] = ttk.Button(self, text='X', command=self.clicked_delete, **defaults)

        self._controls['start_date'].bind('<FocusIn>', self.onfocus_entry)
        self._controls['start_time'].bind('<FocusIn>', self.onfocus_entry)
        self._controls['stop_date'].bind('<FocusIn>', self.onfocus_entry)
        self._controls['stop_time'].bind('<FocusIn>', self.onfocus_entry)

        self._controls['start_date'].bind('<FocusOut>', self.outfocus_date)
        self._controls['start_time'].bind('<FocusOut>', self.outfocus_time)
        self._controls['stop_date'].bind('<FocusOut>', self.outfocus_date)
        self._controls['stop_time'].bind('<FocusOut>', self.outfocus_time)

    def init_position(self) -> None:
        self._controls['manual'].grid(**self.grid_defaults)
        self._controls['start_date'].grid(**self.grid_defaults)
        self._controls['start_time'].grid(**self.grid_defaults)
        self._controls['stop_date'].grid(**self.grid_defaults)
        self._controls['stop_time'].grid(**self.grid_defaults)
        self._controls['time'].grid(**self.grid_defaults)
        self._controls['bt_save'].grid(**self.grid_defaults)
        self._controls['bt_delete'].grid(**self.grid_defaults)

    def refresh(self) -> None:
        self.manual.set(value=self.model.manual)
        self.start_date.set(value=self.model.start.strftime('%d-%m-%Y'))
        self.start_time.set(value=self.model.start.strftime('%H:%M:%S'))
        self.stop_date.set(value=self.model.stop.strftime('%d-%m-%Y'))
        self.stop_time.set(value=self.model.stop.strftime('%H:%M:%S'))
        self.time.set(value=self.model.elapsed_time)

    def onfocus_entry(self, event: tk.Event) -> None:
        event.widget.select_range(0, tk.END)

    def outfocus_date(self, event: tk.E) -> None:
        value: tk.StringVar = getattr(self, event.widget._name)
        date = value.get()
        value.set(utils.dateformat(date))

    def outfocus_time(self, event: tk.E) -> None:
        value: tk.StringVar = getattr(self, event.widget._name)
        time = value.get()
        value.set(utils.timeformat(time))

    def clicked_save(self) -> None:
        model = self.model if self.model.id is not None else None

        with db.get_db().session(model) as session:
            start = f'{self.start_date.get()} {self.start_time.get()}'
            stop = f'{self.stop_date.get()} {self.stop_time.get()}'

            self.model.manual = True
            self.model.start = datetime.datetime.strptime(start, '%d-%m-%Y %H:%M:%S')
            self.model.stop = datetime.datetime.strptime(stop, '%d-%m-%Y %H:%M:%S')

            session.add(self.model)

        self.refresh()

    def clicked_delete(self) -> None:
        if messagebox.askyesno('Delete entry', 'Are you sure you want to delete this entry'):
            self.model.state = m.State.DELETED

            with db.get_db().session(self.model) as session:
                session.delete(self.model)
            self.refresh()

            if hasattr(self.listener, 'event_called'):
                self.listener.event_called('delete', self)


class TaskInfoWin(tk.Toplevel):
    def __init__(self, master: tk.Misc, model: m.Task, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.model = model
        self.task_name = tk.StringVar(value=model.name)

        self._controls: dict[str, ttk.Widget] = {}
        self._grid: list[ttk.Widget] = []

        self.build()
        self.init_position()
        self.populate_grid()

    @property
    def grid_defaults(self) -> dict:
        return {'pady': 5, 'padx': 5, 'sticky': tk.EW}

    def build(self) -> None:
        self.title(f'Information: {self.model.project.name} - {self.model.name}')
        self.attributes("-topmost", True)
        self.grab_set()  # opposite to grab_release

        self._controls['top'] = top = ttk.Frame(self)
        self._controls['bottom'] = ttk.Frame(self)

        self._controls['project_name'] = ttk.Label(top, text=self.model.project.name)
        self._controls['task_name'] = ttk.Entry(top, textvariable=self.task_name)
        self._controls['bt_save'] = ttk.Button(top, text='Save', command=self.clicked_save)
        self._controls['bt_add'] = ttk.Button(top, text='Add', command=self.clicked_add)

    def init_position(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)

        self._controls['top'].grid(row=0, column=1, **self.grid_defaults)
        self._controls['bottom'].grid(row=1, column=1, **self.grid_defaults)

        self._controls['project_name'].grid(row=0, column=0, **self.grid_defaults)
        self._controls['task_name'].grid(row=1, column=0, **self.grid_defaults)
        self._controls['bt_save'].grid(row=1, column=1, **self.grid_defaults)
        self._controls['bt_add'].grid(row=1, column=2, **self.grid_defaults)

    def clean_grid(self):
        for row in self._grid:
            row.destroy()

    def populate_grid(self) -> None:
        with db.get_db().session():
            for idx, entry in enumerate(self.model.entries):
                entry_frame = TaskEntryFrame(self._controls['bottom'], model=entry, listener=self)
                entry_frame.grid(row=idx, column=0, sticky=tk.EW)
                self._grid.append(entry_frame)

    def event_called(self, event: str, row: TaskEntryFrame) -> None:
        if event == 'delete':
            self.clean_grid()
            self.populate_grid()

    def clicked_save(self) -> None:
        with db.get_db().session(self.model) as session:
            self.model.name = self.task_name.get()
            session.add(self.model)

    def clicked_add(self) -> None:
        entry = models.TaskEntry(task_id=self.model.id, manual=True)
        entry.set_start()
        entry.set_stop()
        entry_frame = TaskEntryFrame(self._controls['bottom'], model=entry, listener=self)
        entry_frame.grid(row=len(self._grid)+1, column=0, sticky=tk.EW)
        self._grid.append(entry_frame)


class TaskFrame(ttk.Frame):
    def __init__(self, root: tk.Misc | None = ..., *, model: m.Task, listener: _.Any = None, **kwargs):
        super().__init__(root, **kwargs)

        self.model = model
        self.listener = listener
        self.done = tk.BooleanVar(value=model.state == m.State.CONCLUDED)
        self.name = tk.StringVar(value=model.name)
        self.total = tk.StringVar(value='00:00:00')
        self.today = tk.StringVar(value='00:00:00')
        self.play = tk.StringVar(value='>')

        self._cur_col = -1
        self._cur_entry: m.TaskEntry | None = None
        self._cur_seconds: int = 0
        self._controls: dict[str, ttk.Widget] = {}
        self._play = False
        self._freeze = False

        self.build()
        self.init_position()
        self.refresh()

    @property
    def freeze(self) -> bool:
        return self._freeze

    @freeze.setter
    def freeze(self, value: bool) -> None:
        self._freeze = value
        self.refresh()

    @property
    def grid_defaults(self) -> dict:
        self._cur_col += 1
        return {'pady': 5, 'padx': 5, 'row': 0, 'column': self._cur_col, 'sticky': tk.EW}

    def build(self) -> None:
        style = ttk.Style()
        style.map(
            "TaskFrame.TButton",
            foreground=[("disabled", "DarkGrey")]
        )
        defaults_button = {'width': 2, 'style': 'TaskFrame.TButton'}

        self._controls['done'] = ttk.Checkbutton(self, text='',
                                                 variable=self.done,
                                                 command=self.modified_done)
        self._controls['name'] = ttk.Label(self, textvariable=self.name, width=20)
        self._controls['total'] = ttk.Label(self, textvariable=self.total, width=8)
        self._controls['today'] = ttk.Label(self, textvariable=self.today, width=8)
        self._controls['bt_play'] = ttk.Button(self, textvariable=self.play,
                                               command=self.clicked_ok,
                                               **defaults_button)
        self._controls['bt_delete'] = ttk.Button(self, text='X',
                                                 command=self.clicked_delete,
                                                 **defaults_button)
        self._controls['bt_info'] = ttk.Button(self, text='i',
                                               command=self.clicked_info,
                                               **defaults_button)

        self.grid_columnconfigure(1, weight=1, minsize=100)  # Expand the name column

    def init_position(self) -> None:
        self._controls['done'].grid(**self.grid_defaults)
        self._controls['name'].grid(**self.grid_defaults)
        self._controls['total'].grid(**self.grid_defaults)
        self._controls['today'].grid(**self.grid_defaults)
        self._controls['bt_play'].grid(**self.grid_defaults)
        self._controls['bt_delete'].grid(**self.grid_defaults)
        self._controls['bt_info'].grid(**self.grid_defaults)

    def refresh(self) -> None:
        is_done, is_play, is_freeze = self.done.get(), self._play, self._freeze

        bt_play_state = 'enabled' if not is_done and not is_freeze else 'disabled'
        bt_delete_state = 'enabled' if not is_play and not is_freeze else 'disabled'
        done_state = 'enabled' if not is_play and not is_freeze else 'disabled'
        play_value = '||' if is_play else '>'

        self._controls['bt_play'].configure({'state': bt_play_state})
        self._controls['bt_delete'].configure({'state': bt_delete_state})
        self._controls['done'].configure({'state': done_state})
        self.play.set(play_value)

        self.set_timers()

    def start_timer(self) -> None:
        if not self._play:
            self._cur_seconds = 0
            self._cur_entry = m.TaskEntry()
            self._cur_entry.set_start()
            self._cur_entry.set_stop()

            if self.model.state != m.State.INPROGRESS:
                self.model.state = m.State.INPROGRESS

                with db.get_db().session(self.model) as session:
                    session.add(self.model)

            self.after(1000, self.run_timer)
            self._play = True

    def stop_timer(self) -> None:
        if self._play:
            self._cur_entry.set_stop()
            self.model.entries.append(self._cur_entry)

            with db.get_db().session(self.model) as session:
                session.add(self.model)

            self._cur_entry = None
            self._play = False

    def set_timers(self) -> None:
        seconds = 0
        if self._cur_entry is not None:
            self._cur_entry.set_stop()
            seconds = self._cur_entry.elapsed_seconds

        total = self.model.elapsed_seconds + seconds
        total = datetime.datetime(2023, 1, 1) + datetime.timedelta(seconds=total)

        today = self.model.today_seconds + seconds
        today = datetime.datetime(2023, 1, 1) + datetime.timedelta(seconds=today)

        self.total.set(total.strftime('%H:%M:%S'))
        self.today.set(today.strftime('%H:%M:%S'))

    def modified_done(self) -> None:
        self.model.state = m.State.CONCLUDED if self.done else m.State.INPROGRESS

        with db.get_db().session(self.model) as session:
            session.add(self.model)

        self.refresh()

    def clicked_ok(self) -> None:
        if self._play:
            self.stop_timer()
        else:
            self.start_timer()

        self.refresh()

        if hasattr(self.listener, 'event_called'):
            self.listener.event_called('play' if self._play else 'pause', self)

    def clicked_delete(self) -> None:
        if messagebox.askyesno('Delete task', 'Are you sure you want to delete this task'):
            self.model.state = m.State.DELETED

            with db.get_db().session(self.model) as session:
                session.add(self.model)
            self.refresh()

            if hasattr(self.listener, 'event_called'):
                self.listener.event_called('delete', self)

    def clicked_info(self) -> None:
        info = TaskInfoWin(self, self.model)
        info.wait_window()
        self.refresh()

        if hasattr(self.master, 'event_called'):
            self.master.event_called('info', self)

    def run_timer(self) -> None:
        if self._play:
            self.set_timers()
            self.after(1000, self.run_timer)


class MainFrame(ttk.Frame):
    def __init__(self, root: tk.Misc | None = ..., **kwargs):
        super().__init__(root, **kwargs)

        self.project = tk.StringVar()
        self.task = tk.StringVar()

        self._cur_project: m.Project | None = None
        self._controls: dict[str, ttk.Widget] = {}
        self._grid: list[TaskFrame] = []
        self._menu: dict[str, tk.Menu] = {}
        self._play: bool = False

        self.build_menu()
        self.build()
        self.init_position()
        self.set_projects()
        self.refresh()

    @property
    def grid_defaults(self) -> dict:
        return {'pady': 5, 'padx': 5, 'sticky': tk.EW}

    def build(self) -> None:
        style = ttk.Style()
        style.map(
            "MainFrame.TButton",
            foreground=[("disabled", "DarkGrey")]
        )

        self.master.title('Time tracker')
        self.master.option_add('*tearOff', tk.FALSE)

        self._controls['top'] = top = ttk.Frame(self)
        self._controls['bottom'] = bottom = ttk.Frame(self)

        self._controls['project'] = ttk.Combobox(top, textvariable=self.project)
        self._controls['task'] = ttk.Entry(top, textvariable=self.task)
        self._controls['bt_add_task'] = ttk.Button(top,
                                                   text='Add',
                                                   style='MainFrame.TButton',
                                                   command=self.clicked_add_task)

        self.master.protocol("WM_DELETE_WINDOW", self.closing_window)
        self.task.trace_add('write', self.modified_task)
        self._controls['project'].bind('<<ComboboxSelected>>', func=self.selected_project)

        self.grid_columnconfigure(0, weight=1)
        top.grid_columnconfigure(1, weight=1, minsize=100)
        bottom.grid_columnconfigure(0, weight=1)

    def build_menu(self) -> None:
        self._menu['menubar'] = menubar = tk.Menu(self.master)

        self._menu['report'] = menu_report = tk.Menu(menubar)
        menu_report.add_command(label='Project x Date', command=lambda: None, state='disabled')
        menu_report.add_command(label='Date x Project', command=lambda: None, state='disabled')

        self._menu['project'] = menu_project = tk.Menu(menubar)
        menu_project.add_command(label='Edit project', command=self.clicked_edit_project)
        menu_project.add_command(label='New project', command=self.clicked_create_project)
        menu_project.add_separator()
        menu_project.add_command(label='Delete project', command=self.clicked_delete_project)

        menubar.add_cascade(menu=menu_project, label='Project')
        menubar.add_cascade(menu=menu_report, label='Report')
        self.master['menu'] = menubar

    def init_position(self) -> None:
        self.grid(row=0, column=0, sticky=tk.NSEW)

        self._controls['top'].grid(row=0, column=0, **self.grid_defaults)
        self._controls['bottom'].grid(row=1, column=0, **self.grid_defaults)

        self._controls['project'].grid(row=0, column=0, **self.grid_defaults)
        self._controls['task'].grid(row=0, column=1, **self.grid_defaults)
        self._controls['bt_add_task'].grid(row=0, column=2, **self.grid_defaults)

    def refresh(self) -> None:
        has_project, has_task, is_play = self.project.get() != '', self.task.get() != '', self._play

        bt_add_task_state = 'enabled' if has_project and has_task and not is_play else 'disabled'
        task_state = 'enabled' if has_project and not is_play else 'disabled'
        project_state = 'readonly' if not is_play else 'disabled'
        menu_delete_project_state = 'normal' if has_project and not is_play else 'disabled'
        menu_create_project_state = 'normal' if not is_play else 'disabled'
        menu_edit_project_state = 'normal' if has_project and not is_play else 'disabled'

        self._controls['bt_add_task'].configure({'state': bt_add_task_state})
        self._controls['task'].configure({'state': task_state})
        self._controls['project'].configure({'state': project_state})

        self._menu['project'].entryconfig('Delete project', state=menu_delete_project_state)
        self._menu['project'].entryconfig('New project', state=menu_create_project_state)
        self._menu['project'].entryconfig('Edit project', state=menu_edit_project_state)

    def set_projects(self) -> None:
        combo: ttk.Combobox = self._controls['project']
        with db.get_db().session():
            combo['values'] = [p.name for p in m.Project.find_all()]
        combo.state(['readonly'])

    def clean_grid(self) -> None:
        for widget in self._grid:
            widget.destroy()
        self._grid.clear()

    def populate_grid(self) -> None:
        with db.get_db().session():
            project = m.Project.find_name(self.project.get())
            self._cur_project = project

            if project is not None:
                for idx, task in enumerate(project.tasks):
                    task_frame = TaskFrame(self._controls['bottom'], model=task, listener=self)
                    task_frame.grid(row=idx, column=0, sticky=tk.EW)
                    self._grid.append(task_frame)

    def refresh_grid(self):
        self.clean_grid()
        self.populate_grid()
        self.refresh()

    def selected_project(self, event: tk.Event) -> None:
        self.refresh_grid()

    def event_called(self, event: str, row: TaskFrame) -> None:
        match event:
            case 'delete':
                self._grid.remove(row)
                row.destroy()
            case 'play' | 'pause':
                self._play = True if event == 'play' else False
                for elem in self._grid:
                    if elem is not row:
                        elem.freeze = self._play

        self.refresh()

    def clicked_add_task(self) -> None:
        with db.get_db().session(self._cur_project) as session:
            if m.Task.find_name(self._cur_project.id, self.task.get()) is None:
                self._cur_project.tasks.append(m.Task(name=self.task.get()))
                session.add(self._cur_project)
                self.task.set('')
                self.refresh_grid()
            else:
                messagebox.showerror('Failed to create Task', 'The task name can not be duplicated.')

    def clicked_edit_project(self) -> None:
        with db.get_db().session() as session:
            if name := simpledialog.askstring('Edit project', 'Project Name', initialvalue=self._cur_project.name):
                self._cur_project.name = name
                session.add(self._cur_project)

        self.project.set(name)
        self.set_projects()
        self.refresh()

    def clicked_create_project(self) -> None:
        with db.get_db().session() as session:
            if name := simpledialog.askstring('New project', 'What is the new project name?'):
                if not m.Project.find_name(name):
                    project = m.Project(name=name)
                    session.add(project)
                else:
                    messagebox.showerror('Failed to create project', f'The project name {name!r} already exists.')
                    return

        self.project.set(name)
        self.set_projects()
        self.refresh_grid()

    def clicked_delete_project(self) -> None:
        if (self._cur_project
                and simpledialog.askstring('Delete project',
                                           f'Do you want to delete the project '
                                           f'{self._cur_project.name!r}')):
            with db.get_db().session() as session:
                self._cur_project.state = m.State.DELETED
                session.add(self._cur_project)

        self.project.set('')
        self.set_projects()
        self.refresh_grid()

    def modified_task(self, *args) -> None:
        self.refresh()

    def closing_window(self) -> None:
        if self._play:
            for row in self._grid:
                row.stop_timer()

        self.master.destroy()
