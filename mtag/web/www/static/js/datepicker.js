const calendar = document.getElementById("calendar");
const chosenYearSpan = document.getElementById("chosen-year");
const chosenMonthSpan = document.getElementById("chosen-month");
const minusMonthButton = document.getElementById("minus-month");
const plusMonthButton = document.getElementById("plus-month");

const daySquares = [];
const weekNumSquares = [];

let chosenDate = new Date(2025, 2, 25);
let chosenDateHasBeenUpdated = undefined;

export const initDatepicker = (newDate, newDateChosenFunction) => {
    chosenDate = newDate;

    chosenDateHasBeenUpdated = () => {
        renderDatepicker();
        newDateChosenFunction(new Date(chosenDate));
    };

    function createSquare(squareClass) {
        const square = document.createElement("span");
        square.classList.add(squareClass);
        calendar.appendChild(square);
        return square;
    }

    function createWeekNumSquare() {
        const square = createSquare("week-num");
        weekNumSquares.push(square);
    }

    function createDaySquare() {
        const square = createSquare("day");
        square.addEventListener("click", (event) => {
            if (square.innerText === "") {
                return;
            }

            chosenDate.setDate(parseInt(square.innerText));
            chosenDateHasBeenUpdated();
        });
        daySquares.push(square);
    }

    function createAndAddLine() {
        createWeekNumSquare();
        for (let i = 0; i < 7; ++i) {
            createDaySquare();
        }
    }

    for (let i = 0; i < 6; ++i) {
        createAndAddLine();
    }

    minusMonthButton.addEventListener("click", (event) => {
        chosenDate.setMonth(chosenDate.getMonth() - 1, 1);
        chosenDateHasBeenUpdated();
    });

    plusMonthButton.addEventListener("click", (event) => {
        chosenDate.setMonth(chosenDate.getMonth() + 1, 1);
        chosenDateHasBeenUpdated();
    });

    const todayButton = document.getElementById("today-button");
    todayButton.addEventListener("click", (event) => {
        chosenDate = new Date();
        chosenDateHasBeenUpdated();
    });

    chosenDateHasBeenUpdated();
};

export const addDaysToCurrentDate = (daysToAdd) => {
    chosenDate.setDate(chosenDate.getDate() + daysToAdd);
    chosenDateHasBeenUpdated();
};

function getMondayOfDatesWeek(date) {
    let mondayOfDateWeek = new Date(date);
    const weekdayOfDate = date.getDay();
    if (weekdayOfDate !== 1) {
        const daysToSubtract = weekdayOfDate !== 0 ? weekdayOfDate - 1 : 6;
        mondayOfDateWeek.setDate(mondayOfDateWeek.getDate() - daysToSubtract);
    }

    return mondayOfDateWeek;
}

export const getWeekNum = (chosenDate) => {
    const januaryForth = new Date(chosenDate.getFullYear(), 0, 4);
    const mondayOfJanuaryForthWeek = getMondayOfDatesWeek(januaryForth);
    const mondayOfChosenDateWeek = getMondayOfDatesWeek(chosenDate);
    const weekNum = 1 + Math.round((mondayOfChosenDateWeek - mondayOfJanuaryForthWeek) / (1000 * 60 * 60 * 24 * 7));

    // We've calculated that we are on the week before week one.
    // Calculate the week of the last day of the previous year.
    if (weekNum < 1) {
        const lastDateOfPreviousYear = new Date(chosenDate.getFullYear() - 1, 11, 31);
        return getWeekNum(lastDateOfPreviousYear);
    }

    // No special case needs to be made if aren't on week 53
    if (weekNum < 53) {
        return weekNum;
    }

    // We need to determine if we actually are on week 53 or if we are on week 1.
    const lastDateOfDecember = new Date(chosenDate.getFullYear(), 11, 31);
    const lastDateOfDecemberDay = lastDateOfDecember.getDay();
    const lastWeekContainsNextJanuaryForth = lastDateOfDecemberDay !== 0 && lastDateOfDecemberDay < 4;
    return lastWeekContainsNextJanuaryForth ? 1 : weekNum;
}

function getFirstDateOfMonth(chosenDate) {
    return new Date(chosenDate.getFullYear(), chosenDate.getMonth(), 1);
}

function getWeekdayOffset(date) {
    const worseIndex = date.getDay();
    return worseIndex === 0 ? 6 : worseIndex - 1;
}

function getNumberOfDaysInMonth(chosenDate) {
    return new Date(chosenDate.getFullYear(), chosenDate.getMonth() + 1, 0).getDate();
}

export const renderDatepicker = () => {
    console.log("Rendering: ", chosenDate);
    chosenYearSpan.innerText = chosenDate.getFullYear();
    chosenMonthSpan.innerText = chosenDate.toLocaleString("en-us", { month: "long" });
    const firstDateOfMonth = getFirstDateOfMonth(chosenDate);
    const firstWeekNum = getWeekNum(firstDateOfMonth);
    const firstDayOffset = getWeekdayOffset(firstDateOfMonth);
    const numberOfDaysInMonth = getNumberOfDaysInMonth(chosenDate);

    for (const square of daySquares) {
        square.innerText = "";
        square.disabled = true;
        square.classList.remove("selectable");
        square.classList.remove("selected");
    }

    for (const weekSquare of weekNumSquares) {
        weekSquare.innerText = "";
    }

    const chosenDay = chosenDate.getDate();
    for (let i = 0; i < numberOfDaysInMonth; ++i) {
        const day = i + 1;
        const daySquareIndex = i + firstDayOffset;
        const normalizedIndex = i === 0 ? 0 : i - (7 - firstDayOffset) + 7;

        if (normalizedIndex % 7 === 0) {
            const weekNumIndex = normalizedIndex / 7;
            const weekNumSquare = weekNumSquares[weekNumIndex];

            let currentWeekNum = firstWeekNum + weekNumIndex;

            // Ensure that we actually are on weeks above 52
            if (currentWeekNum > 52) {
                const currentMonday = new Date(firstDateOfMonth);
                currentMonday.setDate(currentMonday.getDate() + weekNumIndex * 7);
                currentWeekNum = getWeekNum(currentMonday);
            }

            weekNumSquare.innerText = currentWeekNum;
        }

        const daySquare = daySquares[daySquareIndex];
        daySquare.classList.add("selectable");
        daySquare.disabled = false;
        daySquare.innerText = day;

        if (day === chosenDay) {
            daySquare.classList.add("selected");
        }
    }
};
