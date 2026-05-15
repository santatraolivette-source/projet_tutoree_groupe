from django.shortcuts import render
from django.http import HttpResponseForbidden
import json
from groq import APIStatusError, Groq
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from bibliotheque.utils import get_user_role
from livres.models import Livre
from adherents.models import Reservation
from emprunts.models import Emprunt
from decouple import config
from .models import HistoriqueChat
from django.contrib.auth.decorators import login_required
from django.db.models import Count


#Récupération de toutes les données nécessaires 
def get_context_bibliotheque(adherent):
    #Données concernant les réservations et détails réservations
    reservations = Reservation.objects.prefetch_related('ligneReservation').filter(
        adherent=adherent
    ).values('statut','date_reservation')[:5]

    # Données concernant l'emprunt
    emprunts = Emprunt.objects.filter(
        reservation__adherent=adherent,
        statut='Non retourné'
    ).values(
        'reservation__ligneReservation__livre__titre',
        'date_limite'
    )[:5]


    categorie_populaire = Emprunt.objects.values('reservation__ligneReservation__livre__categorie').annotate(total=Count('id')).order_by('-total')[:5]

    # Liste de tous les livres
    livres = Livre.objects.filter(quantite__gt=0).values('titre','auteur','categorie','quantite')[:20]

    # On retourne une chaîne de caractères qui contient la requête à envoyer au client GROK
    return f"""
    Tu es un assistant pour une bibliothèque universitaire.
    Tu aides l'adhérent {adherent.nom} {adherent.prenom}.

    Ses emprunts en cours :
    {list(emprunts)}

    Ses réservations :
    {list(reservations)}

    Livres disponibles :
    {list(livres)}

    Les catégories du livre populaire:
    {list(categorie_populaire)}
    
    Règles :
    - Réponds uniquement en français
    - Réponds uniquement aux questions liées à la bibliothèque
    - Sois poli et concis
    """


@csrf_exempt
@login_required
def chatbot(request):
    if get_user_role(request.user)['role'] == 'bibliothecaire':
        return HttpResponseForbidden("Vous n'avez pas la permission nécessaire pour cette page.")
    if request.method == 'POST':
        try:
            data     = json.loads(request.body)
            question = data.get('message', '')  # Récupération du message
            adherent = request.user.compteadherent.personne  # Récupération de l'adhérent connecté

            #Sauvegarder message utilisateur
            HistoriqueChat.objects.create(
                adherent = adherent,
                role     = 'user',
                message  = question
            )

            # Récupérer les 10 derniers messages pour le contexte
            historique = HistoriqueChat.objects.filter(
                adherent=adherent
                ).order_by('-date')[:5][::-1]
                #::-1 renverser l'ordre de l'historique

            # Construire les messages pour Groq
            messages = [
                {'role': 'system', 'content': get_context_bibliotheque(adherent)}
            ]

            # Ajouter l'historique au contexte
            for h in historique:
                messages.append({
                    'role'   : 'user' if h.role == 'user' else 'assistant',
                    'content': h.message
                })

            # Appel Groq
            client   = Groq(api_key=config('GROK_API_KEY'))
            response = client.chat.completions.create(
                model    = 'llama-3.1-8b-instant',
                messages = messages
            )

            reponse_bot = response.choices[0].message.content

            # Sauvegarder réponse bot
            HistoriqueChat.objects.create(
                adherent = adherent,
                role     = 'bot',
                message  = reponse_bot
            )

            return JsonResponse({'response': reponse_bot})
        except APIStatusError as e:
            if e.status_code == 413:
                return JsonResponse({
                    'response' : "Désolé, la conversation est trop longue. Je vais recommencer"
                })
            return JsonResponse({
                'response' : "Une erreur s'est produite, réessayez."
            })
    return render(request, 'chatbot/chat.html')

# Charger l'historique au chargement de la page
def charger_historique(request):
    adherent  = request.user.compteadherent.personne
    historique = HistoriqueChat.objects.filter(
        adherent=adherent
    ).order_by('date')

    data = [
        {'role': h.role, 'message': h.message, 'date': str(h.date)}
        for h in historique
    ]
    # Renvoie les données au format JSON à récupérer dans le template chatbot/chat.html
    return JsonResponse({'historique': data})