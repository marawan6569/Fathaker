import os


class Backup:
    def __init__(self,):
        self.generate_backups_file()

    @staticmethod
    def generate_backups_file():
        if not os.path.isdir('db_backup'):
            os.mkdir('db_backup')
        os.system(f'python3 manage.py dumpdata --indent 4 > db_backup/backup.json')


if __name__ == '__main__':
    backup = Backup()
