from pathlib import Path
import gui
import models
import db
from gui.main_form import MainForm
from gui import build_root

root = Path(__file__).parent.expanduser().absolute()
db_file = root / 'data.sqlite'


def main():
    print('Start')
    create_all = not db_file.exists()
    db.init_db(f'sqlite:///{db_file!s}', echo=False)

    if create_all:
        print('Create all models')
        models.create_all()

    print('Run form')
    root = build_root()
    MainForm(root)
    root.mainloop()

    print('End')


if __name__ == '__main__':
    main()
