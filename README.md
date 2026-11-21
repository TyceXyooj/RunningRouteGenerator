# Running Route Generator

A Python web application built with Flask, OSMnx, NetworkX, and Leaflet.js that dynamically generates randomized, looped running routes of a specified target distance starting and ending at a given street address. While designed primarily for runners, it can also be used for cycling, walking, or other outdoor activities.

## Features

* **Address Geocoding & Network Extraction:** Downloads real-world street network data around a starting address using OpenStreetMap via `osmnx`.
* **Randomized Loop Algorithm:** Generates non-repeating, looped routes by projecting outward, making a perpendicular 90-degree turn, and finding a return path that matches the target distance within a $\pm 800\text{m}$ tolerance.
* **Interactive Map Frontend:** Uses **Leaflet.js** and OpenStreetMap tiles to render generated GeoJSON routes directly in the browser, automatically fitting the map bounds to the route.
* **REST API Endpoint:** Exposes a `/get-route` endpoint that returns generated routes as standard GeoJSON `Feature` objects.

## Project Structure

```text
RunningRouteGenerator/
├── app.py                 # Flask web server handling routes and serving the frontend
├── routing.py             # Core pathfinding logic, coordinate ordering, and GeoJSON/GPX builders
├── requirements.txt       # Python package dependencies
├── Procfile               # Gunicorn deployment configuration
├── README.md              # Project documentation and attributions
├── templates/
│   ├── base.html          # Base Jinja2 HTML layout template
│   └── index.html         # Main user interface form and Leaflet.js map script
└── static/
    ├── css/
    │   └── main.css       # Application styling and loading spinner animations
    └── img/
        ├── earth-icon.ico # Favicon
        └── loader-icon.svg# Loading spinner graphic
```

## Installation & Setup

### 1. Prerequisites

Ensure you have **Python 3.10+** installed on your system.

### 2. Clone the Repository

```bash
git clone https://github.com/TyceXyooj/RunningRouteGenerator.git
cd RunningRouteGenerator
```

### 3. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Running the Web Application

Start the Flask development server:

```bash
python app.py
```

Open your browser and navigate to `http://127.0.0.1:5000/`. Enter a starting street address, city, state, ZIP code, and target distance in meters, then click **Generate Route!** to display the loop on the interactive map.

For production environments using Gunicorn (as configured in `Procfile`):

```bash
gunicorn app:app
```

### API Endpoint: `GET /get-route`

Retrieves a generated route as a GeoJSON `Feature` object.

**Query Parameters:**

* `street` (string): Street address (e.g., `123 Main St`)
* `city` (string): City name (e.g., `Menomonie`)
* `state` (string): State abbreviation (e.g., `WI`)
* `zip` (string): 5-digit ZIP code (e.g., `54751`)
* `distance` (float): Target route distance in meters (e.g., `5000`)

**Example Request:**

```http
GET /get-route?street=123+Main+St&city=Menomonie&state=WI&zip=54751&distance=5000
```

**Example Response:**

```json
{
  "type": "Feature",
  "geometry": {
    "type": "LineString",
    "coordinates": [
      [-91.9193, 44.8755],
      [-91.9180, 44.8762]
    ]
  },
  "properties": {
    "street": "123 Main St",
    "city": "Menomonie",
    "state": "WI",
    "zip": "54751",
    "distance": 5000.0,
    "point_count": 42
  }
}
```

## Future Plans & Roadmap

* **GPX File Download:** `routing.py` currently includes a `route_as_gpx()` function (not yet wired up to the web server or frontend) that converts generated routes into standard `.gpx` XML tracks. In a future update, a **Download GPX** button will be added to the UI so users can export their generated routes directly to GPS watches and fitness apps (such as Garmin, Strava, or Apple Watch).

## Author

* **Tyce Xiong** — [GitHub](https://github.com/TyceXyooj)

## Credits & Acknowledgements

This project relies on several open-source libraries, geographical data providers, and academic research.

### 1. Primary Academic Attribution

* **OSMnx Methodology & Academic Credit:**
  Boeing, G. (2025). Modeling and Analyzing Urban Networks and Amenities with OSMnx. *Geographical Analysis* 57 (4), 567-577. `doi:10.1111/gean.70009`

### 2. Core Libraries & Frameworks

* **OSMnx** — Python package to download, model, analyze, and visualize street networks and amenities from OpenStreetMap.
  * *Citation:* Boeing, G. (2017). OSMnx: New methods for acquiring, constructing, analyzing, and visualizing complex street networks. *Computers, Environment and Urban Systems*, 65, 126-139.
* **NetworkX** — Python software package for the creation, manipulation, and study of the structure, dynamics, and functions of complex networks.
  * *Citation:* Hagberg, A. A., Schult, D. A., & Swart, P. J. (2008). Exploring network structure, dynamics, and function using NetworkX. In *Proceedings of the 7th Python in Science Conference (SciPy 2008)* (pp. 11-15).
* **GeoPandas** — Open-source project to make working with geospatial data in Python easier by extending pandas data types.
* **Flask** — Micro web framework for Python developed by Pallets.
* **Leaflet** — Open-source JavaScript library for mobile-friendly interactive maps, created by Volodymyr Agafonkin and contributors, licensed under the BSD 2-Clause License.

### 3. Data Sources

* **OpenStreetMap (OSM)** — Street network data and map tiles are provided by OpenStreetMap contributors under the Open Database License (ODbL). © OpenStreetMap contributors.
