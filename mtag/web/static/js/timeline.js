export function handleZoom(zoomingIn, currentTimelineDate, renderTimeline) {
    const zoomFactor = 0.03;
    let zoomStepInSeconds = (currentTimelineDate.stop - currentTimelineDate.start) * zoomFactor / 1000;

    // Do not zoom in too far
    if (zoomingIn && zoomStepInSeconds < 5) {
        return;
    }

    if (!zoomingIn) {
        zoomStepInSeconds = -zoomStepInSeconds;
    }

    currentTimelineDate.start.setSeconds(currentTimelineDate.start.getSeconds() + zoomStepInSeconds / 2);
    currentTimelineDate.stop.setSeconds(currentTimelineDate.stop.getSeconds() - zoomStepInSeconds / 2);
    renderTimeline();
}

export function handleMove(movingLeft, currentTimelineDate, renderTimeline) {
    const moveFactor = 0.05;
    let moveStepInSeconds = (currentTimelineDate.stop - currentTimelineDate.start) * moveFactor / 1000;
    if (movingLeft) {
        moveStepInSeconds = -moveStepInSeconds;
    }

    currentTimelineDate.start.setSeconds(currentTimelineDate.start.getSeconds() + moveStepInSeconds);
    currentTimelineDate.stop.setSeconds(currentTimelineDate.stop.getSeconds() + moveStepInSeconds);
    renderTimeline();
}

const TIMELINE_HEIGHT = 30;
const TAGGED_ENTRIES_START_Y = TIMELINE_HEIGHT + 10;
const SPACE_BETWEEN_TIMELINES = TIMELINE_HEIGHT;
const TIMELINE_MARGIN = 10;

export const renderTimeline = (timelineCanvas, currentTimelineDate, taggedEntries, loggedEntries, activityEntries) => {
    const canvasWidth = timelineCanvas.width;
    const canvasHeight = timelineCanvas.height;
    const timelineStart = currentTimelineDate.start;
    const timelineStop = currentTimelineDate.stop;
    const dayDiff = timelineStop - timelineStart;

    const entriesHeight = (canvasHeight - TAGGED_ENTRIES_START_Y - SPACE_BETWEEN_TIMELINES - TIMELINE_MARGIN) / 2;
    const loggedEntriesStartY = TAGGED_ENTRIES_START_Y + entriesHeight + SPACE_BETWEEN_TIMELINES;

    const ctx = timelineCanvas.getContext("2d");

    // Clear the background
    ctx.fillStyle = "#FFF";
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    // Activity entries
    activityEntries.forEach((ae) => {
        ctx.fillStyle = ae.color;

        const startX = ((ae.start - timelineStart) / dayDiff) * canvasWidth;
        const stopX = ((ae.stop - timelineStart) / dayDiff) * canvasWidth;
        ctx.fillRect(startX, 0, stopX - startX, canvasHeight);
    });

    // Time row
    ctx.fillStyle = "#595959";
    ctx.fillRect(0, 0, canvasWidth, TIMELINE_HEIGHT);
    ctx.strokeStyle = "#B3B3B3";
    const startOfTimeTimeline = new Date(timelineStart);
    startOfTimeTimeline.setSeconds(0);
    startOfTimeTimeline.setMinutes(0);
    for (let currentTime = startOfTimeTimeline; currentTime < timelineStop; currentTime.setSeconds(currentTime.getSeconds() + 3600)) {
        const lineX = ((currentTime - timelineStart) / dayDiff) * canvasWidth;
        ctx.beginPath();
        ctx.moveTo(lineX, TIMELINE_HEIGHT - 10);
        ctx.lineTo(lineX, TIMELINE_HEIGHT);
        ctx.stroke();
    }

    // Tagged entries
    taggedEntries.forEach((te) => {
        ctx.fillStyle = te.color;

        const startX = ((te.start - timelineStart) / dayDiff) * canvasWidth;
        const stopX = ((te.stop - timelineStart) / dayDiff) * canvasWidth;
        ctx.fillRect(startX, TAGGED_ENTRIES_START_Y, stopX - startX, entriesHeight);
    });

    // Logged entries
    loggedEntries.forEach((le) => {
        ctx.fillStyle = le.color;

        const startX = ((le.start - timelineStart) / dayDiff) * canvasWidth;
        const stopX = ((le.stop - timelineStart) / dayDiff) * canvasWidth;
        ctx.fillRect(startX, loggedEntriesStartY, stopX - startX, entriesHeight);
    });
}
