# PSX KSE-100 Forecasting Dashboard

## Overview
This project delivers a real-time stock market forecasting dashboard for the Pakistan Stock Exchange (PSX) KSE-100 index. It provides live data fetching, predictive analytics, and interactive visualizations for the index and its constituent companies. The system automatically refreshes data every 5 minutes and offers forecasting capabilities for intraday, next-day, and custom date predictions. The business vision is to provide a comprehensive, accurate, and user-friendly tool for investors and analysts focused on the PSX market, leveraging predictive analytics to aid informed decision-making.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture
The application employs a modular architecture, separating concerns into frontend, data, analytics, visualization, and utility layers. It is designed for real-time data processing with efficient caching mechanisms.

**Core Architectural Decisions:**
-   **Frontend**: Streamlit-based web dashboard with auto-refresh and wide layout for financial data.
-   **Data Layer**: Live data acquisition via web scraping and API integration from PSX sources, including comprehensive KSE-100 company mapping.
-   **Analytics Engine**: Utilizes Facebook Prophet for time series forecasting with configurable parameters, supporting daily and weekly seasonality, and providing 80% confidence intervals.
-   **Visualization Layer**: Interactive charts using Plotly, including candlestick charts with OHLC data and volume indicators, designed for responsiveness.
-   **Caching**: Lightweight in-memory caching (`simple_cache.py`) with a 5-minute TTL optimizes performance and reduces API calls, replacing prior database dependencies.
-   **UI/UX**: Optimized for financial dashboards, featuring sidebar controls, currency and percentage formatting, and CSV export capabilities. Color-coded themes indicate market conditions.
-   **Feature Specifications**: Includes intraday (5-minute intervals), next-day, and custom date forecasting; universal file upload for any financial instrument with automatic column detection; news-based market prediction with sentiment analysis; comprehensive real-time data for all 100 KSE-100 companies; and live KSE-40 dashboard with 5-minute auto-refresh capabilities.

## External Dependencies

**Core Libraries:**
-   **Streamlit**: Web application framework
-   **Pandas**: Data manipulation and analysis
-   **NumPy**: Numerical computing
-   **Plotly**: Interactive visualization
-   **Prophet**: Time series forecasting
-   **BeautifulSoup4**: Web scraping
-   **Requests**: HTTP library

**Specialized Libraries:**
-   **streamlit_autorefresh**: Auto-refresh functionality
-   **trafilatura**: Web content extraction
-   **datetime**: Date and time handling

**Data Sources:**
-   PSX official website (web scraping)
-   Authentic Pakistani financial websites (e.g., Business Recorder, Dawn Business, The News, Dunya Business)