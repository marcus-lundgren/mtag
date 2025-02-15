const ZOOM_FACTOR = 0.03;
const MOVE_FACTOR = 0.05;
const TIMELINE_SIDE_PADDING = 29;
const MAX_BOUNDARY = (23 * 3600 + 59 * 60 + 59) * 1000;

const TIMELINE_HEIGHT = 30;
const TAGGED_ENTRIES_START_Y = TIMELINE_HEIGHT + 10;
const TIMELINE_MARGIN = 10;

export const overlayProperties = {
    canvas: undefined,
    specialMark: undefined,
    mouseX: undefined,
    mouseY: undefined,
    hoveredEntry: undefined
};

export const timelineProperties = {
    canvas: undefined,
    currentTimelineDate: undefined,
    minuteIncrement: undefined,

    // Timeline dimensions
    entityHeight: undefined,
    taggedEntryStartY: TAGGED_ENTRIES_START_Y,
    loggedEntryStartY: undefined,
    boundaryStart: undefined,
    boundaryStop: undefined,
    boundaryDelta: undefined,
    viewportStart: undefined,
    viewportStop: undefined,

    // Entries
    timelineLoggedEntries: [],
    timelineTaggedEntries: [],
    timelineActivityEntries: [],
    visibleLoggedEntries: [],
    visibleTaggedEntries: [],
    visibleActivityEntries: []
};

export class TimelineHelper {
    constructor(canvas, currentTimelineDate) {
        this.canvas = canvas;
        this.currentTimelineDate = currentTimelineDate;
        this.update();
    }

    update() {
        this.canvasWidth = this.canvas.offsetWidth;
        this.canvasWidthWithoutPadding = this.canvasWidth - (TIMELINE_SIDE_PADDING * 2);
        this.startOfDate = this.currentTimelineDate.date;
        this.endOfDate = new Date(this.currentTimelineDate.date);
        this.endOfDate.setHours(23, 59, 59, 0);
        this.boundaryStart = this.currentTimelineDate.start;
        this.boundaryStop = this.currentTimelineDate.stop;
        this.boundaryDelta = this.boundaryStop - this.boundaryStart;
    }

    getCurrentBoundaryDeltaInTime() {
        return this.boundaryDelta;
    }

    getBoundaryStart() {
        return this.boundaryStart;
    }

    getBoundaryStop() {
        return this.boundaryStop;
    }

    setBoundaries(newStart, newStop) {
        this.currentTimelineDate.start.setTime(newStart.getTime());
        this.currentTimelineDate.stop.setTime(newStop.getTime());
        this.update();
    }

    zoom(zoomingIn, mouseDate, callRenderTimeline) {
        let zoomStepInMilliseconds = this.boundaryDelta * ZOOM_FACTOR;
        let newBoundaryDelta = this.boundaryDelta;
        const mouseOffset = mouseDate - this.boundaryStart;
        const mouseRelativeOffset = mouseOffset / this.boundaryDelta;
        const oldRelativeMousePositionInMilliseconds = mouseRelativeOffset * this.boundaryDelta;

        let newStartInMilliseconds = this.boundaryStart.getTime();

        if (zoomingIn) {
            // Do not zoom in too far
            if (zoomStepInMilliseconds < 5000) {
                return;
            }

            newBoundaryDelta -= zoomStepInMilliseconds;
            const newRelativeMousePositionInMilliseconds = Math.floor(newBoundaryDelta * mouseRelativeOffset);
            const startOffset = oldRelativeMousePositionInMilliseconds - newRelativeMousePositionInMilliseconds;
            newStartInMilliseconds += startOffset;
        } else {
            // Do not zoom out in far
            if (MAX_BOUNDARY <= this.boundaryDelta) {
                return;
            }

            newBoundaryDelta += zoomStepInMilliseconds;
            const startOfDateInMilliseconds = this.startOfDate.getTime();
            if (MAX_BOUNDARY <= newBoundaryDelta) {
                newBoundaryDelta = MAX_BOUNDARY;
                newStartInMilliseconds = startOfDateInMilliseconds;
            } else {
                const newRelativeMousePositionInMilliseconds = Math.floor(newBoundaryDelta * mouseRelativeOffset);
                const startOffset = oldRelativeMousePositionInMilliseconds - newRelativeMousePositionInMilliseconds;
                newStartInMilliseconds += startOffset;

                // Ensure that we don't get too far to the left
                if (newStartInMilliseconds < startOfDateInMilliseconds) {
                    newStartInMilliseconds = startOfDateInMilliseconds;
                }

                // Ensure that we don't get too far to the right
                const endOfDateInMilliseconds = startOfDateInMilliseconds + MAX_BOUNDARY;
                if (endOfDateInMilliseconds < newStartInMilliseconds + newBoundaryDelta) {
                    newStartInMilliseconds = endOfDateInMilliseconds - newBoundaryDelta;
                }
            }
        }

        this.boundaryStart.setTime(newStartInMilliseconds);
        this.boundaryStop.setTime(newStartInMilliseconds + newBoundaryDelta);
        this.update();
        callRenderTimeline();
    }

    move(movingLeft, renderTimeline) {
        let moveStep = this.boundaryDelta * MOVE_FACTOR;
        if (movingLeft) {
            moveStep = Math.min(this.boundaryStart - this.currentTimelineDate.date, moveStep);
            moveStep = -moveStep;
        } else {
            moveStep = Math.min(this.endOfDate - this.boundaryStop, moveStep);
        }

        this.boundaryStart.setMilliseconds(this.boundaryStart.getMilliseconds() + moveStep);
        this.boundaryStop.setMilliseconds(this.boundaryStop.getMilliseconds() + moveStep);
        this.update();
        renderTimeline();
    }

    dateToPixel(date) {
        const deltaFromStart = date - this.boundaryStart;
        const relativeDelta = deltaFromStart / this.boundaryDelta;
        return Math.floor(relativeDelta * this.canvasWidthWithoutPadding + TIMELINE_SIDE_PADDING);
    }

    pixelToDate(x) {
        if (x - TIMELINE_SIDE_PADDING <= 0) {
            return this.boundaryStart;
        } else if (x >= this.canvasWidth - TIMELINE_SIDE_PADDING) {
            return this.boundaryStop;
        }

        const xToUse = x - TIMELINE_SIDE_PADDING;
        const relativePixelDelta = xToUse / this.canvasWidthWithoutPadding;
        const d = new Date(this.boundaryStart.getTime() + relativePixelDelta * this.boundaryDelta);
        return d;
    }
}

export class TimelineEntry {
    constructor(entry, parsedEntry, timelineHelper, texts) {
        this.start = parsedEntry.start;
        this.stop = parsedEntry.stop;
        this.color = parsedEntry.color;
        this.entry = entry;
        this.update(timelineHelper);
        this.texts = texts;
    }

    update(timelineHelper) {
        this.startX = timelineHelper.dateToPixel(this.start);
        this.stopX = timelineHelper.dateToPixel(this.stop);
        this.width = this.stopX - this.startX;
    }

    getColor() {
        return this.color;
    }

    getStart() {
        return this.start;
    }

    getStop() {
        return this.stop;
    }

    getStartX() {
        return this.startX;
    }

    getStopX() {
        return this.stopX;
    }

    getWidth() {
        return this.width;
    }

    getTexts() {
        return this.texts;
    }

    containsX(x) {
        return this.startX <= x && x <= this.stopX;
    }
}

const SPACE_BETWEEN_TIMELINES = TIMELINE_HEIGHT;
export const updateTimelineProperties = (timelineHelper) => {
    const canvas = timelineProperties.canvas;
    const canvasWidth = canvas.width;
    const canvasHeight = canvas.height;
    timelineProperties.entityHeight = (canvasHeight - timelineProperties.taggedEntryStartY - SPACE_BETWEEN_TIMELINES - TIMELINE_MARGIN) / 2;
    timelineProperties.loggedEntryStartY = timelineProperties.taggedEntryStartY + timelineProperties.entityHeight + SPACE_BETWEEN_TIMELINES;

    const ctx = canvas.getContext("2d");
    ctx.font = "14px Arial";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    const textWidth = ctx.measureText("88:88").width;
    timelineProperties.minuteIncrement = calculateMinuteIncrement(textWidth, canvasWidth, timelineHelper.getCurrentBoundaryDeltaInTime());
}

export const renderTimeline = (timelineHelper) => {
    const canvas = timelineProperties.canvas;
    const canvasWidth = canvas.width;
    const canvasHeight = canvas.height;

    const entriesHeight = timelineProperties.entityHeight;

    const ctx = canvas.getContext("2d");

    // Clear the background
    ctx.fillStyle = "#FFF";
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    // Activity entries
    timelineProperties.visibleActivityEntries.forEach((ae) => {
        ctx.fillStyle = ae.getColor();
        ctx.fillRect(ae.getStartX(), 0, ae.getWidth(), canvasHeight);
    });

    // Time row
    // - Background
    ctx.fillStyle = "#595959";
    ctx.fillRect(0, 0, canvasWidth, TIMELINE_HEIGHT);

    // - Set up font related things
    const minuteIncrement = timelineProperties.minuteIncrement;
    const startOfTimeTimeline = new Date(timelineHelper.getBoundaryStart());
    startOfTimeTimeline.setSeconds(0);
    startOfTimeTimeline.setMinutes(0);
    const TIMELINE_START_Y = TIMELINE_HEIGHT - 10;

    ctx.font = "14px Arial";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.strokeStyle = "#B3B3B3";
    const timelineStop = new Date(timelineHelper.getBoundaryStop());
    timelineStop.setMinutes(timelineStop.getMinutes() + minuteIncrement);
    for (let currentTime = startOfTimeTimeline;
         currentTime < timelineStop;
         currentTime.setMinutes(currentTime.getMinutes() + minuteIncrement)) {
        const lineX = timelineHelper.dateToPixel(currentTime);
        ctx.beginPath();
        ctx.moveTo(lineX, TIMELINE_START_Y);
        ctx.lineTo(lineX, TIMELINE_HEIGHT);
        ctx.stroke();
        const timeText = getHourAndMinuteText(currentTime);
        ctx.fillStyle = currentTime.getMinutes() === 0 ? "#E6E64C" : "#33CCFF";
        ctx.fillText(timeText, lineX, 5);
    }

    // Tagged entries
    timelineProperties.visibleTaggedEntries.forEach((te) => {
        ctx.fillStyle = te.getColor();
        ctx.fillRect(te.getStartX(), timelineProperties.taggedEntryStartY, te.getWidth(), entriesHeight);
    });

    // Logged entries
    timelineProperties.visibleLoggedEntries.forEach((le) => {
        ctx.fillStyle = le.getColor();
        ctx.fillRect(le.getStartX(), timelineProperties.loggedEntryStartY, le.getWidth(), entriesHeight);
    });

    // Draw the sides
    ctx.fillStyle = "rgba(128, 128, 128, 0.5)";
    ctx.fillRect(0, 0, TIMELINE_SIDE_PADDING, canvasHeight);
    ctx.fillRect(canvasWidth - TIMELINE_SIDE_PADDING, 0, TIMELINE_SIDE_PADDING, canvasHeight);
}

export const updateOverlayProperties = (mouseX, mouseY) => {
    overlayProperties.mouseX = mouseX;
    overlayProperties.mouseY = mouseY;

    const entityHeight = timelineProperties.entityHeight;
    const loggedEntryStartY = timelineProperties.loggedEntryStartY;
    overlayProperties.hoveredEntry = undefined;
    if (loggedEntryStartY <= mouseY
        && mouseY <= loggedEntryStartY + entityHeight) {
        console.log("Looking for logged entries...");
        // Binary search to find the hovered over entry
        const visibleLoggedEntries = timelineProperties.visibleLoggedEntries;
        let start = 0;
        let stop = visibleLoggedEntries.length - 1;
        let hoveredEntry = undefined;
        while (visibleLoggedEntries.specialMark === undefined
               && start <= stop) {
            const middle = start + Math.floor((stop - start) / 2);
            const currentEntry = visibleLoggedEntries[middle];
            if (currentEntry.containsX(mouseX)) {
                overlayProperties.hoveredEntry = currentEntry;
                break;
            } else if (mouseX < currentEntry.getStartX()) {
                stop = middle - 1;
            } else {
                start = middle + 1;
            }
        }
    }
}

export const renderOverlay = (timelineHelper) => {
    const canvas = overlayProperties.canvas;
    const canvasWidth = canvas.width;
    const canvasHeight = canvas.height;

    const mouseX = overlayProperties.mouseX;
    const mouseY = overlayProperties.mouseY;

    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvasWidth, canvasHeight);
    ctx.strokeStyle = "#444";
    ctx.beginPath();
    ctx.moveTo(mouseX, 0);
    ctx.lineTo(mouseX, canvasHeight);
    ctx.stroke();

    const hoveredEntry = overlayProperties.hoveredEntry;
    const specialMark = overlayProperties.specialMark;
    if (hoveredEntry !== undefined) {
        // Hovered entry
        // ctx.fillStyle = "rgba(179, 179, 179, 0.2)";
        ctx.fillStyle = "rgba(179, 179, 179, 0.7)";
        ctx.fillRect(hoveredEntry.getStartX(), timelineProperties.loggedEntryStartY, hoveredEntry.getWidth(), timelineProperties.entityHeight);
    } else if (specialMark !== undefined) {
        // Special mark handling
        ctx.fillStyle = specialMark.color;
        ctx.fillRect(specialMark.x, 0, mouseX - specialMark.x, canvasHeight);
    }

    // Tooltip
    const mouseDate = timelineHelper.pixelToDate(mouseX);
    const mouseDateString = getHourAndMinuteAndSecondText(mouseDate);

    ctx.font = "14px Arial";
    ctx.textBaseline = "top";

    const texts = [mouseDateString];
    if (hoveredEntry !== undefined) {
        texts.push(...hoveredEntry.texts);
    }

    const tooltipText = texts.join(" || ");

    const textMeasurement = ctx.measureText(tooltipText);
    const textWidth = textMeasurement.width;
    const textHeight = textMeasurement.fontBoundingBoxAscent + textMeasurement.fontBoundingBoxDescent;

    const rectangleWidth = textWidth + 5 * 2;
    const rectangleHeight = textHeight + 5 * 2;

    const rectangleX = Math.min(mouseX + 10, canvasWidth - rectangleWidth);
    const rectangleY = Math.min(mouseY + 10, canvasHeight - rectangleHeight);

    const textX = rectangleX + 5;
    const textY = rectangleY + 7;

    ctx.fillStyle = "rgba(75, 75, 175, 0.75)";
    ctx.fillRect(rectangleX, rectangleY, rectangleWidth, rectangleHeight);
    ctx.strokeStyle = "rgba(205, 154, 51, 0.8)"
    ctx.strokeRect(rectangleX, rectangleY, rectangleWidth, rectangleHeight);
    ctx.fillStyle = "yellow";
    ctx.fillText(tooltipText, textX, textY);
}

export const getHourAndMinuteAndSecondText = (date) => {
    const hourString = padLeftWithZero(date.getHours());
    const minuteString = padLeftWithZero(date.getMinutes());
    const secondString = padLeftWithZero(date.getSeconds());

    return `${hourString}:${minuteString}:${secondString}`;
}

function getHourAndMinuteText(date) {
    const hourString = padLeftWithZero(date.getHours());
    const minuteString = padLeftWithZero(date.getMinutes());

    return `${hourString}:${minuteString}`;
}

export const padLeftWithZero = (n) => {
    return n.toString().padStart(2, "0");
}

function calculateMinuteIncrement(textWidth, canvasWidth, dayDiff) {
    const pixelsPerSeconds = canvasWidth / (dayDiff / 1000);
    const textWidthWithPaddingInMinutes = (textWidth + 6) / pixelsPerSeconds / 60;
    if (textWidthWithPaddingInMinutes > 59) {
        return (Math.floor(textWidthWithPaddingInMinutes / 60) + 1) * 60;
    } else if (textWidthWithPaddingInMinutes > 29) {
        return 60;
    } else if (textWidthWithPaddingInMinutes > 14) {
        return 30;
    } else if (textWidthWithPaddingInMinutes > 9) {
        return 15;
    } else if (textWidthWithPaddingInMinutes > 4) {
        return 10;
    } else if (textWidthWithPaddingInMinutes >= 1) {
        return 5;
    }

    return 1;
}
