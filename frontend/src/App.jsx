import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Cloud,
  Database,
  Gauge,
  LayoutDashboard,
  RefreshCw,
  Wind,
} from "lucide-react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  getDailyForecasts,
  getForecasts,
  getMetadata,
  getSummary,
} from "./services/api";

const NAV_ITEMS = [
  { label: "Overview", icon: LayoutDashboard },
  { label: "Forecast Analysis", icon: Activity },
  { label: "Daily Performance", icon: BarChart3 },
];

const numberFormat = new Intl.NumberFormat("en-GB", {
  maximumFractionDigits: 0,
});

const decimalFormat = new Intl.NumberFormat("en-GB", {
  maximumFractionDigits: 2,
});

function formatMW(value) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) {
    return "—";
  }

  return `${numberFormat.format(Number(value))} MW`;
}

function formatNumber(value) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) {
    return "—";
  }

  return decimalFormat.format(Number(value));
}

function formatDateTime(value) {
  if (!value) return "—";

  return new Date(value).toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "UTC",
  }) + " UTC";
}

function MetricCard({
  title,
  value,
  description,
  icon: Icon,
  tone = "blue",
}) {
  return (
    <article className="metric-card">
      <div className="metric-top">
        <span className="metric-title">{title}</span>
        <span className={`metric-icon ${tone}`}>
          <Icon size={19} />
        </span>
      </div>

      <div className="metric-value">{value}</div>
      <div className="metric-description">{description}</div>
    </article>
  );
}

function EmptyState({ message }) {
  return <div className="empty-state">{message}</div>;
}

function App() {
  const [summary, setSummary] = useState(null);
  const [forecasts, setForecasts] = useState([]);
  const [daily, setDaily] = useState([]);
  const [metadata, setMetadata] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeNav, setActiveNav] = useState("Overview");
  const [selectedDay, setSelectedDay] = useState("all");
  const [search, setSearch] = useState("");

  async function loadDashboard() {
    setLoading(true);
    setError("");

    try {
      const [summaryData, forecastData, dailyData, metadataData] =
        await Promise.all([
          getSummary(),
          getForecasts(),
          getDailyForecasts(),
          getMetadata().catch(() => null),
        ]);

      setSummary(summaryData);
      setForecasts(forecastData.data ?? []);
      setDaily(dailyData.data ?? []);
      setMetadata(metadataData);
    } catch (err) {
      setError(
        `${err.message}. Check that FastAPI is running and CORS is configured.`
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  const chartData = useMemo(() => {
    const filtered =
      selectedDay === "all"
        ? forecasts
        : forecasts.filter(
            (item) => item.deliveryHour?.slice(0, 10) === selectedDay
          );

    return filtered.map((item) => ({
      ...item,
      time: item.deliveryHour
        ? new Date(item.deliveryHour).getTime()
        : null,
    }));
  }, [forecasts, selectedDay]);

  const filteredForecasts = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();

    return forecasts
      .filter((item) => {
        if (selectedDay !== "all") {
          if (item.deliveryHour?.slice(0, 10) !== selectedDay) return false;
        }

        if (!normalizedSearch) return true;

        return [
          item.deliveryHour,
          item.publishTime,
          item.forecastGeneration,
          item.actualGeneration,
          item.forecastError,
        ]
          .join(" ")
          .toLowerCase()
          .includes(normalizedSearch);
      })
      .slice(0, 100);
  }, [forecasts, search, selectedDay]);

  const averageAbsoluteDailyError = useMemo(() => {
    if (!daily.length) return null;

    return (
      daily.reduce((sum, item) => sum + Number(item.maeMW ?? 0), 0) /
      daily.length
    );
  }, [daily]);

  const bias = Number(summary?.bias_mw ?? 0);
  const positiveBias = bias >= 0;

  const dailyChartData = daily.map((item) => ({
    ...item,
    day: item.deliveryDate?.slice(-2) ?? "",
  }));

  function navigateTo(label) {
    setActiveNav(label);

    const target = document.getElementById(
      label === "Overview"
        ? "overview"
        : label === "Forecast Analysis"
          ? "forecast-analysis"
          : "daily-performance"
    );

    target?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-logo">
          <Wind size={30} />
        </div>
        <h2>Wind Forecast Intelligence</h2>
        <p>Loading January 2026 generation data...</p>
        <div className="loading-track">
          <div />
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Wind size={24} />
          </div>
          <div>
            <div className="brand-name">WindIQ</div>
            <div className="brand-subtitle">ENERGY INTELLIGENCE</div>
          </div>
        </div>

        <div className="workspace-label">WORKSPACE</div>

        <nav className="navigation" aria-label="Main navigation">
          {NAV_ITEMS.map(({ label, icon: Icon }) => (
            <button
              key={label}
              className={`nav-item ${activeNav === label ? "active" : ""}`}
              onClick={() => navigateTo(label)}
            >
              <Icon size={18} />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="sidebar-status">
            <span className="status-dot" />
            <div>
              <strong>Data service</strong>
              <small>Connected to local API</small>
            </div>
          </div>

          <div className="sidebar-footer">
            <div className="footer-icon">
              <Database size={16} />
            </div>
            <div>
              <strong>Elexon BMRS</strong>
              <small>Source data provider</small>
            </div>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb">
            <span>Analytics</span>
            <span className="breadcrumb-separator">/</span>
            <strong>{activeNav}</strong>
          </div>

          <div className="topbar-actions">
            <span className="period-pill">
              <CalendarDays size={15} />
              January 2026
            </span>

            <button
              className="refresh-button"
              onClick={loadDashboard}
              title="Refresh data"
              aria-label="Refresh data"
            >
              <RefreshCw size={17} />
            </button>
          </div>
        </header>

        {error && (
          <div className="error-banner" role="alert">
            <strong>Unable to load dashboard.</strong>
            <span>{error}</span>
            <button onClick={loadDashboard}>Retry</button>
          </div>
        )}

        <section className="page-heading" id="overview">
          <div>
            <div className="eyebrow">
              <span className="eyebrow-dot" />
              RENEWABLE GENERATION ANALYTICS
            </div>

            <h1>Wind Forecast Intelligence</h1>

            <p className="page-description">
              Understand forecast accuracy, identify generation uncertainty,
              and evaluate the information available for day-ahead purchasing.
            </p>
          </div>

          <div className="data-status">
            <CheckCircle2 size={17} />
            <span>January dataset loaded</span>
          </div>
        </section>

        <div className="context-banner">
          <div className="context-icon">
            <Clock3 size={19} />
          </div>
          <div>
            <strong>Day-ahead forecast evaluation</strong>
            <p>
              Forecasts are selected using a provisional 23:00 UTC previous-day
              cutoff. This assumption must be confirmed against the purchasing
              team's actual decision deadline.
            </p>
          </div>
        </div>

        <section className="metrics-grid" aria-label="Forecast metrics">
          <MetricCard
            title="Mean Absolute Error"
            value={formatMW(summary?.mae_mw)}
            description="Average absolute forecast error"
            icon={Activity}
            tone="blue"
          />

          <MetricCard
            title="Root Mean Square Error"
            value={formatMW(summary?.rmse_mw)}
            description="Penalises larger forecast errors"
            icon={Gauge}
            tone="purple"
          />

          <MetricCard
            title="Forecast Bias"
            value={
              summary?.bias_mw === undefined
                ? "—"
                : `${positiveBias ? "+" : ""}${formatNumber(summary.bias_mw)} MW`
            }
            description={
              positiveBias
                ? "Forecasts exceed actual generation on average"
                : "Forecasts fall below actual generation on average"
            }
            icon={positiveBias ? ArrowUpRight : ArrowDownRight}
            tone={positiveBias ? "orange" : "green"}
          />

          <MetricCard
            title="Forecast Coverage"
            value={
              summary?.coverage_percent === undefined
                ? "—"
                : `${formatNumber(summary.coverage_percent)}%`
            }
            description={`${numberFormat.format(
              summary?.matched_hours ?? 0
            )} matched hourly observations`}
            icon={CheckCircle2}
            tone="green"
          />
        </section>

        <section className="section-card chart-section" id="forecast-analysis">
          <div className="section-header">
            <div>
              <div className="section-kicker">GENERATION COMPARISON</div>
              <h2>Forecast vs. Actual Wind Generation</h2>
              <p className="section-description">
                Compare predicted and observed generation for each delivery hour.
              </p>
            </div>

            <div className="chart-controls">
              <label htmlFor="day-filter">Delivery date</label>
              <select
                id="day-filter"
                value={selectedDay}
                onChange={(event) => setSelectedDay(event.target.value)}
              >
                <option value="all">Entire month</option>
                {daily.map((item) => (
                  <option key={item.deliveryDate} value={item.deliveryDate}>
                    {item.deliveryDate}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="chart-legend">
            <span><i className="legend-dot forecast-dot" /> Forecast</span>
            <span><i className="legend-dot actual-dot" /> Actual generation</span>
          </div>

          <div className="chart-container">
            {chartData.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={chartData}
                  margin={{ top: 12, right: 16, left: 8, bottom: 4 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                    stroke="#e9edf3"
                  />

                  <XAxis
                    dataKey="deliveryHour"
                    tickFormatter={(value) => {
                      const date = new Date(value);
                      return selectedDay === "all"
                        ? date.toLocaleDateString("en-GB", {
                            day: "2-digit",
                            month: "short",
                            timeZone: "UTC",
                          })
                        : date.toLocaleTimeString("en-GB", {
                            hour: "2-digit",
                            minute: "2-digit",
                            timeZone: "UTC",
                          });
                    }}
                    tick={{ fill: "#8792a5", fontSize: 11 }}
                    minTickGap={35}
                    axisLine={false}
                    tickLine={false}
                  />

                  <YAxis
                    tickFormatter={(value) => `${Math.round(value / 1000)}k`}
                    tick={{ fill: "#8792a5", fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    width={42}
                    domain={["auto", "auto"]}
                  />

                  <Tooltip
                    labelFormatter={(value) => formatDateTime(value)}
                    formatter={(value, name) => [
                      formatMW(value),
                      name === "forecastGeneration"
                        ? "Forecast"
                        : "Actual generation",
                    ]}
                    contentStyle={{
                      borderRadius: 12,
                      border: "1px solid #e8edf4",
                      boxShadow: "0 8px 30px rgba(15, 23, 42, 0.08)",
                    }}
                  />

                  <Legend
                    formatter={(value) =>
                      value === "forecastGeneration"
                        ? "Forecast"
                        : "Actual generation"
                    }
                  />

                  <Line
                    type="monotone"
                    dataKey="forecastGeneration"
                    name="forecastGeneration"
                    stroke="#4778ed"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4 }}
                    connectNulls={false}
                  />

                  <Line
                    type="monotone"
                    dataKey="actualGeneration"
                    name="actualGeneration"
                    stroke="#13a87d"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4 }}
                    connectNulls={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState message="No forecast records are available for this selection." />
            )}
          </div>

          <div className="chart-footnote">
            <span>All timestamps displayed in UTC.</span>
            <span>Generation measured in MW.</span>
          </div>
        </section>

        <section
          className="section-card daily-section"
          id="daily-performance"
        >
          <div className="section-header">
            <div>
              <div className="section-kicker">TREND ANALYSIS</div>
              <h2>Daily Forecast Performance</h2>
              <p className="section-description">
                Review how average generation and absolute forecast error vary
                throughout the month.
              </p>
            </div>
            <span className="small-badge">31 delivery days</span>
          </div>

          <div className="daily-summary">
            <div>
              <span className="summary-label">Average daily MAE</span>
              <strong>
                {averageAbsoluteDailyError === null
                  ? "—"
                  : formatMW(averageAbsoluteDailyError)}
              </strong>
            </div>
            <div>
              <span className="summary-label">Daily records</span>
              <strong>{daily.length}</strong>
            </div>
            <div>
              <span className="summary-label">Matched hours</span>
              <strong>{numberFormat.format(summary?.matched_hours ?? 0)}</strong>
            </div>
          </div>

          <div className="daily-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Delivery date</th>
                  <th>Avg. forecast</th>
                  <th>Avg. actual</th>
                  <th>Daily MAE</th>
                  <th>Daily bias</th>
                  <th>Hours</th>
                </tr>
              </thead>
              <tbody>
                {daily.map((item) => (
                  <tr key={item.deliveryDate}>
                    <td className="date-cell">
                      {new Date(
                        `${item.deliveryDate}T12:00:00Z`
                      ).toLocaleDateString("en-GB", {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                        timeZone: "UTC",
                      })}
                    </td>
                    <td>{formatMW(item.averageForecastMW)}</td>
                    <td>{formatMW(item.averageActualMW)}</td>
                    <td className="error-cell">{formatMW(item.maeMW)}</td>
                    <td>
                      <span
                        className={`bias-chip ${
                          Number(item.biasMW) >= 0 ? "bias-positive" : "bias-negative"
                        }`}
                      >
                        {Number(item.biasMW) > 0 ? "+" : ""}
                        {formatNumber(item.biasMW)} MW
                      </span>
                    </td>
                    <td>{item.deliveryHours ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="section-card records-section">
          <div className="section-header records-header">
            <div>
              <div className="section-kicker">OBSERVATION-LEVEL DETAIL</div>
              <h2>Forecast Records</h2>
              <p className="section-description">
                Inspect forecast publication times and corresponding actual
                generation for individual delivery hours.
              </p>
            </div>

            <div className="search-box">
              <input
                type="search"
                placeholder="Search records..."
                aria-label="Search forecast records"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </div>
          </div>

          <div className="table-info">
            Showing {filteredForecasts.length} of{" "}
            {numberFormat.format(forecasts.length)} hourly records
            {selectedDay !== "all" ? ` for ${selectedDay}` : ""}
          </div>

          <div className="daily-table-wrap">
            <table className="data-table records-table">
              <thead>
                <tr>
                  <th>Delivery hour (UTC)</th>
                  <th>Forecast published (UTC)</th>
                  <th>Forecast (MW)</th>
                  <th>Actual (MW)</th>
                  <th>Forecast error (MW)</th>
                </tr>
              </thead>
              <tbody>
                {filteredForecasts.map((item, index) => (
                  <tr key={`${item.deliveryHour}-${index}`}>
                    <td className="date-cell">
                      {formatDateTime(item.deliveryHour)}
                    </td>
                    <td>{formatDateTime(item.publishTime)}</td>
                    <td>{formatMW(item.forecastGeneration)}</td>
                    <td>{formatMW(item.actualGeneration)}</td>
                    <td>
                      <span
                        className={`bias-chip ${
                          Number(item.forecastError) >= 0
                            ? "bias-positive"
                            : "bias-negative"
                        }`}
                      >
                        {Number(item.forecastError) > 0 ? "+" : ""}
                        {formatNumber(item.forecastError)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="table-footnote">
            The table displays up to 100 matching rows to keep the interface
            responsive. Search and delivery-date filters narrow the records.
          </p>
        </section>

        <section className="methodology-card">
          <div className="methodology-icon">
            <Cloud size={21} />
          </div>
          <div>
            <h3>Methodology and limitations</h3>
            <p>
              Forecast error is calculated as forecast generation minus actual
              generation. Positive bias indicates overforecasting on average;
              negative bias indicates underforecasting. MAE measures average
              absolute error, while RMSE gives greater weight to larger errors.
              Actual half-hourly generation is averaged into hourly values for
              comparison with hourly forecasts.
            </p>
            <p>
              The current decision cutoff is provisional. Forecast coverage
              describes matched observations under that assumption; it does not
              establish that the forecast was available by the purchasing
              team's confirmed deadline. Wind generation alone also does not
              determine the utility's complete electricity procurement need.
            </p>
            {metadata && (
              <p className="metadata-note">
                API metadata is available. See the backend documentation for
                endpoint details.
              </p>
            )}
          </div>
        </section>

        <footer className="page-footer">
          <span>WindIQ · Wind Forecast Intelligence</span>
          <span>Data source: Elexon BMRS · January 2026</span>
        </footer>
      </main>
    </div>
  );
}

export default App;
