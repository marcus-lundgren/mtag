export const padLeftWithZero = (n) => {
    return n.toString().padStart(2, "0");
}

export const getHourAndMinuteAndSecondText = (date) => {
    const hourString = padLeftWithZero(date.getHours());
    const minuteString = padLeftWithZero(date.getMinutes());
    const secondString = padLeftWithZero(date.getSeconds());

    return `${hourString}:${minuteString}:${secondString}`;
}

export const getHourAndMinuteText = (date) => {
    const hourString = padLeftWithZero(date.getHours());
    const minuteString = padLeftWithZero(date.getMinutes());

    return `${hourString}:${minuteString}`;
}

export const dateToDateString = (date) => {
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();

    return year + "-" + padLeftWithZero(month) + "-" + padLeftWithZero(day);
}

export const millisecondsToTimeString = (ms) => {
    const msInSeconds = ms / 1000;
    const hours = Math.floor(msInSeconds / 3600);
    const minutes = Math.floor((msInSeconds - hours * 3600) / 60);
    const seconds = Math.floor(msInSeconds % 60);
    return padLeftWithZero(hours) + ":" + padLeftWithZero(minutes) + ":" + padLeftWithZero(seconds);
}

export const dateToISOString = (date) => {
    const seconds = padLeftWithZero(date.getSeconds());
    const minutes = padLeftWithZero(date.getMinutes());
    const hours = padLeftWithZero(date.getHours());
    return `${dateToDateString(date)}T${getHourAndMinuteAndSecondText(date)}`;
}

export const stringToColor = async (str) => {
    const utf8 = new TextEncoder().encode(str);
    const hashBuffer = await crypto.subtle.digest('SHA-256', utf8);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray
          .map((bytes) => bytes.toString(16).padStart(2, '0'))
          .join('');
    return "#" + hashHex.substring(0, 6);
}
