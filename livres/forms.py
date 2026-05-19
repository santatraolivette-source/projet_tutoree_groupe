from django import forms
from .models import Livre


STYLE_DE_BASE = 'form-control mr-3 ml-2 border'
class LivreForm(forms.ModelForm) : 
    class Meta :
        model = Livre
        fields = ['reference' , 'titre' , 'auteur' , 'categorie' , 'quantite']
        widgets = {
            'reference' : forms.TextInput(attrs={
                'class' : STYLE_DE_BASE , 
                'placeholder' : 'Réference du livre'
        }),
            'titre' : forms.TextInput(attrs={
                'class' : STYLE_DE_BASE, 
                'placeholder' : 'Titre'
            }),
            'auteur' : forms.TextInput(attrs={
                'class' : STYLE_DE_BASE, 
                'placeholder' : 'L\'auteur'
            }),
            'categorie' : forms.Select(attrs={
                'class' : STYLE_DE_BASE, 
                'placeholder' : 'Categorie'
            }),
            'quantite' : forms.TextInput(attrs={
                'class' : STYLE_DE_BASE, 
                'placeholder' : 'Quantite'
            }),
            }
        

class LivreModificationForm(forms.ModelForm) : 
    class Meta :
        model = Livre
        fields = ['reference' , 'titre' , 'auteur', 'quantite']
        widgets = {
            'reference' : forms.TextInput(attrs={
                'class' : STYLE_DE_BASE , 
                'title' : 'Vous ne pouvez pas modifier la réference',
                'readonly' : True
        }),
            'titre' : forms.TextInput(attrs={
                'class' : STYLE_DE_BASE, 
                'placeholder' : 'titre'
            }),
            'auteur' : forms.TextInput(attrs={
                'class' : STYLE_DE_BASE, 
                'placeholder' : 'auteur'
            }),
            'quantite': forms.NumberInput(attrs={
                'class' : STYLE_DE_BASE,
                'readonly' : True,
                'title' : 'Vous ne ppuvez pas modifier la quantité du livre'
            })
            }