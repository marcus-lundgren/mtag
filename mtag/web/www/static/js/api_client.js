import { dateToDateString } from "./timeline_utilities.js";

export const fetchEntries = async (date) => {
    const dateString = dateToDateString(date);
    const url = "/entries/" + dateString;
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Response status ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error(error.message);
    }
};

export const fetchCategories = async () => {
    const url = "/categories";
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Response status ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error(error.message);
    }
};

export const fetchCategory = async (id) => {
    // Ensure that we have an actual number to use
    throwIfNotANumber(id);

    const url = "/category/" + id;
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Response status ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error(error.message);
    }
};

export const fetchCategoryStatistics = async (main, sub) => {
    console.log(main, sub);
    const params = new URLSearchParams();
    const mainToUse = main.trim();
    if (mainToUse.length === 0) {
        alert("The given main is empty or whitespace!");
        return;
    }

    params.append("main", mainToUse);

    if (sub) {
        let subToUse = sub.trim();
        if (subToUse.length === 0) {
            alert("The given main is empty or whitespace!");
            return;
        }

        params.append("sub", subToUse);
    }

    const url = "/category/statistics?" + params;
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Response status ${response.status}`);
        }

        return (await response.json()).seconds;
    } catch (error) {
        console.error(error.message);
    }
};

export const fetchUpdateTaggedEntry = async (databaseId, name, url, parentId) => {
    throwIfNotANumber(databaseId);
    if (parentId !== null) {
        throwIfNotANumber(parentId);
    }
    const nameToUse = name.trim();
    throwIfEmptyString(nameToUse);

    try {
        const response = await fetch("/taggedentry/edit", {
            method: "POST",
            body: JSON.stringify({
                id: databaseId,
                name: nameToUse,
                url: url.trim(),
                parentId: parentId
            }),
            header: {
                "Content-type": "application/json; charset=UTF-8"
            }
        });
    } catch (error) {
        console.log(error.message);
    }
}

const throwIfNotANumber = (value) => {
    if (isNaN(+value)) {
        const errorMessage = `The given value '${value}' is not a number!`;
        alert(errorMessage);
        throw new Error(errorMessage);
    }
}

const throwIfEmptyString = (str) => {
    if (str.trim().length === 0) {
        const errorMessage = "The given string is empty or whitespace!";
        alert(errorMessage);
        throw new Error(errorMessage);
    }
}
