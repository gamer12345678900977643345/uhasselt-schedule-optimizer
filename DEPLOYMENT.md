# 🚀 Deployment Guide

Deze guide helpt je om de UHasselt Schedule Optimizer te deployen op verschillende platforms.

## 📋 Voorbereiding

### 1. Google Calendar API Setup

1. **Ga naar [Google Cloud Console](https://console.cloud.google.com/)**
2. **Maak een nieuw project aan** of selecteer een bestaand project
3. **Activeer de Google Calendar API:**
   - Ga naar "APIs & Services" > "Library"
   - Zoek naar "Google Calendar API"
   - Klik op "Enable"
4. **Maak credentials aan:**
   - Ga naar "APIs & Services" > "Credentials"
   - Klik op "Create Credentials" > "OAuth 2.0 Client ID"
   - Kies "Desktop application"
   - Download de JSON file en hernoem naar `credentials.json`

### 2. MyTimetable ICS URL

1. **Ga naar [MyTimetable](https://mytimetable.uhasselt.be/)**
2. **Log in met je UHasselt account**
3. **Ga naar "Export" > "iCal"**
4. **Kopieer de ICS URL** (begint met `https://mytimetable.uhasselt.be/ical/...`)

## 🌐 GitHub Actions (Aanbevolen - Gratis)

### Stap 1: Fork de Repository

1. **Fork deze repository** naar je eigen GitHub account
2. **Clone je fork:**
   ```bash
   git clone https://github.com/JOUW-USERNAME/uhasselt-schedule-optimizer.git
   cd uhasselt-schedule-optimizer
   ```

### Stap 2: Configureer GitHub Secrets

1. **Ga naar je repository op GitHub**
2. **Klik op "Settings" > "Secrets and variables" > "Actions"**
3. **Voeg de volgende secrets toe:**

   **Verplichte Secrets:**
   - `ICS_URL`: Je MyTimetable ICS URL
   - `GOOGLE_CREDENTIALS`: Inhoud van je `credentials.json` file

   **Optionele Variables:**
   - `CALENDAR_NAME`: Naam van je Google Calendar (standaard: "UHasselt Optimized Schedule")
   - `PREFERRED_GROUP`: Je voorkeursgroep (A, B, C, D, E)
   - `OPTIMIZATION_MODE`: earliest_lesson of latest_lesson

### Stap 3: Activeer GitHub Actions

1. **Ga naar de "Actions" tab** in je repository
2. **Klik op "I understand my workflows, go ahead and enable them"**
3. **De workflow draait automatisch elke dag om 8:00**

### Stap 4: Test de Workflow

1. **Ga naar "Actions" > "Daily Schedule Optimization"**
2. **Klik op "Run workflow"** om handmatig te testen
3. **Check de logs** om te zien of alles werkt

## ☁️ Heroku Deployment

### Stap 1: Heroku Setup

1. **Installeer [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)**
2. **Log in op Heroku:**
   ```bash
   heroku login
   ```

### Stap 2: Maak Heroku App

```bash
# Maak een nieuwe app aan
heroku create jouw-app-naam

# Of gebruik een bestaande app
heroku git:remote -a jouw-app-naam
```

### Stap 3: Configureer Environment Variables

```bash
# Stel je MyTimetable URL in
heroku config:set ICS_URL="https://mytimetable.uhasselt.be/ical/..."

# Stel Google Calendar credentials in
heroku config:set GOOGLE_CREDENTIALS="$(cat credentials.json)"

# Optionele configuratie
heroku config:set CALENDAR_NAME="Mijn UHasselt Rooster"
heroku config:set PREFERRED_GROUP="A"
heroku config:set OPTIMIZATION_MODE="earliest_lesson"
```

### Stap 4: Deploy

```bash
# Deploy naar Heroku
git push heroku main

# Start de app
heroku ps:scale web=1

# Bekijk logs
heroku logs --tail
```

### Stap 5: Setup Scheduler (Heroku Scheduler)

1. **Installeer Heroku Scheduler add-on:**
   ```bash
   heroku addons:create scheduler:standard
   ```

2. **Configureer dagelijkse taak:**
   - Ga naar [Heroku Dashboard](https://dashboard.heroku.com/)
   - Selecteer je app
   - Ga naar "Resources" > "Heroku Scheduler"
   - Klik op "Create job"
   - Command: `python main.py --config config.json --sync-google`
   - Frequency: `Daily at 8:00 AM`

## 🐳 Docker Deployment

### Stap 1: Build Docker Image

```bash
# Build de image
docker build -t uhasselt-schedule-optimizer .

# Run de container
docker run -p 5000:5000 \
  -e ICS_URL="https://mytimetable.uhasselt.be/ical/..." \
  -e GOOGLE_CREDENTIALS="$(cat credentials.json)" \
  uhasselt-schedule-optimizer
```

### Stap 2: Docker Compose

```bash
# Start met docker-compose
docker-compose up -d

# Bekijk logs
docker-compose logs -f
```

## 🔧 Lokale Development

### Stap 1: Setup

```bash
# Clone de repository
git clone https://github.com/yourusername/uhasselt-schedule-optimizer.git
cd uhasselt-schedule-optimizer

# Installeer dependencies
pip install -r requirements.txt

# Run setup script
python setup.py
```

### Stap 2: Test

```bash
# Test de optimizer
python main.py --config config.json --sync-google

# Test de API
python webhook_api.py
```

## 📊 Monitoring

### GitHub Actions
- **Logs**: Ga naar "Actions" tab in je repository
- **Status**: Check workflow runs voor success/failure
- **Artifacts**: Download logs en output files

### Heroku
```bash
# Bekijk logs
heroku logs --tail

# Check app status
heroku ps

# Restart app
heroku restart
```

### API Endpoints
- **Health Check**: `GET /health`
- **Status**: `GET /status`
- **Config**: `GET /config`

## 🚨 Troubleshooting

### Veelvoorkomende Problemen

1. **Google Calendar Authentication Failed**
   - Check of `credentials.json` correct is geconfigureerd
   - Verificeer dat Google Calendar API is geactiveerd
   - Check of de OAuth scopes correct zijn

2. **ICS URL Not Found**
   - Verificeer dat de MyTimetable URL correct is
   - Check of je ingelogd bent op MyTimetable
   - Probeer de URL handmatig in je browser

3. **GitHub Actions Failing**
   - Check de secrets in repository settings
   - Bekijk de workflow logs voor specifieke errors
   - Verificeer dat alle required secrets zijn ingesteld

4. **Heroku Deployment Issues**
   - Check de build logs: `heroku logs --tail`
   - Verificeer environment variables: `heroku config`
   - Check of de Procfile correct is

### Debug Mode

```bash
# Run met debug logging
python main.py --config config.json --sync-google --debug

# API met debug mode
FLASK_DEBUG=1 python webhook_api.py
```

## 📞 Support

Als je problemen ondervindt:

1. **Check de logs** voor specifieke error messages
2. **Bekijk de GitHub Issues** voor bekende problemen
3. **Maak een nieuwe issue** met:
   - Beschrijving van het probleem
   - Logs en error messages
   - Je configuratie (zonder gevoelige data)

## 🎉 Success!

Als alles correct is geconfigureerd:

- ✅ Je rooster wordt elke dag om 8:00 automatisch geoptimaliseerd
- ✅ Het geoptimaliseerde rooster wordt gesynchroniseerd met Google Calendar
- ✅ Je kunt de API gebruiken voor externe integraties
- ✅ Alle logs en output zijn beschikbaar voor monitoring

Veel succes met je geoptimaliseerde rooster! 🎓
