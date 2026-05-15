from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from .models import Adherent, CompteAdherent, Reservation
from .forms import FormulaireAjoutAdherent, FormulaireInscription, VerificationParEmail, FormulaireReservation, DetailReservationFormSet, DetailReservationInlineFormSet
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.mail import send_mail
import secrets
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from bibliotheque.utils import get_user_role
from django.forms import ValidationError

@login_required
def liste_adherents(request):
    if get_user_role(request.user)['role'] == 'bibliothecaire':
        adherents = Adherent.objects.all()
        return render(request, "adherents/liste_adherent.html", 
                  {'adherents' : adherents})
    else:
        return HttpResponseForbidden("Vous n'avez pas la permission nécessaire pour cette page.")

@login_required
def ajouter_adherent(request):
    if get_user_role(request.user)['role'] == 'bibliothecaire':
        if request.method == "POST":
            form = FormulaireAjoutAdherent(request.POST)
            if form.is_valid():
                form.save()
                return redirect('listeAdherent')
            else:
                return HttpResponse("Vérifiez bien vos données")
        else:
            form = FormulaireAjoutAdherent()
            return render(request, "adherents/ajouter.html", {
                'form' : form
            })
    else:
        return HttpResponseForbidden("Vous n'avez pas la permission nécessaire pour cette page.")
    
@login_required
def modifier_adherent(request, id):
    if get_user_role(request.user)['role'] == 'bibliothecaire':
        adherent = get_object_or_404(Adherent, pk=id)
        if request.method == "POST":
            form = FormulaireAjoutAdherent(request.POST, instance=adherent)
            if form.is_valid():
                form.save()
                return redirect('listeAdherent')
            else:
                return HttpResponse("Modification non valide")
        else:
            form = FormulaireAjoutAdherent(instance=adherent)
            return render(request, "adherents/modifier.html", {
                'form' : form
            })
    else:
        return HttpResponseForbidden("Vous n'avez pas la permission nécessaire pour cette page.")

@login_required
def supprimer_adherent(request, id):
    if get_user_role(request.user)['role'] == 'bibliothecaire':
        adherent = get_object_or_404(Adherent, pk=id)
        if request.method == "POST":
            adherent.delete()
            return redirect('listeAdherent')
        else:
        
            return render(request, 'adherents/confirmation_suppression.html', {
                'adherent' : adherent
            })
    else:
        return HttpResponseForbidden("Vous n'avez pas la permission nécessaire pour cette page.")

@login_required
def recherche(request) :
    query = request.GET.get('q','').strip()
    if not query:
        return redirect('listeAdherent')
    else:
        nbre_resultat = 0
        adherent_lookup = Q(matricule__icontains=query) | Q(nom__icontains=query) | Q(prenom__icontains=query)|Q(fonctions__icontains=query) 
        adherents =  Adherent.objects.filter(adherent_lookup)
        context = {
            'adherents' : adherents,
            'nbre_resultat' : adherents.count(),
            'query' : query
        }
        return render (request, 'adherents/liste_adherent.html', context)

def verification(request):
    if request.method == "POST":
        form = VerificationParEmail(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            otp = ''.join(secrets.choice('0123456789') for _ in range(5))
            request.session['otp_code'] = otp
            request.session['otp_email'] = email
            send_mail(
                subject='Vérification via code OTP',
                message=f'Bonjour voici votre code OTP {otp}',
                from_email='stockalerte85@gmail.com',
                recipient_list=[email]
            )
            return redirect('inscription')
    else:
        form = VerificationParEmail()
    return render(request, 'adherents/verification.html', {
        'form' : form
    })


# views.py
def inscription(request):
    otp_attendu = request.session.get('otp_code')
    email_verifie = request.session.get('otp_email')

    if not otp_attendu or not email_verifie:
        return redirect('verification')
    
    if request.method == 'POST':
        form = FormulaireInscription(
            request.POST,
            otp_attendu=otp_attendu,
            email_verifie=email_verifie,
        )
        if form.is_valid():
            matricule = form.cleaned_data['matricule']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            # Récupérer la personne autorisée (adhérent)
            personne = Adherent.objects.get(matricule=matricule)

            # Création d'un utilisateur Django associé
            user = User.objects.create_user(
                username=username,
                password=password,
                email=personne.email,
            )

            # Création du compte pour l'adherent
            CompteAdherent.objects.create(
                user=user,
                personne=personne,
            )

            request.session.pop('otp_code', None)
            request.session.pop('otp_email', None)
            return redirect('seConnecter')
    else:
        form = FormulaireInscription(
            otp_attendu=otp_attendu,
            email_verifie=email_verifie,
        )

    return render(request, 'adherents/inscription.html', {'form': form})



#Views qui gère la réservation
@login_required
def reservation_avec_detail(request):
    if get_user_role(request.user)['role'] == 'adherent':
        if request.method == "POST":
            reservation_form = FormulaireReservation(request.POST)
       
            # Vérification si le formulaire est valide
            if reservation_form.is_valid():
                reservation = reservation_form.save(commit=False)
                # Récupérer l'adhérent connecté
                adherent = request.user.compteadherent.personne
                reservation.adherent = adherent
                detail_reservation_form = DetailReservationInlineFormSet(request.POST, instance=reservation)
                if detail_reservation_form.is_valid():
                    #Enregistrement après validation
                    reservation.save()
                    detail_reservation_form.save()

                    return redirect('listeReservation')
            
        else:
            reservation_form = FormulaireReservation()
            detail_reservation_form = DetailReservationInlineFormSet()
        
        context = {
            'reservation_form' : reservation_form,
            'detail_reservation_form' : detail_reservation_form
        }
        return render(request, 'adherents/reservation.html', context)
    else:
        return HttpResponseForbidden("Vous n'avez pas la permission nécessaire pour cette page.")

@login_required
def liste_reservation(request):
    if get_user_role(request.user)['role'] == 'bibliothecaire':
        return HttpResponseForbidden("Vous n'avez pas la permission nécessaire pour cette page.")
    else:
        reservation_avec_details = Reservation.objects.prefetch_related('ligneReservation').filter(adherent=request.user.compteadherent.personne).order_by('-date_reservation')


        paginator = Paginator(reservation_avec_details, 5)

        page_num = request.GET.get('page')
        page_obj = paginator.get_page(page_num)

        context = {
            "page_obj" : page_obj,
            "nbre_reservation" : reservation_avec_details.count()
        }

        return render(request, "adherents/liste_reservation.html", context)
