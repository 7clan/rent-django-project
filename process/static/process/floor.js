const token = localStorage.getItem("jwt_token");
if (!token) {
    alert("You must log in first!");
    window.location.href = "/login-page/";
}

document.querySelectorAll("form").forEach(form => {
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        const actionUrl = form.getAttribute("action") || window.location.href;

        const res = await fetch(actionUrl, {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}` },
            body: formData
        });

        if (res.status === 401) {
            alert("Unauthorized! Please log in again.");
            window.location.href = "/login-page/";
            return;
        }

        if (!res.ok) throw new Error("Form submission failed!");
        window.location.reload();
    });
});
