import { padLeftWithZero } from "./timeline_utilities.js";
import { TimelineHelper } from "./timeline.js";

const minimapContainer = document.getElementById("minimap-container");
const minimapCanvas = document.getElementById("minimap");

const minimapProperties = {};
let actualCurrentTimelineDate = undefined;

const timelineHelper = new TimelineHelper(minimapContainer, minimapProperties);

export const setUpMinimapListeners = (setNewTimelineCanvasBoundaries) => {
    new ResizeObserver(() => {
        console.log("Resizing..");
        minimapCanvas.width = minimapContainer.clientWidth;
        minimapCanvas.height = minimapContainer.clientHeight;
        timelineHelper.update();
        renderMinimap();
    }).observe(minimapContainer);

    const callSetNewTimelineCanvasBoundaries = (offsetX) => {
        let mouseDate = timelineHelper.pixelToDate(offsetX);
        if (mouseDate < actualCurrentTimelineDate.startOfDate) {
            mouseDate = actualCurrentTimelineDate.startOfDate;
        } else if (actualCurrentTimelineDate.endOfDate < mouseDate) {
            mouseDate = actualCurrentTimelineDate.endOfDate;
        }

        setNewTimelineCanvasBoundaries(mouseDate);
    };

    minimapCanvas.addEventListener("mousedown", (event) => {
        callSetNewTimelineCanvasBoundaries(event.offsetX);
    });

    minimapCanvas.addEventListener("mousemove", (event) => {
        if (event.buttons === 1) {
            callSetNewTimelineCanvasBoundaries(event.offsetX);
        }
    });
};

export const updateMinimapProperties = (currentTimelineDate) => {
    actualCurrentTimelineDate = currentTimelineDate;
    minimapProperties.startOfDate = currentTimelineDate.startOfDate;
    minimapProperties.start = currentTimelineDate.startOfDate;
    minimapProperties.date = currentTimelineDate.date;
    minimapProperties.stop = currentTimelineDate.endOfDate;
    minimapProperties.endOfDate = currentTimelineDate.endOfDate;
    timelineHelper.update();
};

export const renderMinimap = () => {
    const TIMELINE_HEIGHT = 10;
    const canvasWidth = minimapCanvas.width;
    const canvasHeight = minimapCanvas.height;

    const entriesHeight = 20;

    const ctx = minimapCanvas.getContext("2d");

    // Clear the background
    ctx.fillStyle = "#FFF";
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    // Time row
    // - Set up font related things
    const startOfTimeTimeline = new Date(minimapProperties.startOfDate);
    const TIMELINE_START_Y = TIMELINE_HEIGHT - 10;

    ctx.font = "20px Arial";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.strokeStyle = "#B3B3B3";
    const timelineStop = new Date(minimapProperties.endOfDate);
    for (let currentTime = startOfTimeTimeline;
         currentTime < timelineStop;
         currentTime.setHours(currentTime.getHours() + 1)) {
        const lineX = timelineHelper.dateToPixel(currentTime);
        const timeText = padLeftWithZero(currentTime.getHours());
        ctx.fillStyle = "#777";
        ctx.fillText(timeText, lineX, canvasHeight / 2);
    }

    // Draw the current viewport boundary in the timeline canvas
    const boundaryStartX = timelineHelper.dateToPixel(actualCurrentTimelineDate.start);
    const boundaryStopX = timelineHelper.dateToPixel(actualCurrentTimelineDate.stop);

    ctx.fillStyle = "rgba(102, 102, 102, 0.5)";
    ctx.fillRect(boundaryStartX, 0, boundaryStopX - boundaryStartX, canvasHeight);
};
