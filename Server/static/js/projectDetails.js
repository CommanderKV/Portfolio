
document.querySelectorAll('.language-section').forEach(section => {
    section.addEventListener('mouseover', () => {
        const lang = section.getAttribute('data-lang');
        document.querySelectorAll(`.language-item[data-lang="${lang}"]`).forEach(item => {
            item.classList.add('highlight');
        });
        section.classList.add('highlight');
    });
    section.addEventListener('mouseout', () => {
        const lang = section.getAttribute('data-lang');
        document.querySelectorAll(`.language-item[data-lang="${lang}"]`).forEach(item => {
            item.classList.remove('highlight');
        });
        section.classList.remove('highlight');
    });
});

document.querySelectorAll('.language-item').forEach(item => {
    item.addEventListener('mouseover', () => {
        const lang = item.getAttribute('data-lang');
        document.querySelectorAll(`.language-section[data-lang="${lang}"]`).forEach(section => {
            section.classList.add('highlight');
        });
        item.classList.add('highlight');
    });
    item.addEventListener('mouseout', () => {
        const lang = item.getAttribute('data-lang');
        document.querySelectorAll(`.language-section[data-lang="${lang}"]`).forEach(section => {
            section.classList.remove('highlight');
        });
        item.classList.remove('highlight');
    });
});

// Auto-scroll through screenshots with active class toggle
const images = document.querySelectorAll('#images img');
let currentIndex = 0;
const scrollInterval = 3000; // 3 seconds

// Set the first element to be active to start
images[0].classList.toggle("active");

function updateActiveImage() {
    images.forEach((img, index) => {
    img.classList.toggle('active', index === currentIndex);
    });
}

setInterval(() => {
    currentIndex = (currentIndex + 1) % images.length;
    updateActiveImage();
}, scrollInterval);

// Initialize the first image as active
updateActiveImage();
