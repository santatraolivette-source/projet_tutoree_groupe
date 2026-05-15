from django.db.models.signals import pre_delete
from django.dispatch import receiver
from .models import Adherent, CompteAdherent

@receiver(pre_delete, sender=Adherent)
def supprimer_user_adherent(sender, instance, **kwargs):
    """Supprime l'utilisateur Django associé avant la suppression de l'adhérent"""
    try:
        compte = CompteAdherent.objects.get(personne=instance)
        compte.user.delete()
    except CompteAdherent.DoesNotExist:
        pass


