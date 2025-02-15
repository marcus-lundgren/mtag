import { renderTimeline, renderOverlay,
         updateTimelineProperties, updateOverlayProperties,
         timelineProperties, overlayProperties,
         TimelineHelper, TimelineEntry,
         getHourAndMinuteAndSecondText, padLeftWithZero } from "./timeline.js";

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

const SpecialTypes = Object.freeze({
    "TAGGING": 0,
    "ZOOMING": 1
});

function callRenderTimeline() {
    updateTimelineProperties(timelineHelper);
    updateTimelineEntries();
    renderTimeline(timelineHelper);
}

const colors = [
    "#123",
    "#452",
    "#ddd",
    "#815",
    "#518",
    "#FAA",
    "#817",
    "#AFA"
];

function randomColor() {
    return colors[Math.floor(Math.random() * colors.length)];
}

function setCurrentDate(newDate) {
    const startOfDay = newDate;
    newDate.setHours(0);
    currentTimelineDate.start = startOfDay;
    currentTimelineDate.date = new Date(startOfDay);
    currentTimelineDate.stop = new Date(new Date(startOfDay).setHours(23, 59, 59, 999));
    timelineHelper.update();

    datePicker.value = dateToDateString(startOfDay);
    fetchEntries();
}

function addDaysToCurrentDate(daysToAdd) {
    const newDate = new Date(currentTimelineDate.date);
    newDate.setDate(newDate.getDate() + daysToAdd);
    setCurrentDate(newDate);
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
        overlayProperties.specialMark = {
            type: event.shiftKey ? SpecialTypes.ZOOMING : SpecialTypes.TAGGING,
            x: event.offsetX,
            color: (event.shiftKey ? "rgba(51, 154, 51, 0.4)" : "rgba(51, 51, 51, 0.4)")
        };
    });

    overlayCanvas.addEventListener("mousemove", (event) => {
        updateOverlayProperties(event.offsetX, event.offsetY);
        renderOverlay(timelineHelper);
    });

    overlayCanvas.addEventListener("mouseup", (event) => {
        const specialMark = overlayProperties.specialMark;
        if (specialMark === undefined) {
            return;
        }

        switch(specialMark.type) {
        case SpecialTypes.ZOOMING:
            const specialDate = timelineHelper.pixelToDate(specialMark.x);
            const mouseDate = timelineHelper.pixelToDate(event.offsetX);
            timelineHelper.setBoundaries(
                specialDate < mouseDate ? specialDate : mouseDate,
                specialDate < mouseDate ? mouseDate : specialDate);
            updateTimelineEntries();
            updateTimelineProperties(timelineHelper);
            renderTimeline(timelineHelper);
            break;
        case SpecialTypes.TAGGING:
        default:
            alert("FIX ME!");
        }

        overlayProperties.specialMark = undefined;
    });

    overlayCanvas.addEventListener("mouseleave", (event) => {
        ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
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
        updateOverlayProperties(event.offsetX, event.offsetY);
        renderTimeline(timelineHelper);
        renderOverlay(timelineHelper);
    });

    datePicker.addEventListener("change", (event) => {
        let newDate = datePicker.valueAsDate;

        // If NULL, then default to the current date
        if (newDate === null) {
            newDate = new Date();
            newDate.setHours(0, 0, 0, 0);
        }
        setCurrentDate(newDate);
    });

    const dateButtonsSetup = {
        "minus-one-week-button": -7,
        "minus-one-day-button": -1,
        "plus-one-day-button": 1,
        "plus-one-week-button": 7
    };

    Object.keys(dateButtonsSetup).forEach((buttonId) => {
        const button = document.getElementById(buttonId);
        button.addEventListener("click", (event) => {
            addDaysToCurrentDate(dateButtonsSetup[buttonId]);
        });
    });
}

async function fetchEntries() {
    loggedEntries.length = 0;
    taggedEntries.length = 0;
    activityEntries.length = 0;

    timelineLoggedEntries.length = 0;
    timelineTaggedEntries.length = 0;
    timelineActivityEntries.length = 0;

    visibleLoggedEntries.length = 0;
    visibleTaggedEntries.length = 0;
    visibleActivityEntries.length = 0;

    const dateString = dateToDateString(currentTimelineDate.date);
    const url = "/entries/" + dateString;
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Response status ${response.status}`);
        }

        const json = await response.json();
        json.logged_entries.forEach((le) => {
            const parsedLe = {
                start: new Date(le.start),
                stop: new Date(le.stop),
                application: le.application_window.application.name,
                title: le.application_window.title,
                color: randomColor()
            };
            loggedEntries.push(parsedLe);
            timelineLoggedEntries.push(new TimelineEntry(le, parsedLe, timelineHelper, [parsedLe.application, parsedLe.title]));
        });

        json.tagged_entries.forEach((te) => {
            const parsedTe = {
                start: new Date(te.start),
                stop: new Date(te.stop),
                category: te.category.name,
                url: te.category.url,
                color: randomColor(),
                categoryStr: te.category_str
            };
            taggedEntries.push(parsedTe);
            timelineTaggedEntries.push(new TimelineEntry(te, parsedTe, timelineHelper, [parsedTe.categoryStr]));
        });

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
    } catch (error) {
        console.error(error.message);
    }
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
    taggedEntries.forEach((te) => {
        let summary = taggedEntrySummaries[te.categoryStr];
        if (summary === undefined) {
            summary = { url: te.url, durationAsDate: new Date(0) };
            taggedEntrySummaries[te.categoryStr] = summary;
        }

        const entryDuration = (te.stop - te.start) / 1000;
        summary.durationAsDate.setSeconds(summary.durationAsDate.getSeconds() + entryDuration);
    });

    for (let [category, summary] of Object.entries(taggedEntrySummaries)) {
        const row = teTableBody.insertRow();
        const durationCell = row.insertCell();
        durationCell.innerText = summary.durationAsDate.toISOString().split("T")[1].split(".")[0];

        const categoryCell = row.insertCell();
        categoryCell.innerText = category;

        const urlCell = row.insertCell();
        if (summary.url !== undefined) {
            urlCell.innerHTML = `<a href="${summary.url}" target="_blank">${summary.url}</a>`
        } else {
            urlCell.innerText = summary.url;
        }
    };
}

function dateToDateString(date) {
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();

    return year + "-" + padLeftWithZero(month) + "-" + padLeftWithZero(day);
}

setUpListeners();
setCurrentDate(new Date("2025-01-15"));
