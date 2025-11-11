# 🌤️ Wetter App (HTML, CSS, JavaScript)

Eine moderne, minimalistische Wetter-App, die aktuelle Wetterdaten für jede Stadt weltweit anzeigt – erstellt mit HTML, CSS und JavaScript.

## 🧰 Technologien
- HTML5  
- CSS3 (Flexbox, Responsive Design)  
- JavaScript (ES6)  
- OpenWeatherMap API  
- VS Code  
- (optional) Live Server Extension zum Testen im Browser

## 🚀 Funktionen

### 🔎 Wetterabfrage
- Stadtname eingeben (z. B. *Berlin*, *Hamburg*, *Rom*)  
- Klick auf **„Wetter anzeigen“** ruft aktuelle Daten über die OpenWeatherMap-API ab  
- Anzeige von:
  - 🌍 Stadtname & Land  
  - 🌡️ Temperatur (in °C)  
  - 🌥️ Wetterbeschreibung (z. B. „leichter Regen“)  
  - 💨 Windgeschwindigkeit  
  - 💧 Luftfeuchtigkeit  
  - 🌡️ „Gefühlt wie“-Temperatur  
  - ☁️ passendes Wetter-Icon  

### 💬 Fehlerbehandlung
- Meldung bei ungültiger oder leerer Eingabe  
- Hinweis, falls Stadt nicht gefunden oder API-Schlüssel fehlerhaft ist  
- Lade-Hinweis während der Datenabfrage  

### 🖼️ Benutzeroberfläche
- Klare, zentrierte Struktur  
- Abgerundete Kanten, Schatten & Farbverlauf-Hintergrund  
- Responsive Design für Desktop & Smartphone  
- Animierter Button-Hover-Effekt  

### 🧩 API-Integration
- Daten von der **OpenWeatherMap Current Weather API**  
- JSON-Parsing & dynamische Anzeige mit JavaScript  
- Parameter:
  - `q` → Stadtname  
  - `units=metric` → metrisches System (°C)  
  - `lang=de` → deutsche Beschreibung  
  - `appid=DEIN_API_KEY` → persönlicher API-Schlüssel  

---

## 📸 Screenshot
![App Screenshot](./assets/screenshot_wetterapp.png)

---

## ▶️ Ausführen (Entwicklung)
1. Repository klonen oder herunterladen  
2. In VS Code öffnen  
3. Optional: „Live Server“-Extension installieren  
4. In der Datei `script.js` den eigenen **OpenWeatherMap-API-Key** eintragen:
   ```js
   const API_KEY = "DEIN_API_KEY";
