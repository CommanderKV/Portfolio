
////////////////////////////////
//  Setup event listener for  //
//  contact form submission   //
////////////////////////////////
document.getElementById("contact-form").addEventListener("submit", function(event) {
    event.preventDefault();  // Prevent default form submission

    // Get form data
    let formData = {
        name: document.getElementById("contact-name").value.trim(),
        email: document.getElementById("contact-email").value.trim(),
        message: document.getElementById("contact-message").value.trim()
    };

    // Clear previous errors
    document.querySelectorAll(".error").forEach(el => el.innerText = "");
    document.getElementById("form-message").innerText = "";

    fetch("/api/contact", {
        method: "POST",
        body: JSON.stringify(formData),
        headers: {
            "Content-Type": "application/json"
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById("form-message").innerText = data.message;
            document.getElementById("form-message").style.color = "var(--success-color)";
            document.getElementById("contact-form").reset();  // Reset form on success
        } else {
            document.getElementById("form-message").innerText = "Please fix the errors before submitting.";
            document.getElementById("form-message").style.color = "var(--danger-color)";
            for (let field in data.errors) {
                document.getElementById(field + "-error").innerText = data.errors[field];
            }
        }
    })
    .catch(error => console.error("Error:", error));
});