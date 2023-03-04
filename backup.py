import os


class Backup:
    def __init__(self,):
        self._generate_backups_file()
        self._backup_to_folder()

    @staticmethod
    def _generate_backups_file():
        if not os.path.isdir('db_backup'):
            os.mkdir('db_backup')
        os.system(f'python3 manage.py dumpdata --indent 4 > db_backup/backup.json')

    @staticmethod
    def _backup_to_folder():
        if not os.path.isdir('../backup'):
            os.mkdir('../backup')

        if os.path.isdir('../backup/db_backup/'):
            os.system('rm -r ../backup/db_backup/')
        if os.path.isdir('../backup/media/'):
            os.system('rm -r ../backup/media/')

        os.system('cp -r db_backup/ ../backup/db_backup/')
        os.system('cp -r media/ ../backup/media/')


if __name__ == '__main__':
    backup = Backup()
