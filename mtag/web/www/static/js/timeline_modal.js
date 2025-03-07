import { getHourAndMinuteAndSecondText, millisecondsToTimeString,
         dateToISOString, secondsToTimeString } from "./timeline_utilities.js";
import { fetchCategories, fetchCategoryStatistics } from "./api_client.js";

const modalCategoriesList = document.getElementById("modal-categories-list");
const modalDateSpan = document.getElementById("modal-date-span");
const modalInput = document.getElementById("modal-input");
const modalSaveButton = document.getElementById("modal-store");
const modalDeleteButton = document.getElementById("modal-delete-button");
const createTaggedEntryModal = document.getElementById("create-tagged-entry-modal");
const editTaggedEntryModal = document.getElementById("edit-tagged-entry-modal");
const enableDeleteButtonCheckbox = document.getElementById("enable-delete-button");
const previouslyTaggedTimeSpan = document.getElementById("previously-tagged-time");

const newTaggedEntryBoundaries = { start: undefined, stop: undefined };
const editTaggedEntryProperties = { id: undefined };

function optionDblClickListener(event) {
    modalInput.value = event.target.text;

    // Fire the input event so that we filter the options again
    modalInput.dispatchEvent(new Event("input"));
}

function addOptionToCategoryList(categoryText) {
    let option = document.createElement("option");
    option.addEventListener("dblclick", optionDblClickListener);
    option.text = categoryText;
    modalCategoriesList.add(option);
}

async function callFetchCategories() {
    modalCategoriesList.options.length = 0;

    const json = await fetchCategories();
    for (const categoryTuple of json) {
        const mainName = categoryTuple.main.name;
        addOptionToCategoryList(mainName);
        for (const c of categoryTuple.children) {
            addOptionToCategoryList(mainName + " >> " + c.name);
        }
    }
}

export const showCreateTaggedEntryDialog = (startDate, stopDate) => {
    modalInput.value = "";
    modalSaveButton.disabled = true;
    callFetchCategories();
    modalDateSpan.innerText =
        getHourAndMinuteAndSecondText(startDate)
        + " - "
        + getHourAndMinuteAndSecondText(stopDate)
        + " (" + millisecondsToTimeString(stopDate - startDate) + ")";
    newTaggedEntryBoundaries.start = dateToISOString(startDate);
    newTaggedEntryBoundaries.stop = dateToISOString(stopDate);
    createTaggedEntryModal.showModal();
};

export const showEditTaggedEntryDialog = (databaseId) => {
    editTaggedEntryProperties.id = databaseId;
    enableDeleteButtonCheckbox.checked = false;
    modalDeleteButton.disabled = true;
    editTaggedEntryModal.showModal();
};

export const setUpModalListeners = (onCreateTaggedEntrySaved, onCreateTaggedEntryCancel, onEditPerformed) => {
    const modalCancelButton = document.getElementById("modal-cancel");
    modalCancelButton.addEventListener("click", (event) => {
        createTaggedEntryModal.close();
    });

    createTaggedEntryModal.addEventListener("close", (event) => {
        onCreateTaggedEntryCancel();
    });

    modalDeleteButton.addEventListener("click", async (event) => {
        // Ensure that we have an actual number to use
        if (isNaN(+editTaggedEntryProperties.id)) {
            alert("The given database id is not a number!");
            return;
        }

        const url = "/taggedentry/" + editTaggedEntryProperties.id;
        try {
            const response = await fetch(url, { method: "DELETE" });
            if (!response.ok) {
                throw new Error(`Response status ${response.status}`);
            }
        } catch (error) {
            console.error(error.message);
        }

        editTaggedEntryModal.close();
        onEditPerformed();
    });

    modalInput.addEventListener("input", async (event) => {
        // Render the previously total tagged time
        const [main, sub] = parseInput(modalInput.value);
        console.log(main, sub);
        if (0 < main.length) {
            const seconds = await fetchCategoryStatistics(main, sub);
            previouslyTaggedTimeSpan.innerText = secondsToTimeString(seconds);
        } else {
            previouslyTaggedTimeSpan.innerText = "-";
        }

        // Filter the list of categories based on the input
        const currentInput = modalInput.value.toLowerCase();
        modalSaveButton.disabled = currentInput.length === 0;
        for (const option of modalCategoriesList.options) {
            option.style.display = option.text.toLowerCase().includes(currentInput) ? "block" : "none";
        }
    });

    modalSaveButton.addEventListener("click", async (event) => {
        const splitInput = modalInput.value.split(">>").map((s) => s.trim());
        if (splitInput.length > 2) {
            alert("Too many '>>' in string");
            return;
        }

        const mainToUse = splitInput[0].trim();
        if (mainToUse.length === 0) {
            alert("Main category is empty");
            return;
        }

        const subToUse = splitInput.length === 1 ? null : splitInput[1].trim();
        if (subToUse !== null && subToUse.length === 0) {
            alert("Sub category is empty");
            return;
        }

        const response = await fetch("/taggedentry/add", {
            method: "POST",
            body: JSON.stringify({
                main: mainToUse,
                sub: subToUse,
                start: newTaggedEntryBoundaries.start,
                stop: newTaggedEntryBoundaries.stop
            }),
            header: {
                "Content-type": "application/json; charset=UTF-8"
            }
        })

        if (!response.ok) {
            alert("Unable to save!");
        } else {
            onCreateTaggedEntrySaved();
        }

        createTaggedEntryModal.close();
    });

    enableDeleteButtonCheckbox.addEventListener("change", (event) => {
        modalDeleteButton.disabled = !enableDeleteButtonCheckbox.checked;
    });
};

const parseInput = (input) => {
    const splitInput = input.split(">>").map((s) => s.trim());
    if (splitInput.length > 2) {
        throw new Error("Too many '>>' in string");
    }

    return [splitInput[0], (splitInput.length === 1 ? "" : splitInput[1])];
};
