const apiUrl = 'http://localhost:3000';

async function registerUser (username, password) {
    const response = await fetch(`${apiUrl}/users`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
    });
    return response.json();
}

async function loginUser (username, password) {
    const response = await fetch(`${apiUrl}/users?username=${username}&password=${password}`);
    const users = await response.json();
    return users.length > 0 ? users[0] : null;
}

async function reportIncident(details, address) {
    const response = await fetch(`${apiUrl}/reports`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ details, address })
    });
    return response.json();
}