import { renderTimeline, renderOverlay, updateTimelineProperties, updateOverlayProperties,
         timelineProperties, overlayProperties, TimelineHelper, TimelineEntry } from "./timeline.js";
import { dateToDateString, stringToColor, millisecondsToTimeString,
         getIntervalString } from "./timeline_utilities.js";
import { updateMinimapProperties, renderMinimap, setUpMinimapListeners } from "./timeline_minimap.js";
import { fetchEntries } from "./api_client.js";
import { showCreateTaggedEntryDialog, setUpModalListeners,
         showEditTaggedEntryDialog } from "./timeline_modal.js";

const canvasContainer = document.getElementById("canvas-container");
const overlayCanvas = document.getElementById('overlay');
const timelineCanvas = document.getElementById('timeline');
const datePicker = document.getElementById("date-picker");

timelineProperties.canvas = timelineCanvas;
overlayProperties.canvas = overlayCanvas;

const loggedEntries = [];
const taggedEntries = [];
const activityEntries = [];

const timelineLoggedEntries = timelineProperties.timelineLoggedEntries;
const timelineTaggedEntries = timelineProperties.timelineTaggedEntries;
const timelineActivityEntries = timelineProperties.timelineActivityEntries;

const visibleLoggedEntries = timelineProperties.visibleLoggedEntries;
const visibleTaggedEntries = timelineProperties.visibleTaggedEntries;
const visibleActivityEntries = timelineProperties.visibleActivityEntries;

const currentTimelineDate = {};
const timelineHelper = new TimelineHelper(canvasContainer, currentTimelineDate);

let newTaggedEntryBoundaries = { start: undefined, stop: undefined };

const SpecialTypes = Object.freeze({
    "TAGGING": 0,
    "ZOOMING": 1
});

function callRenderTimeline() {
    updateTimelineProperties(timelineHelper);
    updateTimelineEntries();
    renderTimeline(timelineHelper);
    renderMinimap();
}

async function setCurrentDate(newDate) {
    const startOfDay = newDate;
    newDate.setHours(0, 0, 0, 0);
    currentTimelineDate.startOfDate = new Date(startOfDay);
    currentTimelineDate.endOfDate = new Date(startOfDay);
    currentTimelineDate.endOfDate.setHours(23, 59, 59, 0);
    currentTimelineDate.start = new Date(startOfDay);
    currentTimelineDate.date = new Date(startOfDay);
    currentTimelineDate.stop = new Date(currentTimelineDate.endOfDate);
    timelineHelper.update();

    datePicker.value = dateToDateString(startOfDay);
    updateMinimapProperties(currentTimelineDate);
    await callFetchEntries();
}

async function addDaysToCurrentDate(daysToAdd) {
    const newDate = new Date(currentTimelineDate.date);
    newDate.setDate(newDate.getDate() + daysToAdd);
    await setCurrentDate(newDate);
}

function updateTimelineEntries() {
    function updateEntries(timelineEntries, visibleEntries) {
        visibleEntries.length = 0;
        let lastStopX = undefined;
        timelineEntries.forEach((e) => {
            e.update(timelineHelper);

            if (e.getStop() < currentTimelineDate.start || currentTimelineDate.stop < e.getStart()) {
                return;
            }

            if (e.getStopX() !== lastStopX) {
                lastStopX = e.getStopX();
                visibleEntries.push(e);
            }
        });
    }

    updateEntries(timelineLoggedEntries, visibleLoggedEntries);
    updateEntries(timelineTaggedEntries, visibleTaggedEntries);
    updateEntries(timelineActivityEntries, visibleActivityEntries);
}

function setUpListeners() {
    const ctx = overlayCanvas.getContext("2d");
    new ResizeObserver(() => {
        console.log("Resizing..");
        overlayCanvas.width = canvasContainer.clientWidth;
        overlayCanvas.height = canvasContainer.clientHeight;
        timelineCanvas.width = canvasContainer.clientWidth;
        timelineCanvas.height = canvasContainer.clientHeight;
        timelineHelper.update();
        updateTimelineEntries();
        updateTimelineProperties(timelineHelper);
        renderTimeline(timelineHelper);
    }).observe(canvasContainer);

    overlayCanvas.addEventListener("mousedown", (event) => {
        // Only handle primary button presses
        if (event.buttons !== 1) {
            return;
        }

        const isZooming = event.shiftKey;
        overlayProperties.keptTaggingStateForDblClick = undefined;

        if (isZooming) {
            overlayProperties.zoomState = {
                initialX: event.offsetX
            };
        } else {
            const taggingMouseDate = overlayProperties.taggingMouseDate;
            let boundaryStart = currentTimelineDate.start;
            let boundaryStop = currentTimelineDate.stop;
            for (const taggedEntry of timelineProperties.timelineTaggedEntries) {
                // The entry is to the right of the mouse. Use its start date
                // as the boundary stop and stop iterating.
                if (taggingMouseDate <= taggedEntry.getStart()) {
                    boundaryStop = taggedEntry.getStart();
                    break;
                }

                // The entry is to the left of the mouse. Use its stop date
                // as the start of the boundary.
                if (taggedEntry.getStop() <= taggingMouseDate) {
                    boundaryStart = taggedEntry.getStop();
                }
            }

            overlayProperties.taggingState = {
                initialDate: taggingMouseDate,
                boundaryStart: boundaryStart,
                boundaryStop: boundaryStop,
                start: taggingMouseDate,
                stop: taggingMouseDate
            };
        }
    });

    overlayCanvas.addEventListener("contextmenu", (event) => {
        event.preventDefault();
        if (overlayProperties.hoveredEntry !== undefined && overlayProperties.hoveredEntryIsTaggedEntry) {
            showEditTaggedEntryDialog(overlayProperties.hoveredEntry.entry.getDatabaseId());
        }
    });

    overlayCanvas.addEventListener("mousemove", (event) => {
        updateOverlayProperties(event.offsetX, event.offsetY, timelineHelper);
        renderOverlay(timelineHelper);
    });

    overlayCanvas.addEventListener("mouseup", (event) => {
        if (overlayProperties.zoomState !== undefined) {
            const zoomState = overlayProperties.zoomState;
            const mouseDate = timelineHelper.pixelToDate(event.offsetX);
            const initialDate = timelineHelper.pixelToDate(zoomState.initialX);

            const startDate = initialDate < mouseDate ? initialDate : mouseDate;
            const stopDate = initialDate < mouseDate ? mouseDate : initialDate;

            timelineHelper.setBoundaries(startDate, stopDate);
            updateTimelineEntries();
            updateTimelineProperties(timelineHelper);
            renderTimeline(timelineHelper);
            overlayProperties.zoomState = undefined;
        } else if (overlayProperties.taggingState !== undefined) {
            const taggingState = overlayProperties.taggingState;

            const startDate = taggingState.start;
            const stopDate = taggingState.stop;

            // The start and stop is the same. Keep its state so that we can use it
            // if a double click event happens.
            if (startDate === stopDate) {
                taggingState.start = taggingState.boundaryStart;
                taggingState.stop = taggingState.boundaryStop;
                overlayProperties.keptTaggingStateForDblClick = taggingState;
                overlayProperties.taggingState = undefined;
            } else {
                showCreateTaggedEntryDialog(startDate, stopDate);
            }
        }
    });

    overlayCanvas.addEventListener("mouseleave", (event) => {
        if (overlayProperties.taggingState !== undefined) {
            return;
        }

        ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
    });

    overlayCanvas.addEventListener("dblclick", (event) => {
        const taggingState = overlayProperties.keptTaggingStateForDblClick;
        if (taggingState === undefined) {
            return;
        }

        overlayProperties.taggingState = overlayProperties.keptTaggingStateForDblClick;
        renderOverlay(timelineHelper);

        const startDate = taggingState.start;
        const stopDate = taggingState.stop;
        showCreateTaggedEntryDialog(startDate, stopDate);
    });

    overlayCanvas.addEventListener("wheel", (event) => {
        event.preventDefault();
        if (event.deltaY !== 0) {
            const mouseDate = timelineHelper.pixelToDate(event.offsetX);
            timelineHelper.zoom(event.deltaY < 0, mouseDate, callRenderTimeline);
        } else if (event.deltaX !== 0) {
            timelineHelper.move(event.deltaX < 0, callRenderTimeline);
        }

        updateTimelineEntries();
        updateOverlayProperties(event.offsetX, event.offsetY, timelineHelper);
        renderTimeline(timelineHelper);
        renderOverlay(timelineHelper);
    });

    datePicker.addEventListener("change", async (event) => {
        let newDate = datePicker.valueAsDate;

        // If NULL, then default to the current date
        if (newDate === null) {
            newDate = new Date();
            newDate.setHours(0, 0, 0, 0);
        }
        await setCurrentDate(newDate);
    });

    const dateButtonsSetup = {
        "minus-one-week-button": -7,
        "minus-one-day-button": -1,
        "plus-one-day-button": 1,
        "plus-one-week-button": 7
    };

    Object.keys(dateButtonsSetup).forEach((buttonId) => {
        const button = document.getElementById(buttonId);
        button.addEventListener("click", async (event) => {
            await addDaysToCurrentDate(dateButtonsSetup[buttonId]);
        });
    });

    const zoomToFitButton = document.getElementById("zoom-to-fit");
    zoomToFitButton.addEventListener("click", (event) => {
        let newStart = undefined;
        let newStop = undefined;

        const updateBoundariesIfElementExists = (entries) => {
            if (entries.length === 0) {
                return;
            }

            let firstEntry = entries[0];
            let lastEntry = entries[entries.length -1];

            if (newStart === undefined || firstEntry.start < newStart) {
                newStart = firstEntry.start;
            }

            if (newStop === undefined || newStop < lastEntry.stop) {
                newStop = lastEntry.stop;
            }
        }

        updateBoundariesIfElementExists(timelineProperties.timelineTaggedEntries);
        updateBoundariesIfElementExists(timelineProperties.timelineLoggedEntries);

        newStart = newStart ?? currentTimelineDate.startOfDate;
        newStop = newStop ?? currentTimelineDate.endOfDate;

        timelineHelper.setBoundaries(newStart, newStop);
        callRenderTimeline();
    });

    setUpMinimapListeners((mouseDate) => {
        const newStart = new Date(mouseDate.getTime() - timelineHelper.getCurrentBoundaryDeltaInTime() / 2);
        const newStop = new Date(mouseDate.getTime() + timelineHelper.getCurrentBoundaryDeltaInTime() / 2);
        timelineHelper.setBoundaries(newStart, newStop);
        callRenderTimeline();
    });

    setUpModalListeners(
        async () => {
            await callFetchEntries();
            overlayProperties.taggingState = undefined;
            overlayProperties.keptTaggingStateForDblClick = undefined;
            overlayCanvas.dispatchEvent(new Event("mouseleave"));
        },
        () => {
            overlayProperties.taggingState = undefined;
            overlayProperties.keptTaggingStateForDblClick = undefined;
            overlayCanvas.dispatchEvent(new Event("mouseleave"));
        },
        async () => {
            await callFetchEntries();
        });
}

async function callFetchEntries() {
    const json = await fetchEntries(currentTimelineDate.date);

    loggedEntries.length = 0;
    taggedEntries.length = 0;
    activityEntries.length = 0;

    timelineLoggedEntries.length = 0;
    timelineTaggedEntries.length = 0;
    timelineActivityEntries.length = 0;

    visibleLoggedEntries.length = 0;
    visibleTaggedEntries.length = 0;
    visibleActivityEntries.length = 0;

    for (const le of json.logged_entries) {
        const parsedLe = {
            start: new Date(le.start),
            stop: new Date(le.stop),
            application: le.application_window.application.name,
            title: le.application_window.title,
            color: await stringToColor(le.application_window.application.name)
        };
        loggedEntries.push(parsedLe);
        timelineLoggedEntries.push(
            new TimelineEntry(le, parsedLe, timelineHelper,
                              [getIntervalString(parsedLe.start, parsedLe.stop), parsedLe.application, parsedLe.title]));
    };

    for (const te of json.tagged_entries) {
        const parsedTe = {
            start: new Date(te.start),
            stop: new Date(te.stop),
            category: te.category.name,
            url: te.category.url,
            color: await stringToColor(te.category_str),
            categoryStr: te.category_str
        };
        taggedEntries.push(parsedTe);
        timelineTaggedEntries.push(new TimelineEntry(te, parsedTe, timelineHelper,
                                                     [getIntervalString(parsedTe.start, parsedTe.stop), parsedTe.categoryStr]));
    };

    json.activity_entries.forEach((ae) => {
        const parsedAe = {
            start: new Date(ae.start),
            stop: new Date(ae.stop),
            color: ae.active ? "#8AD98A" : "#808080"
        };
        activityEntries.push(parsedAe);
        timelineActivityEntries.push(new TimelineEntry(ae, parsedAe, timelineHelper, [(ae.active ? "## Active ##" : "## Inactive ##")]));
    });

    callRenderTimeline();
    updateTables();
}

function updateTables() {
    const leTable = document.getElementById("logged-entries-table");
    const leTableBody = leTable.getElementsByTagName("tbody")[0];

    const teTable = document.getElementById("tagged-entries-table");
    const teTableBody = teTable.getElementsByTagName("tbody")[0];

    // Remove all existing rows
    leTableBody.innerHTML = "";
    teTableBody.innerHTML = "";

    // Add the entries
    loggedEntries.forEach((le) => {
        const row = leTableBody.insertRow();
        const startCell = row.insertCell();
        startCell.innerText = le.start.toISOString();

        const stopCell = row.insertCell();
        stopCell.innerText = le.stop.toISOString();

        const applicationCell = row.insertCell();
        applicationCell.innerText = le.application;

        const titleCell = row.insertCell();
        titleCell.innerText = le.title;
    });

    const taggedEntrySummaries = {};
    let totalTaggedTimeInMilliseconds = 0;
    taggedEntries.forEach((te) => {
        let summary = taggedEntrySummaries[te.categoryStr];
        if (summary === undefined) {
            summary = { url: te.url, durationInMilliseconds: 0 };
            taggedEntrySummaries[te.categoryStr] = summary;
        }

        const entryDuration = te.stop - te.start;
        totalTaggedTimeInMilliseconds += entryDuration;
        summary.durationInMilliseconds += entryDuration;
    });

    for (let [category, summary] of Object.entries(taggedEntrySummaries)) {
        const row = teTableBody.insertRow();
        const durationCell = row.insertCell();
        durationCell.innerText = millisecondsToTimeString(summary.durationInMilliseconds);

        const categoryCell = row.insertCell();
        categoryCell.innerText = category;

        const urlCell = row.insertCell();
        let url = summary.url;
        if (url !== undefined) {
            // TODO - Do this server side instead?
            url = url.replace("{{date}}", dateToDateString(currentTimelineDate.date));
            urlCell.innerHTML = `<a href="${url}" target="_blank">${url}</a>`
        }
    };

    const totalTaggedTimeSpan = document.getElementById("total-tagged-time");
    totalTaggedTimeSpan.innerText = millisecondsToTimeString(totalTaggedTimeInMilliseconds);
}

setUpListeners();
setCurrentDate(new Date("2025-01-15"));
