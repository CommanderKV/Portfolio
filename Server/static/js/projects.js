
const projectCards = document.querySelectorAll('.project-card');

projectCards.forEach(card => {
    card.addEventListener("click", () => {
        window.location.href = "/projects/" + card.getAttribute("data");
    });
});