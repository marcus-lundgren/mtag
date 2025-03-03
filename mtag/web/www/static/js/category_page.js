import { fetchCategories, fetchCategory } from "./api_client.js";

const mainList = document.getElementById("main-list");
const subList = document.getElementById("sub-list");
const categoryNameInput = document.getElementById("category-name");
const changeNameCheckbox = document.getElementById("change-name-checkbox");
const categoryUrlInput = document.getElementById("category-url");
const changeParentSelect = document.getElementById("change-parent-select");

const updateCategoryDetails = async (categoryId) => {
    const category = await fetchCategory(categoryId);
    categoryNameInput.disabled = true;
    categoryNameInput.value = category.name;
    changeNameCheckbox.checked = false;
    categoryUrlInput.value = category.url;
    changeParentSelect.value = category.parent_id ?? -1;
}

const addSubOption = (sub) => {
    let option = document.createElement("option");
    option.text = sub.name;
    option.value = sub.db_id;
    option.addEventListener("click", async (event) => {
        await updateCategoryDetails(event.target.value);
    });
    subList.add(option);
}

const addMainOption = (main, subs) => {
    let option = document.createElement("option");
    option.text = main.name;
    option.value = main.db_id;
    option.addEventListener("click", () => {
        subList.options.length = 0;

        // TODO - Fix this hack?
        main.name = "[Main]";
        addSubOption(main);

        // Select the main from the subs list
        subList.value = main.db_id;

        // Update the details to show the main's information
        updateCategoryDetails(main.db_id);

        // Add the subs
        for (const sub of subs) {
            addSubOption(sub);
        }
    });
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

    const json = await fetchCategories();
    for (const categoryTuple of json) {
        const main = categoryTuple.main;
        addParentChoiceOption(main.name, main.db_id);
        addMainOption(main, categoryTuple.children);
    }
};

const setupListeners = () => {
    changeNameCheckbox.addEventListener("change", (event) => {
        categoryNameInput.disabled = !changeNameCheckbox.checked;
    });
};

setupListeners();
callFetchCategories();
