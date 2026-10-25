# Wind Forecast Intelligence

A data-driven dashboard for analysing UK wind generation forecasts against actual generation, measuring forecast accuracy, and identifying daily forecasting errors.

## Project Overview

Electricity purchasing teams need reliable generation forecasts to support day-ahead purchasing decisions. Errors in renewable generation forecasts can create uncertainty around the amount of electricity that must be sourced from other market participants.

**Wind Forecast Intelligence** analyses wind generation forecasts published for the UK electricity market and compares them with actual wind generation data.

The application provides an interactive dashboard with summary metrics, forecast-versus-actual comparisons, and daily performance analysis.

The current implementation analyses January 2026 data.

## Key Features

- **Performance Overview:** View key forecast accuracy metrics, including Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), and forecast bias.
- **Forecast Analysis:** Compare predicted wind generation against actual generation over the selected analysis period.
- **Daily Performance:** Examine daily forecast accuracy, average forecast generation, average actual generation, and forecast bias.
- **Forecast Selection:** Select the latest eligible forecast publication available before the configured day-ahead cutoff.
- **REST API:** Access forecast data, summary metrics, daily aggregations, and analysis results through FastAPI endpoints.
- **Containerized Deployment:** Run the frontend and backend together using Docker Compose.

## Technology Stack

### Frontend

- React
- Vite
- Recharts
- Lucide React
- JavaScript
- CSS

### Backend

- Python
- FastAPI
- Pandas
- NumPy
- Uvicorn

### Infrastructure and Testing

- Docker
- Docker Compose
- Nginx
- Pytest
- Git and GitHub

## Data Sources

The application uses the UK electricity market data provided by Elexon.

**API base:** `https://data.elexon.co.uk/bmrs/api/v1`

Two principal data sources are used.

| Dataset | Purpose |
|---|---|
| FUELHH | Retrieve actual wind generation data. |
| WINDFOR | Retrieve wind generation forecast publications. |

The actual generation data is retrieved for January 2026. Forecast publications are collected from the relevant publication period, including December 2025 and January 2026, so that eligible forecasts for January delivery can be selected.

### Data Processing

The processing pipeline performs the following steps:

1. Retrieve actual wind generation data and wind forecast publications.
2. Filter forecast records to the January 2026 delivery period.
3. Aggregate half-hourly actual generation observations into hourly values using the mean of the two half-hourly observations.
4. Apply the configured forecast publication cutoff for each delivery day.
5. Select the latest eligible forecast for each delivery hour.
6. Match selected forecasts with actual generation observations.
7. Calculate forecast errors and aggregate performance metrics.
8. Make the processed results available to the dashboard and REST API.

The current analysis contains 744 matched hourly observations, representing 24 hours for each of the 31 days in January 2026.

## Forecast Accuracy Methodology

Let:

- \(F_t\) represent forecast wind generation for hour \(t\).
- \(A_t\) represent actual wind generation for hour \(t\).
- \(N\) represent the number of matched hourly observations.

### Forecast Error

Forecast error is calculated as:

\[
e_t = F_t - A_t
\]

A positive error means wind generation was overforecast. A negative error means wind generation was underforecast.

### Mean Absolute Error (MAE)

MAE measures the average magnitude of forecast errors, regardless of direction.

\[
MAE = \frac{1}{N}\sum_{t=1}^{N}|F_t-A_t|
\]

A lower MAE indicates better forecast accuracy.

### Root Mean Squared Error (RMSE)

RMSE penalizes larger errors more heavily than smaller errors.

\[
RMSE = \sqrt{\frac{1}{N}\sum_{t=1}^{N}(F_t-A_t)^2}
\]

A lower RMSE indicates better performance, particularly when large errors are important.

### Forecast Bias

Forecast bias measures the average signed forecast error.

\[
Bias = \frac{1}{N}\sum_{t=1}^{N}(F_t-A_t)
\]

- Positive bias indicates overforecasting.
- Negative bias indicates underforecasting.
- Bias near zero indicates little average directional error, although individual errors may still be large.

All generation and error metrics are expressed in megawatts (MW).

## Day-Ahead Cutoff Assumption

The current implementation uses **23:00 UTC on the day before delivery** as a provisional forecast publication cutoff.

This is an implementation assumption, not a verified business requirement.

The assignment does not specify an exact decision cutoff time. The cutoff should therefore be confirmed with the relevant business stakeholder or updated if the assignment's full requirements establish a different rule.

Forecasts published after the configured cutoff must not be used when evaluating the day-ahead forecast available at that decision point.

## January 2026 Analysis Results

Using the current provisional cutoff, the analysis produces the following results:

| Metric | Result |
|---|---:|
| Analysis period | 1–31 January 2026 |
| Matched hourly observations | 744 |
| Hourly coverage | 100% |
| Mean Absolute Error (MAE) | 1,935.73 MW |
| Root Mean Squared Error (RMSE) | 2,406.10 MW |
| Forecast Bias | +1,713.72 MW |

### Initial Interpretation

- The matched dataset covers all 744 hourly delivery periods in January 2026.
- The MAE indicates the average magnitude of forecast error across the analysed hours.
- The RMSE exceeds the MAE, reflecting the greater influence of larger errors on the squared-error metric.
- The positive bias indicates that forecast generation was higher than actual generation on average under the current forecast-selection methodology.

These results describe the selected dataset and cutoff assumption. They should not be interpreted as a complete assessment of electricity market procurement costs or financial exposure.

## Application Architecture

The application uses a React frontend, a FastAPI backend, and Nginx to serve the frontend and route API requests.

```text
                    User / Browser
                          |
                          v
                  React Dashboard
                          |
                          v
                    Nginx :80
                     /       \
                    /         \
             Frontend       /api/*
             Static Files       |
                                v
                         FastAPI Backend
                            :8000
                                |
                                v
                     Pandas Analysis Layer
                                |
                                v
                       Processed Data Files
```

Docker Compose runs the frontend and backend as separate services on a shared Docker network.

The frontend is exposed on host port `8081` by default. Nginx forwards requests beginning with `/api/` to the backend service.

## REST API

The backend exposes the following endpoints.

| Endpoint | Description |
|---|---|
| `GET /api/health` | Check API health. |
| `GET /api/metadata` | Retrieve analysis metadata. |
| `GET /api/summary` | Retrieve summary forecast performance metrics. |
| `GET /api/forecasts` | Retrieve hourly forecast analysis data. |
| `GET /api/forecasts/daily` | Retrieve daily forecast performance summaries. |
| `GET /api/analysis` | Retrieve analysis results. |
| `GET /api/openapi.json` | Retrieve the OpenAPI schema. |

Interactive API documentation is available at:

`/api/docs`

For a local Docker deployment, the complete documentation address is:

`http://localhost:8081/api/docs`

## Project Structure

```text
wind-forecast-intelligence/
├── backend/
│   ├── data/
│   │   ├── actual_wind_january_2026.json
│   │   ├── wind_forecasts_january_2026.json
│   │   └── forecast_analysis_january_2026.csv
│   ├── main.py
│   ├── analyze_forecasts.py
│   ├── test_analysis.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── services/
│   │   └── ...
│   ├── package.json
│   ├── package-lock.json
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
├── .gitignore
└── README.md
```

The frontend directory may contain additional application components, pages, assets, and configuration files.

The data files listed above are generated or downloaded during data preparation and analysis. They should be retained in the repository if the application requires them at runtime.

## Getting Started

### Prerequisites

Install the following tools:

- Git
- Docker Desktop, or Docker Engine with the Docker Compose plugin

Docker is the recommended way to run the complete application because it builds the frontend and backend in separate containers.

### Run with Docker Compose

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_RANDOM_REPOSITORY_NAME.git
cd YOUR_RANDOM_REPOSITORY_NAME
```

Replace the example repository URL with the actual public GitHub repository URL.

Build and start the application:

```bash
docker compose up --build -d
```

Open the dashboard:

`http://localhost:8081`

Open the API documentation:

`http://localhost:8081/api/docs`

### Verify the Running Services

Check the container status:

```bash
docker compose ps
```

Check backend logs:

```bash
docker compose logs backend
```

Check frontend logs:

```bash
docker compose logs frontend
```

Stop the application:

```bash
docker compose down
```

## Running the Backend Locally

The backend can also be run independently for development and testing.

Navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

Start the API server:

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The backend will be available at:

`http://127.0.0.1:8000`

When running the backend independently, ensure the frontend is configured to use the correct API base URL and that CORS settings permit the frontend's origin.

## Running the Tests

The backend contains automated tests for forecast metrics and cutoff-based forecast selection.

From the backend directory, install the project dependencies and run:

```bash
python -m pytest -v
```

The current test suite covers:

- Forecast metric calculations.
- Empty input handling.
- Selection of the latest eligible forecast.
- Exclusion of forecasts published after the cutoff.
- Retention of the latest eligible publication when multiple publications exist.

The current local test suite contains five tests.

## Assumptions and Limitations

1. **Forecast cutoff:** The 23:00 UTC day-before-delivery cutoff is provisional and must be confirmed against the business decision rule.
2. **Analysis period:** The current analysis covers January 2026 rather than a continuous, real-time forecasting service.
3. **Actual generation aggregation:** Half-hourly actual generation observations are aggregated into hourly values using their mean.
4. **Data coverage:** The current results contain 744 matched hourly observations. Complete coverage does not, by itself, establish that the forecast-selection methodology is optimal.
5. **Procurement requirements:** The application does not include electricity demand, other generation sources, imports, storage, or market prices. It therefore does not calculate the actual residual electricity procurement requirement or its financial cost.
6. **Forecast uncertainty:** The dashboard measures historical forecast error. It does not currently produce probabilistic forecasts or confidence intervals.
7. **Market interpretation:** Forecast accuracy metrics alone cannot establish the financial impact of forecasting errors without additional demand, pricing, and procurement data.

## Potential Future Enhancements

- Confirm and configure the business-defined day-ahead cutoff.
- Support additional historical periods and automated data refreshes.
- Add forecast error distributions and extreme-error analysis.
- Compare performance across delivery hours, weekdays, and weather conditions.
- Introduce probabilistic forecast evaluation when suitable data is available.
- Incorporate demand forecasts, market prices, and other relevant data to estimate procurement exposure.
- Add configurable analysis periods and exportable reports.

## Deployment

**Dashboard URL:** To be added after deployment.

**Demonstration video:** To be added after recording and uploading the project walkthrough.

## AI Tools Used

OpenAI ChatGPT was used as an AI-assisted development tool during the project to support implementation, debugging, code review, analytical explanations, and documentation.

The application code, data-processing logic, test results, and final deliverables should be reviewed and verified by the project author.

## Data Attribution

Wind generation data and forecast publications are sourced from the Elexon Balancing Mechanism Reporting Service (BMRS).

Data source:

`https://data.elexon.co.uk/bmrs/api/v1`

The analysis is based on the retrieved data and the methodology documented in this repository.

## License

No open-source license has been specified for this project.