const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
const email = document.getElementById('id_email')

email.addEventListener('change', () => {
    let email_utilisateur = email.value
    const isValid = emailRegex.test(email_utilisateur)

    if (!isValid){
    alert("Adresse email invalide")
}

})



