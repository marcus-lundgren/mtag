import { fetchCategories, fetchCategory,
         fetchUpdateTaggedEntry } from "./api_client.js";
import { secondsToTimeString } from "./timeline_utilities.js";

const mainList = document.getElementById("main-list");
const subList = document.getElementById("sub-list");
const categoryNameInput = document.getElementById("category-name");
const changeNameCheckbox = document.getElementById("change-name-checkbox");
const categoryUrlInput = document.getElementById("category-url");
const changeParentSelect = document.getElementById("change-parent-select");
const taggedTime = document.getElementById("tagged-time");
const saveCategoryButton = document.getElementById("save-button");

let categoryTuples = undefined;

const updateCategoryDetails = async (categoryId) => {
    const category = await fetchCategory(categoryId);
    categoryNameInput.disabled = true;
    categoryNameInput.value = category.name;
    changeNameCheckbox.checked = false;
    categoryUrlInput.value = category.url;
    changeParentSelect.value = category.parent_id ?? -1;
    changeParentSelect.disabled = category.has_subs;
    taggedTime.innerText = secondsToTimeString(category.seconds);
}

const addSubOption = (name, databaseId) => {
    let option = document.createElement("option");
    option.text = name;
    option.value = databaseId;
    subList.add(option);
}

const addMainOption = (main) => {
    let option = document.createElement("option");
    option.text = main.name;
    option.value = main.db_id;
    mainList.add(option);
};

const addParentChoiceOption = (name, categoryId) => {
    let option = document.createElement("option");
    option.text = name;
    option.value = categoryId;
    changeParentSelect.add(option);
}

const callFetchCategories = async () => {
    mainList.options.length = 0;
    subList.options.length = 0;
    changeParentSelect.options.length = 0;

    // Add an "empty" option
    addParentChoiceOption("", -1);

    categoryTuples = await fetchCategories();
    let isFirstMain = true;
    for (const categoryTuple of categoryTuples) {
        const main = categoryTuple.main;
        addParentChoiceOption(main.name, main.db_id);
        addMainOption(main);

        if (isFirstMain) {
            isFirstMain = false;
            mainList.value = main.db_id;
            mainList.dispatchEvent(new Event("change"));
        }
    }
};

const setupListeners = () => {
    mainList.addEventListener("change", (event) => {
        const mainDatabaseId = +mainList.value;
        let tuple = undefined;
        for (const t of categoryTuples) {
            if (t.main.db_id === mainDatabaseId) {
                tuple = t;
                break;
            }
        }

        if (tuple === undefined) {
            throw new Error(`Unable to find chosen main with id = ${mainDatabaseId}`);
        }

        subList.options.length = 0;

        // Add the main as a sub option
        addSubOption("[Main]", mainDatabaseId);

        // Select the main from the subs list
        subList.value = mainDatabaseId;

        // Update the details to show the main's information
        updateCategoryDetails(mainDatabaseId);

        // Add the subs
        for (const sub of tuple.children) {
            addSubOption(sub.name, sub.db_id);
        }
    });

    subList.addEventListener("change", (event) => {
        const databaseId = +subList.value;
        updateCategoryDetails(databaseId);
    });

    changeNameCheckbox.addEventListener("change", (event) => {
        categoryNameInput.disabled = !changeNameCheckbox.checked;
    });

    saveCategoryButton.addEventListener("click", async (event) => {
        const databaseId = subList.value;
        const name = categoryNameInput.value;
        const url = categoryUrlInput.value;
        let parentId = changeParentSelect.value;

        // No parent selected. Set the id to NULL
        if (parentId === "-1") {
            parentId = null;
        }

        await fetchUpdateTaggedEntry(databaseId, name, url, parentId);
        window.location.reload();
    });

    categoryNameInput.addEventListener("input", (event) => {
        const value = event.target.value.trim();
        saveCategoryButton.disabled = value.length === 0;
    });
};

setupListeners();
callFetchCategories();
