document.addEventListener("DOMContentLoaded", () => {

    // LOGIN
    const loginBtn = document.getElementById("login-btn");
    if (loginBtn) {
        loginBtn.addEventListener("click", async () => {
            const username = document.getElementById("username").value;
            const password = document.getElementById("password").value;

            try {
                const res = await fetch("/login-jwt/", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, password })
                });

                const data = await res.json();

                if (res.status === 200) {
                    localStorage.setItem("jwt_token", data.token); // for fetch forms
                    window.location.href = "/floors/";
                } else {
                    document.getElementById("login-error").innerText = data.error;
                }
            } catch (err) {
                console.error(err);
                document.getElementById("login-error").innerText = "Login failed!";
            }
        });
    }

    // HANDLE ALL FORMS WITH JWT
    const token = localStorage.getItem("jwt_token");
    document.querySelectorAll("form").forEach(form => {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();

            const formData = new FormData(form);
            const data = {};
            formData.forEach((value, key) => { data[key] = value });

            try {
                const actionUrl = form.getAttribute("action") || "/main-page/"; // ✅ FIX HERE

                const res = await fetch(actionUrl, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": token ? `Bearer ${token}` : ""
                    },
                    body: JSON.stringify(data)
                });

                if (res.status === 401) {
                    alert("Unauthorized! Login again.");
                    localStorage.removeItem("jwt_token");
                    window.location.href = "/login-page/";
                    return;
                }

                const result = await res.json();
                if (result.success) {
                    window.location.reload();
                } else {
                    alert("Error: " + JSON.stringify(result.error));
                }

            } catch (err) {
                console.error(err);
                alert("Error submitting form: " + err);
            }
        });
    });
});
