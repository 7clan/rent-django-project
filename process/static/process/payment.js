const form = document.querySelector("form[action^='/add_payment/']");

if (form) {
    form.addEventListener("submit", async (e) => {
        const token = localStorage.getItem("jwt_token");
        // If no token present, allow normal form submission (server will handle POST)
        if (!token) {
            return; // do not prevent default - let browser submit form
        }
        e.preventDefault();

        const amount = form.amount.value;
        const payment_type = (form.payment_type && form.payment_type.value) ? form.payment_type.value : 'monthly';
        const year_month_covered = form.year_month_covered ? form.year_month_covered.value : '';
        const year_covered = form.year_covered ? form.year_covered.value : '';

        if (!amount && payment_type === 'monthly') {
            alert("Please fill in the amount!");
            return;
        }

        try {
            const payload = { amount: amount, payment_type: payment_type };
            if (payment_type === 'monthly') payload.year_month_covered = year_month_covered;
            if (payment_type === 'yearly') payload.year_covered = year_covered;

            const res = await fetch(form.action, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            const data = await res.json();

            if (res.ok) {
                // Show success message with checkmark
                const successDiv = document.createElement("div");
                successDiv.style.cssText = "background: #4CAF50; color: white; padding: 15px; border-radius: 5px; margin: 10px 0; font-size: 16px;";
                successDiv.textContent = "✅ Payment saved successfully!";
                form.parentNode.insertBefore(successDiv, form);

                // Remove success message after 3 seconds
                setTimeout(() => successDiv.remove(), 3000);

                // Update the payment matrix table
                const monthNames = ["January", "February", "March", "April", "May", "June",
                                  "July", "August", "September", "October", "November", "December"];
                const rows = document.querySelectorAll("table.payment-matrix tbody tr");
                const headerRow = document.querySelector("table.payment-matrix thead tr");
                const headers = headerRow ? Array.from(headerRow.querySelectorAll("th")) : [];

                function markPaid(yearStr, monthIndex) {
                    const monthName = monthNames[monthIndex];
                    for (let row of rows) {
                        const monthCell = row.querySelector("td");
                        if (monthCell && monthCell.textContent === monthName) {
                            const yearIndex = headers.findIndex(h => h.textContent.trim() === String(yearStr));
                            if (yearIndex > 0) {
                                const statusCell = row.querySelectorAll("td")[yearIndex];
                                if (statusCell) statusCell.textContent = "✅";
                            }
                            break;
                        }
                    }
                }

                // prefer server-provided month/payment_type if present
                const respMonth = data.month;
                const respType = data.payment_type || payment_type;
                if (respMonth) {
                    const [rYear, rMonth] = respMonth.split('-');
                    if (respType === 'monthly') {
                        markPaid(rYear, parseInt(rMonth, 10) - 1);
                    } else if (respType === 'yearly') {
                        // mark all 12 months of the year returned
                        const y = parseInt(rYear, 10);
                        for (let m = 0; m < 12; m++) markPaid(y, m);
                    }
                } else {
                    if (payment_type === 'monthly' && year_month_covered) {
                        const [year, month] = year_month_covered.split("-");
                        const monthIndex = parseInt(month, 10) - 1;
                        markPaid(year, monthIndex);
                    } else if (payment_type === 'yearly' && year_covered) {
                        const year = parseInt(year_covered, 10);
                        for (let m = 0; m < 12; m++) markPaid(year, m);
                    }
                }

                // Update totals in the DOM if provided
                if (data.total_paid !== undefined) {
                    const tp = document.getElementById('total_paid');
                    if (tp) tp.textContent = `$${parseFloat(data.total_paid).toFixed(2)}`;
                }
                if (data.expected_total !== undefined) {
                    const et = document.getElementById('expected_total');
                    if (et) et.textContent = `$${parseFloat(data.expected_total).toFixed(2)}`;
                }
                if (data.expected_unpaid !== undefined) {
                    const eu = document.getElementById('expected_unpaid');
                    if (eu) eu.textContent = `$${parseFloat(data.expected_unpaid).toFixed(2)}`;
                }
                if (data.balance !== undefined) {
                    const b = document.getElementById('balance');
                    if (b) b.textContent = `$${parseFloat(data.balance).toFixed(2)}`;
                }

                // Clear form
                form.reset();
            } else {
                alert("❌ Error: " + (data.error || "Payment failed"));
            }
        } catch (error) {
            alert("❌ Network error: " + error.message);
        }
    });
}
