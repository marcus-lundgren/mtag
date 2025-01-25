import { handleZoom, handleMove, renderTimeline } from "./timeline.js";

const canvasContainer = document.getElementById("canvas-container");
const overlayCanvas = document.getElementById('overlay');
const timelineCanvas = document.getElementById('timeline');
const datePicker = document.getElementById("date-picker");

function callRenderTimeline() {
    renderTimeline(timelineCanvas, currentTimelineDate, taggedEntries, loggedEntries);
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

const loggedEntries = [];
const taggedEntries = [];

const currentTimelineDate = {};

function setCurrentDate(newDate) {
    const startOfDay = newDate;
    currentTimelineDate.start = startOfDay;
    currentTimelineDate.date = new Date(startOfDay);
    currentTimelineDate.stop = new Date(new Date(startOfDay).setHours(23, 59, 59, 999));

    datePicker.valueAsDate = startOfDay;
    fetchEntries();
}

function addDaysToCurrentDate(daysToAdd) {
    console.log("adding", daysToAdd);
    const newDate = new Date(currentTimelineDate.date);
    newDate.setDate(newDate.getDate() + daysToAdd);
    setCurrentDate(newDate);
}

let specialMark = undefined;

function setUpListeners() {
    const ctx = overlayCanvas.getContext("2d");
    new ResizeObserver(() => {
        console.log("Resizing..");
        overlayCanvas.width = canvasContainer.clientWidth;
        overlayCanvas.height = canvasContainer.clientHeight;
        timelineCanvas.width = canvasContainer.clientWidth;
        timelineCanvas.height = canvasContainer.clientHeight;
        callRenderTimeline();
    }).observe(canvasContainer);

    overlayCanvas.addEventListener("mousedown", (event) => {
        specialMark = {
            x: event.offsetX,
            color: "rgba(51, 51, 51, 0.4)"
        };
    });

    overlayCanvas.addEventListener("mousemove", (event) => {
        const mouseX = event.offsetX;
        ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
        ctx.strokeStyle = "#444";
        ctx.beginPath();
        ctx.moveTo(mouseX, 0);
        ctx.lineTo(mouseX, overlayCanvas.height);
        ctx.stroke();

        if (specialMark !== undefined) {
            ctx.fillStyle = specialMark.color;
            ctx.fillRect(specialMark.x, 0, mouseX - specialMark.x, overlayCanvas.height);
        }
    });

    overlayCanvas.addEventListener("mouseup", (event) => {
        if (specialMark !== undefined) {
            specialMark = undefined;
            alert("FIX ME!");
        }
    });

    overlayCanvas.addEventListener("mouseleave", (event) => {
        ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
    });

    overlayCanvas.addEventListener("wheel", (event) => {
        event.preventDefault();
        if (event.deltaY !== 0) {
            handleZoom(event.deltaY < 0, currentTimelineDate, callRenderTimeline);
        } else if (event.deltaX !== 0) {
            handleMove(event.deltaX < 0, currentTimelineDate, callRenderTimeline);
        }
    });

    datePicker.addEventListener("change", (event) => {
        setCurrentDate(datePicker.valueAsDate);
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

    const dateString = currentTimelineDate.date.toISOString().split("T")[0];
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
                color: randomColor()
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
        let summary = taggedEntrySummaries[te.category];
        if (summary === undefined) {
            summary = { url: te.url, durationAsDate: new Date(0) };
            taggedEntrySummaries[te.category] = summary;
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

setUpListeners();
setCurrentDate(new Date("2025-01-15"));
fetchEntries();
