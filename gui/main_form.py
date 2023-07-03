import typing as _
from datetime import datetime, timedelta

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import models as m
from db import get_db

from .utils import with_modifiers, command, bind, menu
from .info_form import TaskInfoForm

ListenerType = _.Callable[[str, 'TaskRow'], None]


@with_modifiers
class TaskRow(ttk.Frame):
    DONE = 'DONE'
    NAME = 'NAME'
    TOTAL = 'TOTAL'
    TODAY = 'TODAY'
    BT_PLAY = 'BT_PLAY'
    BT_DELETE = 'BT_DELETE'
    BT_INFO = 'BT_INFO'

    def __init__(self, root: tk.Misc, model: m.Task, listener: ListenerType = None, **kwargs) -> None:
        super().__init__(root, **kwargs)

        self.root = root  # No master
        self.model = model
        self.listener = listener

        self._controls: dict[str, ttk.Widget] = {}
        self._variables: dict[str, tk.Variable] = {}
        self._column = -1
        self._play = False
        self._play_id = None
        self._cur_entry = None

        self.build()
        self.init_position()
        self.refresh()
        self.refresh_values()

    # region Build
    @property
    def position_attributes(self):
        self._column += 1
        return {'pady': 5, 'padx': 5, 'sticky': tk.EW, 'row': 0, 'column': self._column}

    def build(self) -> None:
        style = ttk.Style()
        style.map(
            "TaskFrame.TButton",
            foreground=[("disabled", "DarkGrey")]
        )

        self._variables[self.DONE] = done = tk.BooleanVar()
        self._controls[self.DONE] = ttk.Checkbutton(self, width=1, variable=done)

        self._variables[self.NAME] = name = tk.StringVar()
        self._controls[self.NAME] = ttk.Label(self, textvariable=name)

        lb_defaults = {'width': 8}
        self._variables[self.TOTAL] = total = tk.StringVar()
        self._controls[self.TOTAL] = ttk.Label(self, textvariable=total, **lb_defaults)

        self._variables[self.TODAY] = today = tk.StringVar()
        self._controls[self.TODAY] = ttk.Label(self, textvariable=today, **lb_defaults)

        bt_defaults = {'width': 2, 'style': 'TaskFrame.TButton'}
        self._variables[self.BT_PLAY] = play = tk.StringVar(value='>')
        self._controls[self.BT_PLAY] = ttk.Button(self, textvariable=play, **bt_defaults)

        self._controls[self.BT_DELETE] = ttk.Button(self, text='X', **bt_defaults)
        self._controls[self.BT_INFO] = ttk.Button(self, text='i', **bt_defaults)

    def init_position(self) -> None:
        self.grid_columnconfigure(1, weight=1)

        self._controls[self.DONE].grid(**self.position_attributes)
        self._controls[self.NAME].grid(**self.position_attributes)
        self._controls[self.TOTAL].grid(**self.position_attributes)
        self._controls[self.TODAY].grid(**self.position_attributes)
        self._controls[self.BT_PLAY].grid(**self.position_attributes)
        self._controls[self.BT_DELETE].grid(**self.position_attributes)
        self._controls[self.BT_INFO].grid(**self.position_attributes)

    def refresh(self) -> None:
        is_gone = self.model is None
        is_play = self._play
        is_done = self._variables[self.DONE].get()

        bt_play = 'enabled' if not is_gone and not is_done else 'disabled'
        in_done = bt_delete = bt_info = 'enabled' if not is_gone and not is_play else 'disabled'

        self._controls[self.DONE].configure({'state': in_done})
        self._controls[self.BT_PLAY].configure({'state': bt_play})
        self._controls[self.BT_DELETE].configure({'state': bt_delete})
        self._controls[self.BT_INFO].configure({'state': bt_info})

    def refresh_values(self) -> None:
        if self.model:
            with get_db().session():
                self._variables[self.DONE].set(self.model.state == m.State.CONCLUDED)
                self._variables[self.NAME].set(self.model.name)
                self._variables[self.TOTAL].set(self.format_time(self.model.elapsed_seconds))
                self._variables[self.TODAY].set(self.format_time(self.model.today_seconds))

        else:
            self._variables[self.DONE].set(False)
            self._variables[self.NAME].set('')
            self._variables[self.TOTAL].set(self.format_time(0))
            self._variables[self.TODAY].set(self.format_time(0))

    def refresh_timers(self) -> None:
        with get_db().session():
            seconds = 0
            if self._cur_entry is not None:
                self._cur_entry.set_stop()
                seconds = self._cur_entry.elapsed_seconds

            total = self.model.elapsed_seconds + seconds
            today = self.model.today_seconds + seconds

        self._variables[self.TOTAL].set(self.format_time(total))
        self._variables[self.TODAY].set(self.format_time(today))
    # endregion

    # region Helpers
    def format_time(self, seconds: int) -> str:
        total = datetime(2023, 1, 1) + timedelta(seconds=seconds)
        return total.strftime('%H:%M:%S')
    # endregion

    # region Services
    def start_timer(self) -> None:
        with get_db().session() as session:
            self._cur_entry = m.TaskEntry(task_id=self.model.id, manual=False)
            self._cur_entry.set_start()
            self._cur_entry.set_stop()

            if self.model.state != m.State.INPROGRESS:
                self.model.state = m.State.INPROGRESS
                session.add(self.model)

    def stop_timer(self) -> None:
        with get_db().session() as session:
            self._cur_entry.set_stop()
            session.add(self._cur_entry)

        self._cur_entry = None

    def run_timer(self) -> None:
        if self._play:
            self.refresh_timers()
            self._play_id = self.after(1000, self.run_timer)

    def delete_task(self, project_id: int, name: str) -> bool:
        with get_db().session() as session:
            if task := m.Task.find_name(project_id, name):
                task.state = m.State.DELETED
                session.add(task)
                return True

        messagebox.showerror('Failed to delete', f'Failed to delete task {name!r}')
        return False
    # endregion

    # region Events
    @command(DONE)
    def changed_done(self) -> None:
        state = m.State.CONCLUDED if self._variables[self.DONE].get() else m.State.INPROGRESS

        with get_db().session() as session:
            self.model.state = state
            session.add(self.model)

        self.refresh()

    @command(BT_PLAY)
    def clicked_play(self) -> None:
        self._play = not self._play
        self._variables[self.BT_PLAY].set('||' if self._play else '>')

        if self._play:
            self.start_timer()
            self.run_timer()
        else:
            self.stop_timer()
            self.after_cancel(self._play_id)

        self.refresh()

        if self.listener is not None:
            self.listener('play', self)

    @command(BT_DELETE)
    def clicked_delete(self) -> None:
        with get_db().session():
            project_id = self.model.project_id
            task_name = self.model.name

        if messagebox.askyesno('Delete task', f'Do you want to delete the task {task_name}'):
            if self.delete_task(project_id, task_name):
                self.model = None
                self.refresh_values()
                self.refresh()

        if self.listener is not None:
            self.listener('delete', self)

    @command(BT_INFO)
    def clicked_info(self) -> None:
        if self.listener is not None:
            self.listener('info', self)
    # endregion


@with_modifiers
class MainForm(ttk.Frame):
    FR_TOP = 'FR_TOP'
    FR_BOTTOM = 'FR_BOTTOM'
    PROJECT = 'PROJECT'
    TASK = 'TASK'
    BT_ADD_TASK = 'BT_ADD_TASK'
    MN_MAIN = 'MN_MAIN'
    MN_REPORT = 'MN_REPORT'
    MN_PROJECT = 'MN_PROJECT'

    def __init__(self, root: tk.Tk, **kwargs) -> None:
        super().__init__(root, **kwargs)

        self.root: tk.Tk = root  # No master
        self._cur_project: m.Project | None = None
        self._controls: dict[str, ttk.Widget] = {}
        self._variables: dict[str, tk.Variable] = {}
        self._menus: dict[str, tk.Menu] = {}
        self._grid: list[ttk.Widget] = []

        self.build()
        self.build_menu()
        self.init_position()
        self.refresh_grid()
        self.refresh_projects()

    # region Build

    def build(self) -> None:
        self.root.title('Time tracker')

        self._controls[self.FR_TOP] = fr_top = ttk.Frame(self)
        self._controls[self.FR_BOTTOM] = ttk.Frame(self)

        self._variables[self.PROJECT] = project = tk.StringVar()
        self._controls[self.PROJECT] = ttk.Combobox(fr_top, textvariable=project, state='readonly')

        self._variables[self.TASK] = task = tk.StringVar()
        self._controls[self.TASK] = ttk.Entry(fr_top, textvariable=task)

        self._controls[self.BT_ADD_TASK] = ttk.Button(fr_top, text='Add')

    def build_menu(self) -> None:
        # TODO: styling
        self.root.option_add('*tearOff', tk.FALSE)

        self._menus[self.MN_MAIN] = menubar = tk.Menu(self.master)

        self._menus[self.MN_REPORT] = menu_report = tk.Menu(menubar)
        menu_report.add_command(label='Project x Date', state='disabled')
        menu_report.add_command(label='Date x Project', state='disabled')

        self._menus[self.MN_PROJECT] = menu_project = tk.Menu(menubar)
        menu_project.add_command(label='New project')
        menu_project.add_separator()
        menu_project.add_command(label='Edit project')
        menu_project.add_command(label='Delete project')

        menubar.add_cascade(menu=menu_project, label='Project')
        menubar.add_cascade(menu=menu_report, label='Report')
        self.master['menu'] = menubar

    def init_position(self) -> None:
        self.grid(row=0, column=0, sticky=tk.NSEW)
        self.grid_columnconfigure(0, weight=1)

        defaults = {'sticky': tk.EW}
        self._controls[self.FR_TOP].grid(row=0, column=0, **defaults)
        self._controls[self.FR_TOP].grid_columnconfigure(3, weight=1)

        self._controls[self.FR_BOTTOM].grid(row=1, column=0, **defaults)
        self._controls[self.FR_BOTTOM].grid_columnconfigure(0, weight=1)

        defaults = {'pady': 5, 'padx': 5, 'sticky': tk.EW}
        self._controls[self.PROJECT].grid(row=0, column=0, **defaults)
        self._controls[self.TASK].grid(row=0, column=1, **defaults)
        self._controls[self.BT_ADD_TASK].grid(row=0, column=2, **defaults)

    def refresh(self) -> None:
        has_project = self._cur_project is not None
        has_task = self._variables[self.TASK].get() != ''

        mn_project_edit = mn_project_delete = 'normal' if has_project else 'disabled'
        bt_add_task = 'enabled' if has_project and has_task else 'disabled'
        in_task = 'enabled' if has_project else 'disabled'

        self._menus[self.MN_PROJECT].entryconfig('Edit project', state=mn_project_edit)
        self._menus[self.MN_PROJECT].entryconfig('Delete project', state=mn_project_delete)

        self._controls[self.BT_ADD_TASK].configure({'state': bt_add_task})
        self._controls[self.TASK].configure({'state': in_task})

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
            if self._cur_project is not None:
                for idx, task in enumerate(self._cur_project.tasks):
                    task_frame = TaskRow(self._controls[self.FR_BOTTOM], model=task, listener=self.listener)
                    task_frame.grid(row=idx, column=0, sticky=tk.EW)
                    self._grid.append(task_frame)

    def refresh_projects(self) -> None:
        with get_db().session():
            self._controls[self.PROJECT]['values'] = [p.name for p in m.Project.find_all()]

    def refresh_all(self) -> None:
        self.refresh_projects()
        self.refresh_grid()
    # endregion

    # region Helpers
    def listener(self, event: str, row: TaskRow) -> None:
        if event == 'delete':
            row.destroy()
            self.refresh_grid()
        elif event == 'info':
            info_form = TaskInfoForm(self, row.model)
            info_form.wait_window()

            self.refresh_grid()
        else:
            print(event, row)
    # endregion

    # region Services
    def create_project(self, name: str) -> bool:
        with get_db().session() as session:
            if m.Project.find_name(name) is None:
                session.add(m.Project(name=name))
                return True

        messagebox.showerror('Cannot create project', f'The project name {name!r} already exists.')
        return False

    def edit_project(self, old_name: str, new_name: str) -> bool:
        with get_db().session() as session:
            if (m.Project.find_name(new_name) is None) and (project := m.Project.find_name(old_name)):
                project.name = new_name
                session.add(project)
                return True

        messagebox.showerror('Failed to edit project', f'Failed to change project {old_name!r} to {new_name!r}')
        return False

    def delete_project(self, name: str) -> bool:
        with get_db().session() as session:
            if project := m.Project.find_name(name):
                project.state = m.State.DELETED
                session.add(project)
                return True

        messagebox.showerror('Failed to delete project', f'Failed to delete the project {name!r}')
        return False

    def select_project(self, name: str) -> bool:
        if name == '':
            self._cur_project = None
            self._variables[self.PROJECT].set('')
            return True

        with get_db().session():
            if project := m.Project.find_name(name):
                self._cur_project = project
                self._variables[self.PROJECT].set(name)
                return True

        messagebox.showerror('Project not found', f'Project {name!r} was not found.')
        return False

    def add_task(self, project_id: int, name: str) -> bool:
        with get_db().session() as session:
            if m.Task.find_name(project_id, name) is None:
                task = m.Task(project_id=project_id, name=name)
                session.add(task)
                return True

        messagebox.showerror('Failed to create task', f'Failed to create the task {name!r}.')
        return False
    # endregion

    # region Events
    @command(BT_ADD_TASK)
    def clicked_add_task(self) -> None:
        with get_db().session():
            project_id = self._cur_project.id

        task_name = self._variables[self.TASK].get()
        if self.add_task(project_id, task_name):
            self._variables[self.TASK].set('')
            self.refresh_grid()

    @bind('<KeyRelease>', TASK)
    def key_released_task(self, event: tk.Event) -> None:
        self.refresh()

    @bind('<<ComboboxSelected>>', PROJECT)
    def selected_project(self, event: tk.Event) -> None:
        self.select_project(self._variables[self.PROJECT].get())
        self.refresh_grid()

    @menu(MN_PROJECT, 'New project')
    def clicked_new_project(self) -> None:
        if (project_name := simpledialog.askstring('New project', 'New project name:')) is not None:
            if project_name != '' and self.create_project(project_name):
                self.select_project(project_name)
                self.refresh_all()

    @menu(MN_PROJECT, 'Edit project')
    def clicked_edit_project(self) -> None:
        with get_db().session():
            cur_project_name = self._cur_project.name

        if (project_name := simpledialog.askstring(
                'Edit project',
                'Project name:',
                initialvalue=cur_project_name
        )) is not None:

            if project_name != cur_project_name and self.edit_project(cur_project_name, project_name):
                self.select_project(project_name)
                self.refresh_all()

    @menu(MN_PROJECT, 'Delete project')
    def clicked_delete_project(self) -> None:
        with get_db().session():
            cur_project_name = self._cur_project.name

        if messagebox.askyesno('Delete project',
                               f'Are you sure you want to delete the project {cur_project_name!r}'):
            if self.delete_project(cur_project_name):
                self.select_project('')
                self.refresh_all()

    # endregion
