# UHasselt Schedule Optimizer

Back-end tool die de UHasselt MyTimetable ICS-link automatisch analyseert, groepen detecteert (A/B/all/{N/A}), en een geoptimaliseerde Google Calendar ICS genereert volgens voorkeuren van de gebruiker.

## Doel

Minimaliseer tijdsverlies tussen lessen door lessen van parallelle groepen te vergelijken (bv. groep A en B) en de vroegste of best passende lessen te kiezen.

## Gebruik

### Lokale installatie

1. Installeer Python 3.10 of hoger
2. Installeer dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configureer de tool:
   - Bewerk `config.json` met je MyTimetable ICS URL
   - Pas voorkeuren aan (groep, optimalisatiemodus, etc.)

4. Run de optimizer:
   ```bash
   python main.py --url "https://mytimetable.uhasselt.be/ical/..." --output "mijn_rooster.ics"
   ```

### Configuratie

De `config.json` file bevat de volgende opties:

- `ics_url`: Je MyTimetable ICS URL
- `preferred_group`: Voorkeursgroep ("A", "B", "C", "D", "E")
- `fallback_group_behavior`: Wat te doen als voorkeursgroep niet beschikbaar is
- `optimization_mode`: "earliest_lesson" of "latest_lesson"
- `minimum_break_minutes`: Minimale pauze tussen lessen
- `skip_weekends`: Weekendlessen overslaan (true/false)
- `timezone`: Tijdzone (standaard: "Europe/Brussels")

## Functionaliteit

### Groepdetectie

De tool detecteert automatisch groepen via regex-patronen:
- Groep A/B/C/D/E
- "all" of "alle" voor alle groepen
- {N/A} voor niet-toepasbare groepen

### Optimalisatie

1. **Download**: ICS-bestand wordt gedownload van MyTimetable
2. **Parse**: Events worden geanalyseerd en gegroepeerd per vak
3. **Detectie**: Groepen worden automatisch gedetecteerd
4. **Selectie**: Per vak wordt de beste les gekozen volgens voorkeuren
5. **Generatie**: Nieuwe ICS wordt gegenereerd met optimale planning

### Output

Het gegenereerde ICS-bestand bevat:
- `SUMMARY`: Vaknaam + Type + Groep
- `DESCRIPTION`: Docent(en), Locatie, Groep(en), Oorspronkelijke MyTimetable ID
- `LOCATION`: Originele locatie (A101, A102, ...)
- `DTSTART_DTEND`: Exacte start- en eindtijd (met tijdzone)

## Voorbeeld

```bash
# Met configuratiebestand
python main.py --config config.json

# Met directe URL
python main.py --url "https://mytimetable.uhasselt.be/ical/..." --output "optimized.ics"
```

## Toekomstige uitbreidingen

- Webinterface voor groepselectie en voorkeuren
- Automatische integratie met Google Calendar API
- Weekvisualisatie van vrije tijd en zelfstudieblokken
- Machine-learning suggesties op basis van les- en prestatiepatronen

## Auteur

Michel Carmans - UHasselt Schedule Optimizer v1.0
