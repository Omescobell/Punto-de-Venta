# Front Documentation

## React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

**Start Server** ´/frontend/´ server npm run

---

#### Login

Use of credentials to send de acces to de api route '/api/auth/login/'
Crendentials: email,password
Succesful = send to Ventas.jsx View and send **Usertype**
Fail = Error mesaje

### Users View

Owner: Full Access
Admin: Full Access
User/Employe: Ventas, Clientes , Inventario

### Users

Form: username , email, password, first_name, last_name, address, role, phone number.

if the Usertype is employe or the sesion is over show a messaje to **Access denied or Sesion out of time **

### Chatbot

Form: Existent_user , phone number.

If the Usertype is employe or the sesion is over show a messaje to **Access denied or Sesion out of time **

### Ventas

Show all products and quantity
Show seletion of diferent clients and in base option is 'Cliente Visitante'

Pay methots: 'Cash, Card, Credit'
