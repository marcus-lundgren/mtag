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
