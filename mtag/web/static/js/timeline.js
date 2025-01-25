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

export const renderTimeline = (timelineCanvas, currentTimelineDate, taggedEntries, loggedEntries, activityEntries) => {
    const canvasWidth = timelineCanvas.width;
    const canvasHeight = timelineCanvas.height;
    const timelineStart = currentTimelineDate.start;
    const timelineStop = currentTimelineDate.stop;
    const dayDiff = timelineStop - timelineStart;

    const ctx = timelineCanvas.getContext("2d");
    ctx.fillStyle = "#FFF";
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    activityEntries.forEach((ae) => {
        ctx.fillStyle = ae.color;

        const startX = ((ae.start - timelineStart) / dayDiff) * canvasWidth;
        const stopX = ((ae.stop - timelineStart) / dayDiff) * canvasWidth;
        ctx.fillRect(startX, 0, stopX - startX, canvasHeight);
    });

    taggedEntries.forEach((te) => {
        ctx.fillStyle = te.color;

        const startX = ((te.start - timelineStart) / dayDiff) * canvasWidth;
        const stopX = ((te.stop - timelineStart) / dayDiff) * canvasWidth;
        ctx.fillRect(startX, 0, stopX - startX, 50);
    });

    loggedEntries.forEach((le) => {
        ctx.fillStyle = le.color;

        const startX = ((le.start - timelineStart) / dayDiff) * canvasWidth;
        const stopX = ((le.stop - timelineStart) / dayDiff) * canvasWidth;
        ctx.fillRect(startX, 75, stopX - startX, 125);
    });
}
