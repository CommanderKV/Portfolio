// Grab the dropdown elements
const dropdown = document.querySelector(".dropdown");
const toggle = document.querySelector(".dropdown-toggle");
const caret = document.querySelector(".caret");

toggle.addEventListener("click", function (event) {
    event.preventDefault();
    dropdown.classList.toggle("active");
});

// Close dropdown if clicked outside
document.addEventListener("click", function (event) {
    if (!dropdown.contains(event.target)) {
        dropdown.classList.remove("active");
    }
});