from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django import forms
from django.utils.translation import gettext_lazy as _

# Créer un formulaire d'authentification qui hérite de AuthenticationForm
class FormulaireAuthentification(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder' : 'Entrez votre nom d\'utilisateur ici',
        'class' : 'form-control',
        'id' : 'username'
    }), label="Nom d'utilisateur")
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class' : 'form-control',
        'id':'password',
        'placeholder' : 'Entrez votre mot de passe'
    }), label="Mot de passe")


class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnalisation du label du champ
        self.fields['new_password1'].label = "Choisissez votre nouveau secret"
        # Personnalisation de l'aide en dessous
        self.fields['new_password1'].help_text = "Évitez le nom de votre chat !"