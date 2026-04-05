import { dateToDateString } from "./timeline_utilities.js";

export const fetchEntries = async (date) => {
    const dateString = dateToDateString(date);
    const response = await apiFetch(`/entries/${dateString}`);
    return await parseJsonResponse(response);
};

export const fetchCategories = async () => {
    const response = await apiFetch('/categories');
    return await parseJsonResponse(response);
};

export const fetchCategory = async (id) => {
    throwIfNotANumber(id, 'Category ID');
    const response = await apiFetch(`/category/${id}`);
    return await parseJsonResponse(response);
};

export const fetchCategoryStatistics = async (main, sub) => {
    throwIfEmptyString(main, 'Main category');

    const params = new URLSearchParams({ main: main.trim() });
    if (sub) {
        throwIfEmptyString(sub, 'Sub category');
        params.append('sub', sub.trim());
    }

    const response = await apiFetch(`/category/statistics?${params}`);
    const data = await parseJsonResponse(response);
    return data.seconds;
};

export const fetchUpdateCategory = async (databaseId, name, url, parentId) => {
    throwIfNotANumber(databaseId, 'Database ID');
    if (parentId !== null) {
        throwIfNotANumber(parentId, 'Parent ID');
    }
    throwIfEmptyString(name, 'Category name');

    await apiFetch('/category/edit', {
        method: 'POST',
        body: JSON.stringify({
            id: databaseId,
            name: name.trim(),
            url: url.trim(),
            parentId: parentId
        }),
        headers: { 'Content-type': 'application/json; charset=UTF-8' }
    });
};

export const fetchDeleteTaggedEntry = async (id) => {
    throwIfNotANumber(id, 'Entry ID');
    await apiFetch(`/taggedentry/${id}`, { method: 'DELETE' });
};

export const fetchDeleteCategory = async (id) => {
    throwIfNotANumber(id, 'Category ID');
    await apiFetch(`/category/${id}`, { method: 'DELETE' });
};

const apiFetch = async (url, options = {}) => {
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response;
    } catch (error) {
        console.error('API Error:', error.message);
        throw error;
    }
};

const parseJsonResponse = async (response) => {
    try {
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('JSON Parsing Error:', error.message);
        throw error;
    }
};

const throwIfNotANumber = (value, paramName) => {
    if (isNaN(+value)) {
        const errorMessage = `${paramName} must be a valid number`;
        alert(errorMessage);
        throw new Error(errorMessage);
    }
};

const throwIfEmptyString = (str, paramName) => {
    if (str.trim().length === 0) {
        const errorMessage = `${paramName} cannot be empty or whitespace`;
        alert(errorMessage);
        throw new Error(errorMessage);
    }
};
