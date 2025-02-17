// Get the education and work elements needed
let educationBtn = document.getElementById("education-btn");
let education = document.getElementById("education");
let workBtn = document.getElementById("work-btn");
let work = document.getElementById("work");

function toggleActive() {
    if (educationBtn.classList.contains("active")) {
        educationBtn.classList.remove("active");
        workBtn.classList.add("active");

        education.classList.add("in-active");
        work.classList.remove("in-active");

    } else {
        educationBtn.classList.add("active");
        workBtn.classList.remove("active");

        education.classList.remove("in-active");
        work.classList.add("in-active");
    }
}

educationBtn.addEventListener("click", toggleActive);
workBtn.addEventListener("click", toggleActive);