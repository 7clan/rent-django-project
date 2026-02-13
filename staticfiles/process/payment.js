const form = document.querySelector("form[action^='/add_payment/']");

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const token = localStorage.getItem("jwt_token");
    if (!token) {
        alert("You must log in!");
        return;
    }

    const res = await fetch(form.action, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
            amount: form.amount.value,
            year_month_covered: form.year_month_covered.value
        })
    });

    if (res.ok) {
        location.reload();
    } else {
        const errorMsg = await res.text();
        alert("Error: " + errorMsg);
    }
});
