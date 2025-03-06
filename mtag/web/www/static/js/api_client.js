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
    if (isNaN(+id)) {
        alert("The given database id is not a number!");
        return;
    }

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
