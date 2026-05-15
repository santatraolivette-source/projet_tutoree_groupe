from django.apps import AppConfig


class AdherentsConfig(AppConfig):
    name = 'adherents'


    def ready(self):
        import adherents.signals#Signal django pour supprimer le compte lié à l'adherent lorsu'on le supprime
