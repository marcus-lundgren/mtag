const ZOOM_FACTOR = 0.03;
const MOVE_FACTOR = 0.05;
const TIMELINE_SIDE_PADDING = 29;

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
        this.startDate = this.currentTimelineDate.start;
        this.stopDate = this.currentTimelineDate.stop;
        this.boundaryDelta = this.stopDate - this.startDate;
    }

    getCurrentBoundaryDeltaInTime() {
        return this.boundaryDelta;
    }

    getTimelineStart() {
        return this.startDate;
    }

    getTimelineStop() {
        return this.stopDate;
    }

    zoom(zoomingIn, callRenderTimeline) {
        let zoomStepInSeconds = this.boundaryDelta * ZOOM_FACTOR / 1000;

        // Do not zoom in too far
        if (zoomingIn && zoomStepInSeconds < 5) {
            return;
        }

        if (!zoomingIn) {
            zoomStepInSeconds = -zoomStepInSeconds;
        }

        this.startDate.setSeconds(this.startDate.getSeconds() + zoomStepInSeconds / 2);
        this.stopDate.setSeconds(this.stopDate.getSeconds() - zoomStepInSeconds / 2);
        this.update();
        callRenderTimeline();
    }

    move(movingLeft, renderTimeline) {
        let moveStep = this.boundaryDelta * MOVE_FACTOR;
        if (movingLeft) {
            moveStep = Math.min(this.startDate - this.currentTimelineDate.date, moveStep);
            moveStep = -moveStep;
        } else {
            moveStep = Math.min(this.endOfDate - this.stopDate, moveStep);
        }

        this.startDate.setMilliseconds(this.startDate.getMilliseconds() + moveStep);
        this.stopDate.setMilliseconds(this.stopDate.getMilliseconds() + moveStep);
        this.update();
        renderTimeline();
    }

    dateToPixel(date) {
        const deltaFromStart = date - this.startDate;
        const relativeDelta = deltaFromStart / this.boundaryDelta;
        return relativeDelta * this.canvasWidthWithoutPadding + TIMELINE_SIDE_PADDING;
    }
}

const TIMELINE_HEIGHT = 30;
const TAGGED_ENTRIES_START_Y = TIMELINE_HEIGHT + 10;
const SPACE_BETWEEN_TIMELINES = TIMELINE_HEIGHT;
const TIMELINE_MARGIN = 10;

export const renderTimeline = (timelineHelper, timelineCanvas, taggedEntries, loggedEntries, activityEntries) => {
    const canvasWidth = timelineCanvas.width;
    const canvasHeight = timelineCanvas.height;

    const entriesHeight = (canvasHeight - TAGGED_ENTRIES_START_Y - SPACE_BETWEEN_TIMELINES - TIMELINE_MARGIN) / 2;
    const loggedEntriesStartY = TAGGED_ENTRIES_START_Y + entriesHeight + SPACE_BETWEEN_TIMELINES;

    const ctx = timelineCanvas.getContext("2d");

    // Clear the background
    ctx.fillStyle = "#FFF";
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    // Activity entries
    activityEntries.forEach((ae) => {
        ctx.fillStyle = ae.color;

        const startX = timelineHelper.dateToPixel(ae.start);
        const stopX = timelineHelper.dateToPixel(ae.stop);
        ctx.fillRect(startX, 0, stopX - startX, canvasHeight);
    });

    // Time row
    // - Background
    ctx.fillStyle = "#595959";
    ctx.fillRect(0, 0, canvasWidth, TIMELINE_HEIGHT);

    // - Set up font related things
    ctx.font = "12px Arial";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    const textWidth = ctx.measureText("88:88").width;
    const minuteIncrement = calculateMinuteIncrement(textWidth, canvasWidth, timelineHelper.getCurrentBoundaryDeltaInTime());

    const startOfTimeTimeline = new Date(timelineHelper.getTimelineStart());
    startOfTimeTimeline.setSeconds(0);
    startOfTimeTimeline.setMinutes(0);
    const TIMELINE_START_Y = TIMELINE_HEIGHT - 10;
    ctx.strokeStyle = "#B3B3B3";
    const timelineStop = timelineHelper.getTimelineStop();
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
    taggedEntries.forEach((te) => {
        ctx.fillStyle = te.color;

        const startX = timelineHelper.dateToPixel(te.start);
        const stopX = timelineHelper.dateToPixel(te.stop);
        ctx.fillRect(startX, TAGGED_ENTRIES_START_Y, stopX - startX, entriesHeight);
    });

    // Logged entries
    loggedEntries.forEach((le) => {
        ctx.fillStyle = le.color;

        const startX = timelineHelper.dateToPixel(le.start);
        const stopX = timelineHelper.dateToPixel(le.stop);
        ctx.fillRect(startX, loggedEntriesStartY, stopX - startX, entriesHeight);
    });

    // Draw the sides
    ctx.fillStyle = "rgba(128, 128, 128, 0.5)";
    ctx.fillRect(0, 0, TIMELINE_SIDE_PADDING, canvasHeight);
    ctx.fillRect(canvasWidth - TIMELINE_SIDE_PADDING, 0, TIMELINE_SIDE_PADDING, canvasHeight);
}

function getHourAndMinuteText(date) {
    const hours = date.getHours();
    const minutes = date.getMinutes();

    const hoursString = hours < 10 ? "0" + hours : hours;
    const minuteString = minutes < 10 ? "0" + minutes : minutes;

    return hoursString + ":" + minuteString;
}

function calculateMinuteIncrement(textWidth, canvasWidth, dayDiff) {
    const pixelsPerSeconds = canvasWidth / (dayDiff / 1000);
    const textWidthWithPadding = (textWidth + 6) / pixelsPerSeconds / 60;
    if (textWidthWithPadding > 59) {
        return (Math.floor(textWidthWithPadding / 60) + 1) * 60;
    } else if (textWidthWithPadding > 29) {
        return 60;
    } else if (textWidthWithPadding > 14) {
        return 30;
    } else if (textWidthWithPadding > 9) {
        return 15;
    } else if (textWidthWithPadding > 4) {
        return 10;
    } else if (textWidthWithPadding >= 1) {
        return 5;
    }

    return 1;
}
