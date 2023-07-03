import typing as _
from functools import wraps

if _.TYPE_CHECKING:
    from tkinter import Event, ttk


BINDERS_FUNC = '''\
def init_binders(self) -> None:
    """Assign binders, there should be an attribute called '_controls'."""
    if hasattr(self, '_controls'):
{calls}
'''
BINDERS_CALL = "        self._controls['{control}'].bind('{event}', self.{command})"

COMMANDS_FUNC = '''\
def init_commands(self) -> None:
    """Assign methods to the controls, stored in the attribute '_controls'."""
    if hasattr(self, '_controls'):
{calls}
'''
COMMANDS_CALL = "       self._controls['{control}'].configure(command=self.{command})"

MENUS_FUNC = '''\
def init_menus_command(self) -> None:
    """Assign methods to the controls, stored in the attribute '_controls'."""
    if hasattr(self, '_controls'):
{calls}
'''
MENUS_CALL = "      self._menus['{control}'].entryconfig('{action}', command=self.{command})"


def __new_init__(self, *args, **kwargs) -> None:
    self.__orig_init__(*args, **kwargs)

    if func := getattr(self, 'init_binders', None):
        func()
    if func := getattr(self, 'init_commands', None):
        func()
    if func := getattr(self, 'init_menus_command', None):
        func()


def _exec(cls, func_template, call_template, call_list):
    calls = '\n'.join(
        call_template.format(**kwargs)
        for kwargs in call_list
    )

    ns = {}
    exec(func_template.format(calls=calls), ns)
    func_name = list(ns.keys())[-1]
    setattr(cls, func_name, ns[func_name])


def with_modifiers(cls):
    """
    Create the binders based on the method decorator `bind`.

    Example:
    --------

    >>> @with_modifiers
    >>> class SomeFrame(ttk.Frame):
    >>>     # do something here
    >>>
    >>>     @bind('<FocusIn>', 'control-name')
    >>>     @bind('<FocusIn>', 'another-control')
    >>>     def focus_in(self, event):
    >>>         # do something when focus-in is triggered
    >>>
    >>>     @command('some-control')
    >>>     def clicked(self):
    >>>         # do something here
    """
    event_list, command_list, menu_list = [], [], []
    for name, value in vars(cls).copy().items():
        if callable(value):
            if hasattr(value, '_events'):
                event_list.extend(
                    [dict(event=event, control=control, command=name)
                     for event, control in value._events]
                )

            if hasattr(value, '_commands'):
                command_list.extend(
                    [dict(control=control, command=name)
                     for control in value._commands]
                )

            if hasattr(value, '_menus'):
                menu_list.extend(
                    [dict(control=control, action=action, command=name)
                     for control, action in value._menus]
                )

    if event_list:
        _exec(cls, BINDERS_FUNC, BINDERS_CALL, event_list)

    if command_list:
        _exec(cls, COMMANDS_FUNC, COMMANDS_CALL, command_list)

    if menu_list:
        _exec(cls, MENUS_FUNC, MENUS_CALL, menu_list)

    init = getattr(cls, '__init__')

    setattr(cls, '__orig_init__', init)
    setattr(cls, '__init__', __new_init__)

    return cls


def bind(event: str, control: str) -> _.Callable:
    """
    Use this with class decorator `with_modifiers`.

    :param event: The event name (see https://manpages.debian.org/bookworm/tk8.6-doc/bind.3tk.en.html)
    :param control: reference to a tk widget stored in the attribute _control in the class instance.
    :return: the wrapper
    """
    def _bind(func: _.Callable[[_.Any, 'Event'], None]) -> _.Callable:
        @wraps(func)
        def __bind(self, the_event: 'Event') -> _.Any:
            return func(self, the_event)

        events = getattr(func, '_events', [])
        __bind._events = [(event, control), *events]

        return __bind
    return _bind


def command(control: str) -> _.Callable:
    """
    Use this with class decorator `with_modifiers`.

    :param control: reference to a tk widget stored in the attribute _control in the class instance.
    :return: the wrapper
    """
    def _command(func: _.Callable[[_.Any], None]) -> _.Callable:
        @wraps(func)
        def __command(self) -> _.Any:
            return func(self)

        commands = getattr(func, '_commands', [])
        __command._commands = [control, *commands]

        return __command
    return _command


def menu(control: str, action: str) -> _.Callable:
    def _menu(func: _.Callable[[_.Any], None]) -> _.Callable:
        @wraps(func)
        def __menu(self) -> _.Any:
            return func(self)

        menus = getattr(func, '_menus', [])
        __menu._menus = [(control, action), *menus]

        return __menu
    return _menu
