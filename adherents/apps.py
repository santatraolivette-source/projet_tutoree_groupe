from django.apps import AppConfig


class AdherentsConfig(AppConfig):
    name = 'adherents'


    def ready(self):
        import adherents.signals  # Signal Django pour supprimer le compte lié à l'adhérent lorsqu'on le supprime
