const API_BASE = '/api/auth';

async function login(event) {
    event.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: "include",
            body: JSON.stringify({ username, password }),
        });

        console.log("Response status:", response.status);

        const responseData = await response.json();
        console.log("Response headers:", [...response.headers.entries()]);

        if (response.ok) {
            console.log("Авторизация успешна, переадресация...");
            window.location.href = '/admin';
        } else {
            console.log("Ошибка авторизации:", responseData);
            const alertBox = document.getElementById('alertBox');
            alertBox.textContent = responseData.detail || 'Ошибка авторизации';
            alertBox.classList.remove('d-none');
        }
    } catch (error) {   
        console.error('Ошибка сети или сервера:', error);
        const alertBox = document.getElementById('alertBox');
        alertBox.textContent = 'Ошибка сети или сервера';
        alertBox.classList.remove('d-none');
    }
}

document.getElementById('loginForm').addEventListener('submit', login);
