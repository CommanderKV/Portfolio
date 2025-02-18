
////////////////////////////////
//  Setup event listener for  //
//  contact form submission   //
////////////////////////////////
document.getElementById("contact-form").addEventListener("submit", function(event) {
    event.preventDefault();  // Prevent default form submission

    // Get form data
    let formData = {
        email: document.getElementById("email").value.trim(),
        message: document.getElementById("message").value.trim()
    };

    // Clear previous errors
    document.querySelectorAll(".error").forEach(el => el.innerText = "");
    document.getElementById("error-msg").innerText = "";

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
            document.getElementById("error-msg").innerText = data.message;
            document.getElementById("error-msg").style.color = "var(--success-color)";
            document.getElementById("contact-form").reset();  // Reset form on success
        } else {
            document.getElementById("error-msg").innerText = data.errors[0];
            document.getElementById("error-msg").style.color = "var(--danger-color)";
        }
    })
    .catch(error => console.error("Error:", error));
});