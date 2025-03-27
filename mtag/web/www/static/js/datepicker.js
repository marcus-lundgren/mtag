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

function getWeekdayOffset(chosenDate) {
    const worseIndex = new Date(chosenDate.getFullYear(), chosenDate.getMonth(), 1).getDay();
    return worseIndex === 0 ? 6 : worseIndex - 1;
}

function getNumberOfDaysInMonth(chosenDate) {
    return new Date(chosenDate.getFullYear(), chosenDate.getMonth() + 1, 0).getDate();
}

export const renderDatepicker = () => {
    console.log("Rendering: ", chosenDate);
    chosenYearSpan.innerText = chosenDate.getFullYear();
    chosenMonthSpan.innerText = chosenDate.toLocaleString("en-us", { month: "long" });
    const firstDayOffset = getWeekdayOffset(chosenDate);
    const numberOfDaysInMonth = getNumberOfDaysInMonth(chosenDate);

    for (const square of daySquares) {
        square.innerText = "";
        square.disabled = true;
        square.classList.remove("selectable");
        square.classList.remove("selected");
    }

    const chosenDay = chosenDate.getDate();
    for (let i = 0; i < numberOfDaysInMonth; ++i) {
        const day = i + 1;
        const daySquareIndex = i + firstDayOffset;
        const normalizedIndex = i === 0 ? 0 : i - (7 - firstDayOffset) + 7;

        if (normalizedIndex % 7 === 0) {
            const weekNum = weekNumSquares[normalizedIndex / 7];
            weekNum.innerText = 1 + (normalizedIndex / 7);
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
