const token = localStorage.getItem("jwt_token");
if (!token) {
    alert("You must log in first!");
    window.location.href = "/login-page/";
}

// Wait for DOM to be ready before attaching event listeners
document.addEventListener("DOMContentLoaded", function() {
    console.log("floor.js loaded - attaching form listeners");
    
    document.querySelectorAll("form").forEach(form => {
        // Skip payment forms (handled by payment.js)
        if (form.action.includes("/add_payment/")) return;
        
        console.log("Attaching listener to form:", form.action);
        
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            console.log("Form submitted");
            const formData = new FormData(form);
            const actionUrl = form.getAttribute("action") || window.location.href;

            try {
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

                const responseData = await res.json();

                if (res.ok) {
                    alert("✅ Successfully saved!");
                    window.location.reload();
                } else {
                    // Display validation errors if available
                    if (responseData.errors) {
                        let errorMsg = "Validation errors:\n\n";
                        for (let field in responseData.errors) {
                            const fieldError = responseData.errors[field];
                            if (Array.isArray(fieldError)) {
                                errorMsg += `${field}: ${fieldError.join(", ")}\n`;
                            } else if (typeof fieldError === 'object') {
                                errorMsg += `${field}: ${JSON.stringify(fieldError)}\n`;
                            } else {
                                errorMsg += `${field}: ${fieldError}\n`;
                            }
                        }
                        alert(errorMsg);
                    } else {
                        alert("❌ Error: " + (responseData.error || "Form submission failed!"));
                    }
                }
            } catch (error) {
                alert("❌ Network error: " + error.message);
            }
        });
    });
    
    if (document.querySelectorAll("form").length === 0) {
        console.warn("No forms found on page");
    }

    // Show expected months from start date to today for renter form
    const startInput = document.getElementById('renter_start_date');
    const expectedInfo = document.getElementById('expected_info');
    async function updateExpected() {
        if (!startInput || !expectedInfo) return;
        const val = startInput.value;
        const aptEl = document.getElementById('apartment_select');
        const apartmentId = aptEl ? aptEl.value : '';
        if (!val || !apartmentId) { expectedInfo.textContent = ''; return; }
        try {
            const res = await fetch(`/api/expected/?apartment=${apartmentId}&start_date=${val}`);
            if (!res.ok) {
                expectedInfo.textContent = 'Could not calculate expected payments';
                return;
            }
            const data = await res.json();
            expectedInfo.textContent = `Expected months: ${data.months_count}, Expected total: $${data.expected_total}`;
        } catch (e) {
            expectedInfo.textContent = 'Error calculating expected payments';
        }
    }
    if (startInput) startInput.addEventListener('change', updateExpected);
    const aptSelect = document.getElementById('apartment_select');
    if (aptSelect) aptSelect.addEventListener('change', updateExpected);
    updateExpected();
});

