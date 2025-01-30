
const bars = document.querySelectorAll(".profile-details .repo-language-bar");
const texts = document.querySelectorAll(".profile-details .repo-languages-list li");

function handleHover(event) {
    const language = event.target.getAttribute("data-language");
    if (!language) return;

    // Select matching bar and text elements
    const matchingBars = document.querySelectorAll(`.repo-language-bar[data-language='${language}']`);
    const matchingTexts = document.querySelectorAll(`.repo-languages-list li[data-language='${language}']`);

    // Apply hover styles
    matchingBars.forEach(bar => {
        bar.style.height = "15px";
        bar.style.transform = "scale(1.1)";
        bar.style.transition = "all 0.3s ease-in-out";
        bar.style.borderRadius = "10px";
        bar.style.borderColor = "white";
        bar.style.borderStyle = "solid";
        bar.style.borderWidth = "1px";
        bar.style.zIndex = "1";
    });

    matchingTexts.forEach(text => {
        text.style.color = "white";
        text.style.transform = "scale(1.1)";
        text.style.transition = "all 0.3s ease-in-out";
    });
}

function handleMouseLeave(event) {
    const language = event.target.getAttribute("data-language");
    if (!language) return;

    // Select matching bar and text elements
    const matchingBars = document.querySelectorAll(`.repo-language-bar[data-language='${language}']`);
    const matchingTexts = document.querySelectorAll(`.repo-languages-list li[data-language='${language}']`);

    // Reset styles when hover ends
    matchingBars.forEach(bar => {
        bar.style.height = "10px";
        bar.style.transform = "scale(1)";
        bar.style.borderRadius = "";
        bar.style.borderColor = "";
        bar.style.borderStyle = "";
        bar.style.borderWidth = "";
        bar.style.zIndex = "0";
    });

    matchingTexts.forEach(text => {
        text.style.color = "";
        text.style.transform = "scale(1)";
    });
}

// Add event listeners to bars and text elements
bars.forEach(bar => {
    bar.addEventListener("mouseenter", handleHover);
    bar.addEventListener("mouseleave", handleMouseLeave);
});

texts.forEach(text => {
    text.addEventListener("mouseenter", handleHover);
    text.addEventListener("mouseleave", handleMouseLeave);
});