import { fetchCategories, fetchCategory } from "./api_client.js";

const mainList = document.getElementById("main-list");
const subList = document.getElementById("sub-list");
const categoryNameInput = document.getElementById("category-name");
const categoryUrlInput = document.getElementById("category-url");

const addSubOption = (sub) => {
    let option = document.createElement("option");
    option.text = sub.name;
    option.value = sub.db_id;
    option.addEventListener("click", async () => {
        const category = await fetchCategory(sub.db_id);
        console.log(category);
        categoryNameInput.value = category.name;
        categoryUrlInput.value = category.url;
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
        for (const sub of subs) {
            addSubOption(sub);
        }
    });
    mainList.add(option);
};

const callFetchCategories = async () => {
    mainList.options.length = 0;
    subList.options.length = 0;

    const json = await fetchCategories();
    for (const categoryTuple of json) {
        addMainOption(categoryTuple.main, categoryTuple.children);
    }
};

callFetchCategories();
