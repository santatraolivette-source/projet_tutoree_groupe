from datetime import timedelta
from django.utils import timezone

from django.db.models import Count, Sum
from livres.models import Livre
from adherents.models import Adherent, Reservation
from emprunts.models import Emprunt
from .utils import get_user_role
from django.http import HttpResponse

# On définit cette fonction de context processors parce que nous avons besoin de renvoyer ces données
# à la template de base pour éviter de créer une fonction view pour chaque application
# Cette fonction dashboard_stats s'exécute automatiquement à chaque requête et envoie les données à tous les templates
def dashboard_stats(request):
    ajourd_hui = timezone.now().date()  # Date d'aujourd'hui
    dans_3_jours = ajourd_hui + timedelta(days=3)
    # Données pour bibliothécaire
    # Total livre par titre
    try:
        total_livres = Livre.objects.aggregate(total=Sum('quantite'))['total'] or 0  # calculer le nombre de livres
        # disponibles en additionnant les quantités et en stockant le résultat dans une variable total
        # aggregate retourne un dictionnaire {'total' : total}
        titres_differents = Livre.objects.count()  # On compte les différents titres de livres enregistrés


        # Totaux adhérents
        total_adherents = Adherent.objects.count()
        # Membres actifs
        # emprunt__statut = requête join Adherent --> Reservation --> Emprunt --> statut
        # .distinct() évite les doublons
        # Adhérent qui a un emprunt en cours
        membres_actifs = Adherent.objects.filter(reservation__emprunt__statut='Non retourné').distinct().count()
    

        #Emprunts en cours
        # Filtration des emprunts avec attribut statut = 'Non retourné'
        emprunts_non_retournee = Emprunt.objects.filter(statut='Non retourné').count()

        
        role_utilisateur = get_user_role(request.user)
        if request.user.is_authenticated:
            total_reservation_effectue = 0
            reservation_validee = 0
            reservation_refusee = 0
            retour_imminent = Emprunt.objects.filter(reservation__adherent__compteadherent__user=request.user, date_limite=dans_3_jours).count()
            total_livre_lu = Emprunt.objects.filter(reservation__adherent__compteadherent__user=request.user).count()
            emprunt_actif=  Emprunt.objects.filter(reservation__adherent__compteadherent__user=request.user, statut='Non retourné').count()
        
            if role_utilisateur['role'] == 'adherent':
                total_reservation_effectue = Reservation.objects.filter(adherent=request.user.compteadherent.personne).count()
                reservation_validee = Reservation.objects.filter(adherent= request.user.compteadherent.personne, statut='Validée').count()
                reservation_refusee = Reservation.objects.filter(adherent= request.user.compteadherent.personne, statut='Refusée').count()
            reservation_en_attente = total_reservation_effectue - (reservation_refusee + reservation_validee)
            return {
                'total_livres' : total_livres,
                'titres_differents' : titres_differents,
                'total_adherents' : total_adherents,
                'membres_actifs' : membres_actifs,
                'emprunts_non_retourne' : emprunts_non_retournee,
                'total_reservation_effectuee' :total_reservation_effectue,
                'reservation_validee' : reservation_validee,
                'reservation_refusee' : reservation_refusee,
                'reservation_en_attente' : reservation_en_attente,
                'retour_imminent' :retour_imminent,
                'total_livre_lu' : total_livre_lu,
                'emprunt_actif' :emprunt_actif,
            
            }
        
        return {
            'default' : None
        }
    except:
        return HttpResponse("Bienvenue, l'application est en maintenance. Veuillez contacter l'administrateur. Merci pour votre patience")


def user_role(request):
    return {'user_role' : get_user_role(request.user)}

    