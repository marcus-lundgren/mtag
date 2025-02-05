import { renderTimeline, TimelineHelper, getHourAndMinuteAndSecondText, padLeftWithZero } from "./timeline.js";

const canvasContainer = document.getElementById("canvas-container");
const overlayCanvas = document.getElementById('overlay');
const timelineCanvas = document.getElementById('timeline');
const datePicker = document.getElementById("date-picker");

const loggedEntries = [];
const taggedEntries = [];
const activityEntries = [];

const currentTimelineDate = {};
let timelineHelper = new TimelineHelper(canvasContainer, currentTimelineDate);

function callRenderTimeline() {
    renderTimeline(timelineHelper, timelineCanvas, taggedEntries, loggedEntries, activityEntries);
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

const SpecialTypes = Object.freeze({
    "TAGGING": 0,
    "ZOOMING": 1
});
let specialMark = undefined;

function setUpListeners() {
    const ctx = overlayCanvas.getContext("2d");
    new ResizeObserver(() => {
        console.log("Resizing..");
        overlayCanvas.width = canvasContainer.clientWidth;
        overlayCanvas.height = canvasContainer.clientHeight;
        timelineCanvas.width = canvasContainer.clientWidth;
        timelineCanvas.height = canvasContainer.clientHeight;
        timelineHelper.update();
        callRenderTimeline();
    }).observe(canvasContainer);

    overlayCanvas.addEventListener("mousedown", (event) => {
        specialMark = {
            type: event.shiftKey ? SpecialTypes.ZOOMING : SpecialTypes.TAGGING,
            x: event.offsetX,
            color: (event.shiftKey ? "rgba(51, 154, 51, 0.4)" : "rgba(51, 51, 51, 0.4)")
        };
    });

    overlayCanvas.addEventListener("mousemove", (event) => {
        const mouseX = event.offsetX;
        const mouseY = event.offsetY;
        ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
        ctx.strokeStyle = "#444";
        ctx.beginPath();
        ctx.moveTo(mouseX, 0);
        ctx.lineTo(mouseX, overlayCanvas.height);
        ctx.stroke();

        // Tooltip
        const mouseDate = timelineHelper.pixelToDate(mouseX);
        const mouseDateString = getHourAndMinuteAndSecondText(mouseDate);

        ctx.font = "14px Arial";
        ctx.textBaseline = "top";
        const textMeasurement = ctx.measureText(mouseDateString);
        const textWidth = textMeasurement.width;
        const textHeight = textMeasurement.fontBoundingBoxAscent + textMeasurement.fontBoundingBoxDescent;

        const rectangleWidth = textWidth + 5 * 2;
        const rectangleHeight = textHeight + 5 * 2;

        const rectangleX = Math.min(mouseX + 10, overlayCanvas.width - rectangleWidth);
        const rectangleY = Math.min(mouseY + 10, overlayCanvas.height - rectangleHeight);

        const textX = rectangleX + 5;
        const textY = rectangleY + 7;

        ctx.fillStyle = "rgba(75, 75, 175, 0.75)";
        ctx.fillRect(rectangleX, rectangleY, rectangleWidth, rectangleHeight);
        ctx.fillStyle = "yellow";
        ctx.fillText(mouseDateString, textX, textY);

        // Special mark handling
        if (specialMark !== undefined) {
            ctx.fillStyle = specialMark.color;
            ctx.fillRect(specialMark.x, 0, mouseX - specialMark.x, overlayCanvas.height);
        }
    });

    overlayCanvas.addEventListener("mouseup", (event) => {
        if (specialMark === undefined) {
            return;
        }

        switch(specialMark.type) {
        case SpecialTypes.ZOOMING:
            const specialDate = timelineHelper.pixelToDate(specialMark.x);
            const mouseDate = timelineHelper.pixelToDate(event.offsetX);
            timelineHelper.setBoundaries(
                specialDate < mouseDate ? specialDate : mouseDate,
                specialDate < mouseDate ? mouseDate : specialDate,
                callRenderTimeline);
            break;
        case SpecialTypes.TAGGING:
        default:
            alert("FIX ME!");
        }

        specialMark = undefined;
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

    const dateString = dateToDateString(currentTimelineDate.date);
    const url = "/entries/" + dateString;
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Response status ${response.status}`);
        }

        const json = await response.json();
        json.logged_entries.forEach((le) => {
            loggedEntries.push({
                start: new Date(le.start),
                stop: new Date(le.stop),
                title: le.application_window.title,
                color: randomColor()
            });
        });

        json.tagged_entries.forEach((te) => {
            taggedEntries.push({
                start: new Date(te.start),
                stop: new Date(te.stop),
                category: te.category.name,
                url: te.category.url,
                color: randomColor(),
                categoryStr: te.category_str
            })
        });

        json.activity_entries.forEach((ae) => {
            activityEntries.push({
                start: new Date(ae.start),
                stop: new Date(ae.stop),
                color: ae.active ? "#8AD98A" : "#808080"
            })
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
fetchEntries();
