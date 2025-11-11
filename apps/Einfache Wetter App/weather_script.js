// API-Key
const API_KEY = ""; 

// Basis-URL der API
const BASE_URL = "https://api.openweathermap.org/data/2.5/weather";

const cityInput = document.getElementById("cityInput");
const searchButton = document.getElementById("searchButton");
const messageEl = document.getElementById("message");
const weatherResultEl = document.getElementById("weatherResult");

const cityNameEl = document.getElementById("cityName");
const weatherIconEl = document.getElementById("weatherIcon");
const temperatureEl = document.getElementById("temperature");
const descriptionEl = document.getElementById("description");
const feelsLikeEl = document.getElementById("feelsLike");
const humidityEl = document.getElementById("humidity");
const windEl = document.getElementById("wind");

// Funktion: Nachricht anzeigen (Fehler/Hinweis)
function showMessage(text, isError = true) {
    messageEl.textContent = text;
    messageEl.style.color = isError ? "#c00" : "#0a0";
}

// Funktion: Wetterdaten holen
async function fetchWeather(city) {
    try {
        showMessage("Lade Daten...", false);
        weatherResultEl.classList.add("hidden");

        const url = `${BASE_URL}?q=${encodeURIComponent(
            city
        )}&appid=${API_KEY}&units=metric&lang=de`;

        const response = await fetch(url);

        if (!response.ok) {
            if (response.status === 404) {
                throw new Error("Stadt nicht gefunden. Bitte prüfe deine Eingabe.");
            } else {
                throw new Error("Fehler beim Abrufen der Wetterdaten.");
            }
        }

        const data = await response.json();
        showMessage(""); // Nachricht zurücksetzen
        renderWeather(data);
    } catch (error) {
        showMessage(error.message, true);
    }
}

// Funktion: Wetterdaten ins UI einfügen
function renderWeather(data) {
    const cityName = `${data.name}, ${data.sys.country}`;
    const temp = Math.round(data.main.temp);
    const feelsLike = Math.round(data.main.feels_like);
    const humidity = data.main.humidity;
    const windSpeed = data.wind.speed;
    const description = data.weather[0].description;
    const iconCode = data.weather[0].icon; // z. B. "04d"

    cityNameEl.textContent = cityName;
    temperatureEl.textContent = `${temp} °C`;
    descriptionEl.textContent = description;
    feelsLikeEl.textContent = `${feelsLike} °C`;
    humidityEl.textContent = `${humidity} %`;
    windEl.textContent = `${windSpeed} m/s`;

    const iconUrl = `https://openweathermap.org/img/wn/${iconCode}@2x.png`;
    weatherIconEl.src = iconUrl;
    weatherIconEl.alt = description;

    weatherResultEl.classList.remove("hidden");
}

// Event: Button-Klick
searchButton.addEventListener("click", () => {
    const city = cityInput.value.trim();
    if (!city) {
        showMessage("Bitte gib eine Stadt ein.");
        return;
    }
    fetchWeather(city);
});

// Event: Enter-Taste im Input
cityInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        searchButton.click();
    }
});
