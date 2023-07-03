import typing as _
from tkinter import messagebox
from functools import wraps

RecordId = _.NewType('RecordId', int)
Message = _.NewType('Message', str)
IsOk = _.NewType('IsOk', bool)
OnErrorResult = _.Tuple[IsOk, RecordId, Message] | _.Tuple[RecordId, Message] | RecordId
OnErrorFunc = _.Callable[..., OnErrorResult]


class ServiceResult:
    def __init__(self, *, ok: bool = True, record_id: int = None, message: str = None) -> None:
        self.is_ok = ok
        self.record_id = record_id
        self.message = message

    def __repr__(self) -> str:
        return (f'ServiceResult(is_ok: {self.is_ok!r}, '
                f'record_id: {self.record_id!r},'
                f'message: {self.message!r})')

    def __bool__(self) -> bool:
        return self.is_ok

    def show_message(self) -> None:
        if self.is_ok:
            messagebox.showinfo(message=self.message)
        else:
            messagebox.showerror(message=self.message)


def on_error(message: str) -> _.Callable:
    def _on_error(func: OnErrorFunc) -> _.Callable:
        @wraps(func)
        def __on_error(self, *args, **kwargs) -> ServiceResult:
            try:
                result = func(self, *args, **kwargs)

                *is_ok, record_id, msg = result if isinstance(result, tuple) else (True, result, '')

                is_ok = is_ok[0] if len(is_ok) == 1 else True

                return ServiceResult(ok=is_ok, record_id=record_id, message=msg)
            except Exception as ex:
                msg = f'{message}\n\n{ex}'
                return ServiceResult(ok=False, message=msg)
        return __on_error
    return _on_error
