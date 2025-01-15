const canvasContainer = document.getElementById("canvas-container");
const overlayCanvas = document.getElementById('overlay');
const timelineCanvas = document.getElementById('timeline');

const colors = [
    "#123",
    "#452",
    "#ddd",
    "#815"
];

function randomColor() {
    return colors[Math.floor(Math.random() * colors.length)];
}

var loggedEntries = [];
const currentDate = new Date("2025-01-13");

function renderTimeline() {
    const ctx = timelineCanvas.getContext("2d");
    ctx.fillStyle = "#FFF";
    const canvasWidth = timelineCanvas.width;
    ctx.fillRect(0, 0, canvasWidth, timelineCanvas.height);
    const startOfDay = new Date(new Date(currentDate).setHours(20, 0, 0, 0));
    const endOfDay = new Date(new Date(currentDate).setHours(22, 59, 59, 999));
    const dayDiff = endOfDay - startOfDay;

    loggedEntries.forEach((le) => {
        ctx.fillStyle = le.color;

        const startX = ((le.start - startOfDay) / dayDiff) * canvasWidth;
        const stopX = ((le.stop - startOfDay) / dayDiff) * canvasWidth;
        ctx.fillRect(startX, 0, stopX - startX, 50);
    });
}

function setUpListeners() {
    const ctx = overlayCanvas.getContext("2d");
    new ResizeObserver(() => {
        console.log("Resizing..");
        overlayCanvas.width = canvasContainer.clientWidth;
        overlayCanvas.height = canvasContainer.clientHeight;
        timelineCanvas.width = canvasContainer.clientWidth;
        timelineCanvas.height = canvasContainer.clientHeight;
        renderTimeline();
    }).observe(canvasContainer);

    overlayCanvas.addEventListener("mousemove", (event) => {
        const mouseX = event.offsetX;
        ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
        ctx.strokeStyle = "#444";
        ctx.beginPath();
        ctx.moveTo(mouseX, 0);
        ctx.lineTo(mouseX, overlayCanvas.height);
        ctx.stroke();
    });

    overlayCanvas.addEventListener("mouseleave", (event) => {
        ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
    });
}

async function fetchEntries() {
    const dateString = currentDate.toISOString().split("T")[0];
    const url = "/entries/" + dateString;
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Response status ${response.status}`);
        }

        const json = await response.json();
        console.log(json);
        json.logged_entries.forEach((le) => {
            loggedEntries.push({
                start: new Date(le.start),
                stop: new Date(le.stop),
                title: le.application_window.title,
                color: randomColor()
            });
        });
    } catch (error) {
        console.error(error.message);
    }
}

setUpListeners();
fetchEntries().then(() => {
    renderTimeline();
});
