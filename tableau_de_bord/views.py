import datetime
import io
import json

from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from bibliotheque.utils import get_user_role
from livres.models import Livre
from adherents.models import Adherent, Reservation
from emprunts.models import Emprunt
from django.db.models import F, Avg, DurationField, ExpressionWrapper, Sum, Count
from django.db.models.functions import TruncMonth, TruncDate
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle



@login_required
def index_dashboard(request):
    try:
        # Récupération des quantités de livres par catégorie
        # .values('categorie') == regroupé par catégorie
        # .annotate(total_quantite=Sum('quantite')) == On additionne la valeur de l'attribut quantite de chaque catégorie regroupée
        # Puis on arrange par catégorie
        quantite_par_categorie = Livre.objects.values('categorie').annotate(total_quantite=Sum('quantite')).order_by('categorie')
        labels_livre_categorie = [q['categorie'] for q in quantite_par_categorie]
        data_livre_categorie = [q['total_quantite'] for q in quantite_par_categorie]
    
    
    
        # On regroupe les adhérents par fonction puis on crée une variable à la volée effectif total qui
        # contient l'effectif des adhérents groupés par fonction
        adherent_par_fonction = Adherent.objects.values('fonctions').annotate(effectif_total=Count('matricule'))
        labels_adherent_fonction = [a['fonctions'] for a in adherent_par_fonction]
        data_adherent_fonction = [a['effectif_total'] for a in adherent_par_fonction]



    
        # On récupère le nombre d'emprunts des 7 derniers mois
        # Définir une variable pour stocker la date de début : aujourd'hui - 7 mois
        date_debut = timezone.now() - relativedelta(months=7)
        # __gt = greater than
        # __lte = less than or equal
        # __lt = less than
        #truncMonth = Tronque une date en ne gardant que l'année et les mois
        emprunt_par_mois = (
            Emprunt.objects.
            filter(date_emprunt__gte=date_debut)#gte = greater than or equal 'lookup django'
            .annotate(mois=TruncMonth('date_emprunt'))#On crée une variable temporaire mois , 
            .values('mois')#Regroupé par mois
            .annotate(total=Count('id'))#Crée une variable total pour stocker la total des emprunts en un mois 
            .order_by('mois')
        )


        retours_par_mois = (
            Emprunt.objects
            .filter(date_retour__isnull=False)#Filtrer les enregistrement où date_retour n'est pas vide
            .annotate(mois=TruncMonth('date_retour'))
            .values('mois')
            .annotate(total=Count('id'))
            .order_by('mois')
        )

        
        emprunt_journalier = (
            Emprunt.objects
            .values('date_emprunt')
            .annotate(total=Count('id'))
            .order_by('date_emprunt')
        )

        labels_emprunt_journalier = [e['date_emprunt'].strftime('%d/%m/%y') for e in emprunt_journalier]
        data_emprunt_journalier = [e['total'] for e in emprunt_journalier]
    
        #Formatage pour le graphe emprunts/retours par mois
        #Formater les données pour faciliter leurs utilisation dans le graphe
        labels_emprunt_mois = []#Variable pour stocker les labels ['janvier', 'fevrier', ....]
        emprunts_data = []#Variable pour stocker les données pour emprunts
        retours_dict = {r['mois'].strftime('%b'): r['total']for r in retours_par_mois}

        for e in emprunt_par_mois:
            mois_label = e['mois'].strftime('%b')
            labels_emprunt_mois.append(mois_label)
            emprunts_data.append(e['total'])

        retours_data = [retours_dict.get(label, 0) for label in labels_emprunt_mois]
    



        #Emprunts par catégorie
        emprunt_par_categorie = Emprunt.objects.values('reservation__ligneReservation__livre__categorie').annotate(total=Count('id')).order_by('reservation__ligneReservation__livre__categorie')
        labels_emprunt_categorie = [e['reservation__ligneReservation__livre__categorie'] for e in emprunt_par_categorie]
        data_emprunt_categorie = [e['total'] for e in emprunt_par_categorie]


        #Livres en retard
        livres_en_retard = Emprunt.objects.filter(date_limite__lt=timezone.now().date(), statut='Non retourné').count()
    
        #Categories populaire
        categorie_populaire = Emprunt.objects.values('reservation__ligneReservation__livre__categorie').annotate(total=Count('id')).order_by('-total').first()['reservation__ligneReservation__livre__categorie']
    

        #Taux de retour
        total_emprunts_retournee = Emprunt.objects.filter(statut='Retourné').count()
        total_emprunts = Emprunt.objects.count()
        taux_de_retour = 0;
        if total_emprunts:
            taux_de_retour = ((total_emprunts_retournee / total_emprunts) * 100).__round__(2)#Arrondir deux chiffres après la virgule


        #Durrée moyenne d'un emprunt
        duree = ExpressionWrapper(F('date_retour') - F('date_emprunt'), output_field=DurationField())
        resultat = (
            Emprunt.objects
            .filter(date_retour__isnull=False)
            .aggregate(moyenne=Avg(duree))
        )
    
        duree_moyenne = resultat['moyenne'].days if resultat['moyenne'] else 0
    
        emprunts_en_cours = Emprunt.objects.filter(reservation__adherent__compteadherent__user=request.user, statut='Non retourné')
    

        #Genres lu adhérent
        genres_lus = Emprunt.objects.values('reservation__ligneReservation__livre__categorie').filter(reservation__adherent__compteadherent__user=request.user).annotate(total=Count('id')).order_by('-total')[:5]
        label_genre_lus = [e['reservation__ligneReservation__livre__categorie'] for e in genres_lus]
        data_genre_lus = [e['total'] for e in genres_lus]

        return render(request, 'tableau_de_bord/index.html', {
            'labels_livre_categorie' : json.dumps(labels_livre_categorie),
            'data_livre_categorie' : json.dumps(data_livre_categorie),
            'labels_adherent_fonction' : json.dumps(labels_adherent_fonction),
            'data_adherent_fonction' : json.dumps(data_adherent_fonction),
            'labels_emprunt_mois' : json.dumps(labels_emprunt_mois),
            'emprunts_data' : json.dumps(emprunts_data),
            'retours_data' : json.dumps(retours_data),
            'labels_emprunt_categorie' : json.dumps(labels_emprunt_categorie),
            'data_emprunt_categorie' : json.dumps(data_emprunt_categorie),
            'labels_emprunt_journalier' : json.dumps(labels_emprunt_journalier),
            'data_emprunt_journalier' : json.dumps(data_emprunt_journalier),
            'taux_de_retour' : taux_de_retour,
            'duree_moyenne' : duree_moyenne,
            'categorie_populaire' : categorie_populaire,
            'livres_en_retard' : livres_en_retard,
            'emprunts_en_cours' : emprunts_en_cours,
            'label_genre_lus' : json.dumps(label_genre_lus),
            'data_genre_lus': json.dumps(data_genre_lus),
        })
    except:
        return render(request, 'tableau_de_bord/index.html')


def generer_recu_pdf(reservation, emprunt):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='ReceiptTitle', fontSize=18, leading=22, spaceAfter=12, alignment=1))
    styles.add(ParagraphStyle(name='SectionHeading', fontSize=12, leading=14, spaceAfter=8, textColor=colors.HexColor('#2563eb')))
    styles.add(ParagraphStyle(name='Small', fontSize=10, leading=12))
    styles.add(ParagraphStyle(name='TableCell', fontSize=10, leading=14, spaceAfter=4))

    def escape_text(text):
        if text is None:
            return ''
        return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    elements = [
        Paragraph("Reçu d'emprunt - Bibliothèque", styles['ReceiptTitle']),
        Paragraph(f"Réservation n°: {reservation.pk}", styles['SectionHeading']),
        Paragraph(f"Date réservation: {reservation.date_reservation.strftime('%d/%m/%Y')}", styles['Normal']),
        Paragraph(f"Date validation: {reservation.date_validation.strftime('%d/%m/%Y') if reservation.date_validation else 'N/A'}", styles['Normal']),
        Spacer(1, 12),
        Paragraph("Informations adhérent", styles['SectionHeading']),
        Paragraph(f"Nom: {reservation.adherent.nom} {reservation.adherent.prenom}", styles['Normal']),
        Paragraph(f"Matricule: {reservation.adherent.matricule}", styles['Normal']),
        Paragraph(f"Email: {reservation.adherent.email}", styles['Normal']),
        Spacer(1, 12),
        Paragraph("Livres réservés", styles['SectionHeading']),
    ]

    table_data = [["Référence", "Titre", "Auteur", "Quantité"]]
    for detail in reservation.ligneReservation.select_related('livre').all():
        livre = detail.livre
        table_data.append([
            Paragraph(escape_text(livre.reference), styles['TableCell']),
            Paragraph(escape_text(livre.titre), styles['TableCell']),
            Paragraph(escape_text(livre.auteur), styles['TableCell']),
            Paragraph(str(detail.quantite), styles['TableCell']),
        ])

    table = Table(table_data, colWidths=[80, 240, 160, 50])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('WORDWRAP', (0, 0), (-1, -1), 'CJK'),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 16))
    elements.append(Paragraph("Informations de validation", styles['SectionHeading']))
    elements.append(Paragraph(f"Bibliothécaire: {emprunt.bibliothecaire.get_full_name() or emprunt.bibliothecaire.username}", styles['Normal']))
    elements.append(Paragraph(f"Statut emprunt: {emprunt.statut}", styles['Normal']))
    elements.append(Spacer(1, 24))
    elements.append(Paragraph("Merci d'avoir utilisé la bibliothèque.", styles['Small']))

    doc.build(elements)
    buffer.seek(0)
    return buffer


@login_required
def liste_reservation_avalidee(request):
    if get_user_role(request.user)['role'] == 'bibliothecaire':
        if request.method == "POST":
            return HttpResponse("Requette POST")
        else:
            reservation_avec_details = Reservation.objects.prefetch_related('ligneReservation').filter(statut='En attente').order_by('-date_reservation')
            return render(request, 'tableau_de_bord/reservation_non_validee.html', {
                'reservation_avec_details' : reservation_avec_details
            })
    else:
        return HttpResponseForbidden("Vous n'avez pas la permission nécessaire pour cette page.")

@login_required    
def valider_reservation(request, id):
    if get_user_role(request.user)['role'] == 'bibliothecaire':

        reservation = Reservation.objects.get(id=id)

        reservation.statut = 'Validée'
        reservation.valider_par = request.user
        reservation.date_validation = timezone.now().date()
        reservation.save()

        for detail in reservation.ligneReservation.all():
            detail.livre.quantite -= detail.quantite
            detail.livre.save()

        emprunt = Emprunt.objects.create(
            reservation=reservation,
            bibliothecaire=request.user
        )

        pdf_buffer = generer_recu_pdf(reservation, emprunt)
        response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="recu_emprunt_{reservation.pk}.pdf"'
        return response
    else:
        return HttpResponseForbidden("Vous n'avez pas la permission nécessaire pour cette page.")

@login_required
def refuser_reservation(request, id):
    if get_user_role(request.user)['role'] == 'bibliothecaire':
        reservation = Reservation.objects.get(id=id)

        reservation.statut = 'Refusée'
        reservation.valider_par = request.user
        reservation.date_validation = timezone.now().date()
        reservation.save()

    
        return redirect('listeReservationAValidee')
    else:
        return HttpResponseForbidden("Vous n'avez pas la permission nécessaire pour cette page.")

def mes_emprunts(request):
    if get_user_role(request.user)['role'] == 'bibliothecaire':
        return HttpResponseForbidden("Vous n'avez pas la permission nécessaire pour cette page.")
    else:
        emprunts = Emprunt.objects.filter(reservation__adherent__compteadherent__user=request.user, statut='Retourné')
        print(emprunts)
        return render(request, "tableau_de_bord/mes_emprunts.html", {
            'emprunts' : emprunts
        })
