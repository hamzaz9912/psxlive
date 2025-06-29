# PSX KSE-100 Forecasting Dashboard

## Overview

This is a real-time stock market forecasting dashboard specifically designed for the Pakistan Stock Exchange (PSX) KSE-100 index. The application provides live data fetching, predictive analytics, and interactive visualizations for the KSE-100 index and its constituent companies. The system automatically refreshes data every 5 minutes and offers forecasting capabilities for intraday, next-day, and custom date predictions.

## System Architecture

The application follows a modular architecture with clear separation of concerns:

- **Frontend**: Streamlit-based web dashboard with auto-refresh capabilities
- **Data Layer**: Web scraping and API integration for live stock data
- **Analytics Engine**: Machine learning models for stock price forecasting
- **Visualization Layer**: Interactive charts using Plotly
- **Utilities**: Helper functions for data formatting and export

The architecture supports real-time data processing with caching mechanisms to optimize performance and reduce API calls.

## Key Components

### 1. Main Application (`app.py`)
- **Purpose**: Entry point and UI orchestration
- **Key Features**: 
  - Auto-refresh every 5 minutes using `streamlit_autorefresh`
  - Session state management for data persistence
  - Wide layout configuration optimized for financial dashboards
  - Sidebar controls for user interaction

### 2. Data Fetching Module (`data_fetcher.py`)
- **Purpose**: Live data acquisition from PSX sources
- **Key Features**:
  - Web scraping with proper headers and session management
  - KSE-100 companies mapping with 20+ major stocks
  - Caching with 5-minute TTL to optimize performance
  - Robust error handling for unreliable data sources

### 3. Forecasting Engine (`forecasting.py`)
- **Purpose**: Stock price prediction using machine learning
- **Technology**: Facebook Prophet for time series forecasting
- **Key Features**:
  - Configurable forecasting parameters (changepoint sensitivity, seasonality)
  - Support for daily and weekly seasonality patterns
  - 80% confidence intervals for predictions
  - Multiplicative seasonality mode optimized for financial data

### 4. Visualization Module (`visualization.py`)
- **Purpose**: Interactive chart generation
- **Technology**: Plotly for dynamic visualizations
- **Key Features**:
  - Candlestick charts with OHLC data
  - Volume indicators as subplots
  - Color-coded themes for different market conditions
  - Responsive design for various screen sizes

### 5. Utilities (`utils.py`)
- **Purpose**: Helper functions for data processing
- **Key Features**:
  - Currency formatting with PKR symbol
  - Percentage formatting with configurable decimal places
  - Volume formatting with appropriate units
  - CSV export capabilities

## Data Flow

1. **Data Acquisition**: Web scraping from PSX sources every 5 minutes
2. **Data Processing**: Cleaning and structuring raw market data
3. **Caching**: Temporary storage with TTL to reduce API calls
4. **Forecasting**: Prophet model training and prediction generation
5. **Visualization**: Real-time chart updates with forecast overlays
6. **User Interaction**: Dashboard controls for customization and export

## External Dependencies

### Core Libraries
- **Streamlit**: Web application framework
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Plotly**: Interactive visualization
- **Prophet**: Time series forecasting
- **BeautifulSoup4**: Web scraping
- **Requests**: HTTP library

### Specialized Libraries
- **streamlit_autorefresh**: Auto-refresh functionality
- **trafilatura**: Web content extraction
- **datetime**: Date and time handling

### Data Sources
- PSX official website (web scraping)
- Investing.com (potential backup source)
- TradingView widgets (alternative data source)

## Deployment Strategy

The application is designed for deployment on cloud platforms with the following considerations:

### Recommended Platforms
1. **Streamlit Cloud**: Primary deployment target with native Streamlit support
2. **Render**: Alternative with good performance and reliability
3. **Heroku**: Backup option with free tier availability

### Deployment Requirements
- Python 3.8+ runtime environment
- Memory requirements: ~512MB for Prophet model
- Auto-refresh capabilities require persistent connections
- Rate limiting considerations for web scraping

### Performance Optimizations
- Streamlit caching with 5-minute TTL
- Session state management for data persistence
- Efficient data structures using Pandas
- Lazy loading of forecasting models

## Changelog
- June 29, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.