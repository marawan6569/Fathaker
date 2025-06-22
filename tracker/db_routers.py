class TrackerRouter:
    models = {'statistics'}
    statistics_db = "statistics"
    default_db = "default"

    def db_for_read(self, model, **hints):
        if model._meta.model_name in self.models:
            return self.statistics_db
        return self.default_db

    def db_for_write(self, model, **hints):
        if model._meta.model_name in self.models:
            return self.statistics_db
        return self.default_db

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if model_name in self.models:
            return False
        return True