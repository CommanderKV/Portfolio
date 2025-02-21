const projectCards = document.querySelectorAll('.project-card');

projectCards.forEach(card => {
    card.addEventListener("click", (event) => {
        const target = event.target;
        if (target.closest('.project-cta a')) {
            // If the "See project" button is clicked, go to the project URL
            window.open(target.closest('.project-cta a').href, '_blank');
        } else {
            // If anything else in the project card is clicked, go to the custom URL
            window.location.href = "/projects/" + card.getAttribute("data");
        }
    });
});