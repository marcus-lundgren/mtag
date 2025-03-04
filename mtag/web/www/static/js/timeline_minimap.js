import { padLeftWithZero } from "./timeline_utilities.js";
import { TimelineHelper } from "./timeline.js";

const minimapContainer = document.getElementById("minimap-container");
const minimapCanvas = document.getElementById("minimap");

const minimapProperties = {
    taggedEntryBlocks: [],
    loggedEntryBlocks: []
};

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
}

export const setMinimapEntries = (taggedEntries, loggedEntries) => {
    minimapProperties.taggedEntryBlocks.length = 0;
    minimapProperties.loggedEntryBlocks.length = 0;

    function addBlocks(entries, blocksList) {
        let currentBlock = { start: undefined, stop: undefined };
        for (const entry of entries) {
            // Continue with the current block
            if (currentBlock.stop === entry.start) {
                currentBlock.stop = entry.stop;
                continue;
            }

            // We have an existing block, but the current entry doesn't start where it stops.
            // Add it to the list and create a new block
            if (currentBlock.stop !== undefined && currentBlock.stop !== entry.start) {
                currentBlock.stop = new Date(currentBlock.stop);
                blocksList.push(currentBlock);
                currentBlock = { start: undefined, stop: undefined };
            }

            // Our current block is empty. Initialize it with the current entries start and stop.
            if (currentBlock.stop === undefined) {
                currentBlock.start = new Date(entry.start);
                currentBlock.stop = entry.stop;
                continue;
            }
        }

        // Add the finally created block if it exists
        if (currentBlock.stop !== undefined) {
            currentBlock.stop = new Date(currentBlock.stop);
            blocksList.push(currentBlock);
        }
    }

    addBlocks(taggedEntries, minimapProperties.taggedEntryBlocks);
    addBlocks(loggedEntries, minimapProperties.loggedEntryBlocks);
};

export const renderMinimap = () => {
    const canvasWidth = minimapCanvas.width;
    const canvasHeight = minimapCanvas.height;
    const entriesHeight = canvasHeight / 5;
    const taggedEntriesStartY = entriesHeight * 1;
    const loggedEntriesStartY = entriesHeight * 3.5;

    const ctx = minimapCanvas.getContext("2d");

    // Clear the background
    ctx.fillStyle = "#FFF";
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    // Time row
    // - Set up font related things
    const startOfTimeTimeline = new Date(minimapProperties.startOfDate);

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

    // Tagged entry blocks
    ctx.fillStyle = "rgb(255, 163, 0)";
    for (const block of minimapProperties.taggedEntryBlocks) {
        const start = timelineHelper.dateToPixel(block.start);
        const stop = timelineHelper.dateToPixel(block.stop);
        ctx.fillRect(start, taggedEntriesStartY, stop - start, entriesHeight);
    }

    // Logged entry blocks
    ctx.fillStyle = "rgb(77, 77, 205)";
    for (const block of minimapProperties.loggedEntryBlocks) {
        const start = timelineHelper.dateToPixel(block.start);
        const stop = timelineHelper.dateToPixel(block.stop);
        ctx.fillRect(start, loggedEntriesStartY, stop - start, entriesHeight);
    }

    // Draw the current viewport boundary in the timeline canvas
    const boundaryStartX = timelineHelper.dateToPixel(actualCurrentTimelineDate.start);
    const boundaryStopX = timelineHelper.dateToPixel(actualCurrentTimelineDate.stop);

    ctx.fillStyle = "rgba(102, 102, 102, 0.5)";
    ctx.fillRect(boundaryStartX, 0, boundaryStopX - boundaryStartX, canvasHeight);
};
