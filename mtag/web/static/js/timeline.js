const canvasContainer = document.getElementById("canvas-container");
const overlayCanvas = document.getElementById('overlay');
const timelineCanvas = document.getElementById('timeline');

const colors = [
    "#123",
    "#452",
    "#ddd",
    "#815"
]
function randomColor() {
    return colors[Math.floor(Math.random() * colors.length)];
}

function createEntry(start) {
    return {
        startX: start,
        stopX: start + 30 + Math.random() * 140,
        color: randomColor()
    }
}

function overlayTimeline() {
    const ctx = timelineCanvas.getContext("2d");
    ctx.fillStyle = "#FFF";
    ctx.fillRect(0, 0, timelineCanvas.width, timelineCanvas.height);
    for (let i = 0; i < timelineCanvas.width;) {
        const entry = createEntry(i);
        ctx.fillStyle = entry.color;
        ctx.fillRect(entry.startX, 0, entry.stopX - entry.startX, 50);
        i = entry.stopX;
    }
}

function overlayTest() {
    const ctx = overlayCanvas.getContext("2d");
    new ResizeObserver(() => {
        console.log("Resizing..");
        overlayCanvas.width = canvasContainer.clientWidth;
        overlayCanvas.height = canvasContainer.clientHeight;
        timelineCanvas.width = canvasContainer.clientWidth;
        timelineCanvas.height = canvasContainer.clientHeight;
        overlayTimeline();
    }).observe(canvasContainer);

    overlayCanvas.addEventListener("mousemove", (event) => {
        const mouseX = event.offsetX;
        ctx.clearRect(0, 0, overlayCanvas.width * 100, overlayCanvas.height);
        ctx.strokeStyle = "#444";
        ctx.beginPath();
        ctx.moveTo(mouseX, 0);
        ctx.lineTo(mouseX, overlayCanvas.height);
        ctx.stroke();
    })
}

overlayTimeline();
overlayTest();
