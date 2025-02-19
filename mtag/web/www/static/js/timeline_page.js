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

const newTaggedEntryDialog = document.getElementById("new-tagged-entry-modal");
const modalCategoriesList = document.getElementById("modal-categories-list");
const modalDateSpan = document.getElementById("modal-date-span");

const SpecialTypes = Object.freeze({
    "TAGGING": 0,
    "ZOOMING": 1
});

function callRenderTimeline() {
    updateTimelineProperties(timelineHelper);
    updateTimelineEntries();
    renderTimeline(timelineHelper);
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

        const specialDate = timelineHelper.pixelToDate(specialMark.x);
        const mouseDate = timelineHelper.pixelToDate(event.offsetX);

        const startDate = specialDate < mouseDate ? specialDate : mouseDate;
        const stopDate = specialDate < mouseDate ? mouseDate : specialDate;

        switch(specialMark.type) {
        case SpecialTypes.ZOOMING:
            const specialDate = timelineHelper.pixelToDate(specialMark.x);
            const mouseDate = timelineHelper.pixelToDate(event.offsetX);
            timelineHelper.setBoundaries(startDate, stopDate);
            updateTimelineEntries();
            updateTimelineProperties(timelineHelper);
            renderTimeline(timelineHelper);
            break;
        case SpecialTypes.TAGGING:
            fetchCategories();
            modalDateSpan.innerText =
                getHourAndMinuteAndSecondText(startDate)
                + " - "
                + getHourAndMinuteAndSecondText(stopDate)
                + " (" + millisecondsToTimeString(stopDate - startDate) + ")";
            newTaggedEntryDialog.style.display = "block";
            break;
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

    const modalCancelButton = document.getElementById("modal-cancel");
    modalCancelButton.addEventListener("click", (event) => {
        newTaggedEntryDialog.style.display = "none";
    });
}

function addOptionToCategoryList(categoryText) {
    let option = document.createElement("option");
    option.text = categoryText;
    modalCategoriesList.add(option);
}

async function fetchCategories() {
    modalCategoriesList.options.length = 0;

    const url = "/categories";
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Response status ${response.status}`);
        }

        const json = await response.json();

        for (const categoryTuple of json) {
            const mainName = categoryTuple.main.name;
            addOptionToCategoryList(mainName);
            for (const c of categoryTuple.children) {
                addOptionToCategoryList(mainName + " >> " + c.name);
            }
        }
    } catch (error) {
        console.error(error.message);
    }
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
        for (const le of json.logged_entries) {
            const parsedLe = {
                start: new Date(le.start),
                stop: new Date(le.stop),
                application: le.application_window.application.name,
                title: le.application_window.title,
                color: await stringToColor(le.application_window.application.name)
            };
            loggedEntries.push(parsedLe);
            timelineLoggedEntries.push(new TimelineEntry(le, parsedLe, timelineHelper, [parsedLe.application, parsedLe.title]));
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
            timelineTaggedEntries.push(new TimelineEntry(te, parsedTe, timelineHelper, [parsedTe.categoryStr]));
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

function dateToDateString(date) {
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();

    return year + "-" + padLeftWithZero(month) + "-" + padLeftWithZero(day);
}

function millisecondsToTimeString(ms) {
    const msInSeconds = ms / 1000;
    const hours = Math.floor(msInSeconds / 3600);
    const minutes = Math.floor((msInSeconds - hours * 3600) / 60);
    const seconds = Math.floor(msInSeconds % 60);
    return padLeftWithZero(hours) + ":" + padLeftWithZero(minutes) + ":" + padLeftWithZero(seconds);
}

async function stringToColor(str) {
    const utf8 = new TextEncoder().encode(str);
    const hashBuffer = await crypto.subtle.digest('SHA-256', utf8);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray
          .map((bytes) => bytes.toString(16).padStart(2, '0'))
          .join('');
    return "#" + hashHex.substring(0, 6);
}

setUpListeners();
setCurrentDate(new Date("2025-01-15"));
