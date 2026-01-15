# Steps
1.1. Set email in input[type='email'][aria-label='Adresse e-mail']
1.2. Click [role='button'][aria-label='Suivant']
2.1. Set code in input[aria-label='Code de confirmation']
2.2. Click [role='button'][aria-label='Suivant']
2.3. If Error -> Click [role='button'][aria-label='Je n’ai pas reçu le code']
2.4. Then click (Changer adresse e-mail) div > div > div > div > div > div > div > div > div > div:nth-child(2) > div > div > div.wbloks_87 > div:nth-child(3) > div > div > div > div > div > div > div > div > div:nth-child(2)
3.1. Set password in input[type='password'][aria-label='Mot de passe']
3.2. Click [role='button'][aria-label='Suivant']
4.1. Set birthdate in input[type='date'][aria-label="Date de naissance (0 ans)"]
4.2. Click [role='button'][aria-label='Suivant']
5.1. Set name in input[type='text'][aria-label='Nom complet']
5.2. Click [role='button'][aria-label='Suivant']
6.1. Set username in input[type='text-no_suggestion'][aria-label='Nom de profil']
6.2. Click [role='button'][aria-label='Suivant']
7.1. Click [role='button'][aria-label='J’accepte']

> in every step we need to way element to be visible and do action

# How to click a button
```javascript
const suivant = document.querySelector("button-selector")

if (suivant) {
    suivant.dispatchEvent(new MouseEvent("mousedown", { bubbles: true }));
    suivant.dispatchEvent(new MouseEvent("mouseup", { bubbles: true }));
    suivant.dispatchEvent(new MouseEvent("click", { bubbles: true }));
}
```