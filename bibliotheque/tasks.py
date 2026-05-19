from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from emprunts.models import Emprunt
from django.conf import settings

def envoyer_rappels():
    ajourd_hui = timezone.now().date()  # Date d'aujourd'hui
    dans_3_jours = ajourd_hui + timedelta(days=3)  # 3 jours avant la date limite

    # On récupère tous les emprunts non retournés dont la date limite est dans 3 jours
    emprunts_bientot = Emprunt.objects.filter(
        statut='Non retourné',
        date_limite=dans_3_jours
    )

    # On envoie un email à chaque emprunteur
    for emprunt in emprunts_bientot:
        send_mail(
            subject='Rappel : retour de livre',
            message=f"""Bonjour {emprunt.adherent.nom} {emprunt.adherent.prenom},
Votre livre \"{emprunt.ref_livre.titre}\" doit être retourné dans 3 jours.
Merci de bien vouloir apporter le justificatif d'emprunt lors de votre passage.

Cordialement,
La bibliothèque
""",
            from_email=settings.EMAIL_FROM,
            recipient_list=[emprunt.adherent.email]
        )


    
    #Tous les emprunts en retard
    emprunts_retard = Emprunt.objects.filter(
        statut='Non retourné',
        date_limite__lt=ajourd_hui
    )

    emprunts_retard.update(statut='En retard')#On met à jour le statut

    # Envoi d'un email de notification
    for emprunt in emprunts_retard:
        send_mail(
            subject='Retard : retour de livre',
            message=f"""Bonjour {emprunt.adherent.nom} {emprunt.adherent.prenom},
Votre prêt du livre "{emprunt.ref_livre.titre}" est en retard depuis le {emprunt.date_limite}.
Nous vous remercions de bien vouloir rapporter l'ouvrage à la bibliothèque dans les meilleurs délais.

Cordialement,
La bibliothèque""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[emprunt.adherent.email]
        )