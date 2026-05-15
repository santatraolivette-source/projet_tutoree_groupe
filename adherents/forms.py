from django import forms
from .models import Adherent, CompteAdherent, Reservation, DetailReservation
from django.forms import BaseInlineFormSet, ValidationError, inlineformset_factory

class FormulaireAjoutAdherent(forms.ModelForm):
    class Meta:
        model = Adherent
        fields = '__all__'
        widgets = {
            'matricule' : forms.TextInput(attrs={
                'class' : 'form-control'
            }),
            'nom' : forms.TextInput(attrs={
                'class' : 'form-control'
            }),
            'prenom' : forms.TextInput(attrs={
                'class' : 'form-control'
            }),
            'email' : forms.EmailInput(attrs={
                'class' : 'form-control'
            }),
            'fonctions' : forms.Select(attrs={
                'class' : 'form-control'
            })
        }


class FormulaireInscription(forms.Form):
    matricule = forms.CharField(label='Matricule', 
                                widget=forms.TextInput(attrs={
                                    'class' : 'form-control border',
                                    'placeholder' : 'ex: 3243'
                                }))
    username = forms.CharField(label='Nom d\'utilisateur', 
                               widget=forms.TextInput(attrs={
                                   'class' : 'form-control border',
                                   'placeholder' : 'Rakoto'
                               }))
    code_otp = forms.CharField(label="Code OTP", 
                               widget=forms.TextInput(attrs={
                                   'class' : 'form-control border',
                                   'placeholder' : 'XXXXX'
                               }))
    password = forms.CharField(label='Mots de passe',
                               widget=forms.PasswordInput(attrs={
                                   'class' : 'form-control border',
                                   'placeholder' : 'Composé au moins 8 caractères(0-9,*/%,a-z,A-Z)'
                               }))
    password2 = forms.CharField(label='Confirmer mots de passe',
                                widget=forms.PasswordInput(attrs={
                                    'class' : 'form-control border',
                                    'placeholder' : 'Entrez le même mots de passe ici'
                                }))
                                
   

    def __init__(self, *args, otp_attendu=None, email_verifie=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.otp_attendu = otp_attendu
        self.email_verifie = email_verifie

    def clean_code_otp(self):
        code_otp = self.cleaned_data.get('code_otp')
        if self.otp_attendu is None:
            raise forms.ValidationError("Impossible de vérifier le code OTP.")
        if code_otp != self.otp_attendu:
            raise forms.ValidationError("Code OTP incorrect")
        return code_otp

    def clean(self):
        cleaned_data = super().clean()
        matricule = cleaned_data.get('matricule')
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')

        if not Adherent.objects.filter(matricule=matricule).exists():
            raise forms.ValidationError("Votre matricule n'est pas réconnu. Contactez l'administration.")
        
        if self.email_verifie is None:
            raise forms.ValidationError("Impossible de vérifier l'adresse email.")

        personne = Adherent.objects.get(matricule=matricule)
        if personne.email != self.email_verifie:
            raise forms.ValidationError("L'email vérifié ne correspond pas au matricule fourni.")
        
        if CompteAdherent.objects.filter(personne__matricule=matricule).exists():
            raise forms.ValidationError(
                "Un compte existe dejà pour ce matricule"
            )
        
        if password != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas")
        
        return cleaned_data
    

#Formulaire pour la verification par email
class VerificationParEmail(forms.Form):
    email = forms.EmailField(label="Entrez votre adresse email",
                             widget=forms.EmailInput(attrs={
                                 'class' : 'form-control border',
                                 'id' : 'email'
                             }))
    

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')

        return cleaned_data

#Formulaire pour la réservation
class FormulaireReservation(forms.ModelForm):
    class Meta:
        model = Reservation
        exclude = ['adherent', 'statut',
                   'valider_par',
                   'date_validation']#On exclue tous les champs parce qu'ils vont être remplie automatiquement au niveau de views 
        


#Formulaire pour le détail de réservation
class DetailReservationFormSet(BaseInlineFormSet):
    min_num = 1
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        
        #On verifie si il n'y a aucun doublons
        livre_deja_ajoutee = set()#variable pour stocker les livres reservés sans doublons
        valid_forms_count = 0 #Variable pour compter le nombre de détail

        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                livre_reserver = form.cleaned_data.get('livre')
                quantite = form.cleaned_data.get('quantite')

                if not livre_reserver:
                    continue
                
                if livre_reserver in livre_deja_ajoutee:
                    raise ValidationError(
                        "Vous avez ajouté le même livre plusieurs fois"
                    )
                
                livre_deja_ajoutee.add(livre_reserver)
                if livre_reserver and quantite:
                    if quantite > livre_reserver.quantite:
                        raise forms.ValidationError(
                            f"Stock insuffisant pour le livre '{livre_reserver.titre}'"
                            f"- Stock disponible : {livre_reserver.quantite}"
                        )
                else:
                    raise forms.ValidationError(
                        "La quantité doit supérieur ou égale à 1"
                    )


                valid_forms_count += 1
        if valid_forms_count < 1:
            raise ValidationError("Vous devez reserver au moins un livre")
    
#Utilisation de inlineformset_factory de Django pour faciliter l'enregistrement de plusieurs formulaire
#enfant (DetailReservation) avec un même parent(Reservation)
DetailReservationInlineFormSet = inlineformset_factory(
    Reservation,#Modele parent
    DetailReservation,#Modèle enfant
    fields = ['livre', 'quantite'],#Les champs à remplir
    widgets={
        'livre' : forms.Select(attrs={
            'class' : 'form-control'
        }),
        'quantite' : forms.NumberInput(attrs={
            'class' : 'form-control'
        })
    },
    extra=1,#Le nombre des formulaires enfant
    can_delete=False,#On peut  supprime le formulaire enfant
    formset=DetailReservationFormSet#On précise le formset utilisé
)
