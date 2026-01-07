import React from 'react';


// * Funcion para validar el inicio de sesión
function Login() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    if (username === 'admin' && password === 'admin') {
        TipeOfUser();
    } else {
        FailLogin();
    }
}
// * Funcion para retornar un mensaje de error en el inicio de sesión
function FailLogin() {
    alert('Inicio de sesión fallido');
    document.getElementById('username').value = '';
    document.getElementById('password').value = '';
}

function TipeOfUser() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

}
