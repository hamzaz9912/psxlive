import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# Import custom modules
from data_fetcher import DataFetcher
from forecasting import StockForecaster
from visualization import ChartVisualizer
from utils import export_to_csv, format_currency
from database import get_database_manager

# Page configuration
st.set_page_config(
    page_title="PSX KSE-100 Forecasting Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'data_fetcher' not in st.session_state:
    st.session_state.data_fetcher = DataFetcher()
if 'forecaster' not in st.session_state:
    st.session_state.forecaster = StockForecaster()
if 'visualizer' not in st.session_state:
    st.session_state.visualizer = ChartVisualizer()
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = get_database_manager()
if 'last_update' not in st.session_state:
    st.session_state.last_update = None
if 'kse_data' not in st.session_state:
    st.session_state.kse_data = None
if 'companies_data' not in st.session_state:
    st.session_state.companies_data = {}

def main():
    st.title("📈 PSX KSE-100 Forecasting Dashboard")
    st.markdown("---")
    
    # Auto-refresh every 5 minutes (300 seconds)
    count = st_autorefresh(interval=300000, limit=None, key="data_refresh")
    
    # Sidebar for controls
    with st.sidebar:
        st.header("Dashboard Controls")
        
        # Refresh button
        if st.button("🔄 Refresh Data Now", use_container_width=True):
            st.session_state.last_update = None
            st.rerun()
        
        # Show last update time
        if st.session_state.last_update:
            st.info(f"Last Updated: {st.session_state.last_update.strftime('%H:%M:%S')}")
        
        st.markdown("---")
        
        # Analysis type selection
        analysis_type = st.selectbox(
            "Select Analysis Type",
            ["KSE-100 Index", "Individual Companies", "Database Overview"],
            key="analysis_type"
        )
        
        # Date range selection
        st.subheader("Forecast Settings")
        forecast_type = st.selectbox(
            "Forecast Period",
            ["Today (Intraday)", "Next Day", "Custom Date Range"],
            key="forecast_type"
        )
        
        custom_date = None
        days_ahead = 1
        
        if forecast_type == "Custom Date Range":
            custom_date = st.date_input(
                "Select Target Date",
                value=datetime.now().date() + timedelta(days=7),
                min_value=datetime.now().date(),
                max_value=datetime.now().date() + timedelta(days=365)
            )
            days_ahead = (custom_date - datetime.now().date()).days
        elif forecast_type == "Today (Intraday)":
            days_ahead = 0
        
        # Company selection for individual analysis
        selected_company = None
        if analysis_type == "Individual Companies":
            companies = st.session_state.data_fetcher.get_kse100_companies()
            selected_company = st.selectbox(
                "Select Company",
                list(companies.keys()),
                key="selected_company"
            )
    
    # Main content area
    if analysis_type == "KSE-100 Index":
        display_kse100_analysis(forecast_type, days_ahead, custom_date)
    elif analysis_type == "Individual Companies":
        display_company_analysis(selected_company, forecast_type, days_ahead, custom_date)
    else:
        display_database_overview()

def display_kse100_analysis(forecast_type, days_ahead, custom_date):
    """Display KSE-100 index analysis and forecasting"""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 KSE-100 Index Analysis")
    
    with col2:
        if st.button("💾 Export Data", use_container_width=True):
            if st.session_state.kse_data is not None:
                csv = export_to_csv(st.session_state.kse_data, "KSE-100")
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"kse100_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    # Fetch KSE-100 data
    with st.spinner("Fetching KSE-100 data..."):
        try:
            kse_data = None
            
            # First try to get recent data from database
            db_data = st.session_state.db_manager.get_stock_data('KSE-100', days=30)
            
            # Check if we need fresh data (older than 5 minutes)
            need_fresh_data = True
            if db_data is not None and not db_data.empty:
                latest_db_date = pd.to_datetime(db_data['date'].max())
                if (datetime.now() - latest_db_date).total_seconds() < 300:  # 5 minutes
                    need_fresh_data = False
                    kse_data = db_data
            
            # Fetch fresh data if needed
            if need_fresh_data:
                kse_data = st.session_state.data_fetcher.fetch_kse100_data()
                if kse_data is not None and not kse_data.empty:
                    # Store in database
                    st.session_state.db_manager.store_stock_data('KSE-100', 'KSE-100 Index', kse_data)
            
            if kse_data is not None and not kse_data.empty:
                st.session_state.kse_data = kse_data
                st.session_state.last_update = datetime.now()
                
                # Current price display
                current_price = kse_data['close'].iloc[-1]
                prev_price = kse_data['close'].iloc[-2] if len(kse_data) > 1 else current_price
                change = current_price - prev_price
                change_pct = (change / prev_price) * 100 if prev_price != 0 else 0
                
                # Display current metrics
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                
                with metric_col1:
                    st.metric(
                        "Current Price",
                        format_currency(current_price),
                        delta=f"{change:+.2f} ({change_pct:+.2f}%)"
                    )
                
                with metric_col2:
                    st.metric("High", format_currency(kse_data['high'].iloc[-1]))
                
                with metric_col3:
                    st.metric("Low", format_currency(kse_data['low'].iloc[-1]))
                
                # Historical chart
                st.subheader("📈 Live Price Movement")
                historical_chart = st.session_state.visualizer.create_price_chart(
                    kse_data, "KSE-100 Index - Live Data"
                )
                st.plotly_chart(historical_chart, use_container_width=True)
                
                # Forecasting
                st.subheader("🔮 Price Forecast")
                
                with st.spinner("Generating forecast..."):
                    try:
                        forecast_data = st.session_state.forecaster.forecast_stock(
                            kse_data, days_ahead=days_ahead
                        )
                        
                        if forecast_data is not None:
                            # Display forecast metrics
                            forecast_price = forecast_data['yhat'].iloc[-1]
                            forecast_change = forecast_price - current_price
                            forecast_change_pct = (forecast_change / current_price) * 100
                            
                            forecast_col1, forecast_col2 = st.columns(2)
                            
                            with forecast_col1:
                                period_text = {
                                    0: "End of Day",
                                    1: "Tomorrow",
                                    days_ahead: f"{days_ahead} Days Ahead" if days_ahead > 1 else "Tomorrow"
                                }.get(days_ahead, f"{days_ahead} Days Ahead")
                                
                                st.metric(
                                    f"Forecasted Price ({period_text})",
                                    format_currency(forecast_price),
                                    delta=f"{forecast_change:+.2f} ({forecast_change_pct:+.2f}%)"
                                )
                            
                            with forecast_col2:
                                confidence_lower = forecast_data['yhat_lower'].iloc[-1]
                                confidence_upper = forecast_data['yhat_upper'].iloc[-1]
                                st.metric(
                                    "Confidence Range",
                                    f"{format_currency(confidence_lower)} - {format_currency(confidence_upper)}"
                                )
                            
                            # Forecast chart
                            forecast_chart = st.session_state.visualizer.create_forecast_chart(
                                kse_data, forecast_data, "KSE-100 Index Forecast"
                            )
                            st.plotly_chart(forecast_chart, use_container_width=True)
                            
                        else:
                            st.error("Unable to generate forecast. Insufficient data.")
                            
                    except Exception as e:
                        st.error(f"Forecasting error: {str(e)}")
                
            else:
                st.error("Unable to fetch KSE-100 data. Please try again later.")
                
        except Exception as e:
            st.error(f"Data fetching error: {str(e)}")

def display_company_analysis(selected_company, forecast_type, days_ahead, custom_date):
    """Display individual company analysis and forecasting"""
    
    if not selected_company:
        st.info("Please select a company from the sidebar to view analysis.")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"📊 {selected_company} Analysis")
    
    with col2:
        if st.button("💾 Export Data", use_container_width=True):
            if selected_company in st.session_state.companies_data:
                csv = export_to_csv(st.session_state.companies_data[selected_company], selected_company)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"{selected_company.lower().replace(' ', '_')}_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    # Fetch company data
    with st.spinner(f"Fetching {selected_company} data..."):
        try:
            company_data = None
            company_symbol = st.session_state.data_fetcher.get_kse100_companies()[selected_company]
            
            # First try to get recent data from database
            db_data = st.session_state.db_manager.get_stock_data(company_symbol, days=30)
            
            # Check if we need fresh data (older than 5 minutes)
            need_fresh_data = True
            if db_data is not None and not db_data.empty:
                latest_db_date = pd.to_datetime(db_data['date'].max())
                if (datetime.now() - latest_db_date).total_seconds() < 300:  # 5 minutes
                    need_fresh_data = False
                    company_data = db_data
            
            # Fetch fresh data if needed
            if need_fresh_data:
                company_data = st.session_state.data_fetcher.fetch_company_data(selected_company)
                if company_data is not None and not company_data.empty:
                    # Store in database
                    st.session_state.db_manager.store_stock_data(company_symbol, selected_company, company_data)
            
            if company_data is not None and not company_data.empty:
                st.session_state.companies_data[selected_company] = company_data
                
                # Current price display
                current_price = company_data['close'].iloc[-1]
                prev_price = company_data['close'].iloc[-2] if len(company_data) > 1 else current_price
                change = current_price - prev_price
                change_pct = (change / prev_price) * 100 if prev_price != 0 else 0
                
                # Display current metrics
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                
                with metric_col1:
                    st.metric(
                        "Current Price",
                        format_currency(current_price),
                        delta=f"{change:+.2f} ({change_pct:+.2f}%)"
                    )
                
                with metric_col2:
                    st.metric("High", format_currency(company_data['high'].iloc[-1]))
                
                with metric_col3:
                    st.metric("Low", format_currency(company_data['low'].iloc[-1]))
                
                # Historical chart
                st.subheader("📈 Live Price Movement")
                historical_chart = st.session_state.visualizer.create_price_chart(
                    company_data, f"{selected_company} - Live Data"
                )
                st.plotly_chart(historical_chart, use_container_width=True)
                
                # Forecasting
                st.subheader("🔮 Price Forecast")
                
                with st.spinner("Generating forecast..."):
                    try:
                        forecast_data = st.session_state.forecaster.forecast_stock(
                            company_data, days_ahead=days_ahead
                        )
                        
                        if forecast_data is not None:
                            # Display forecast metrics
                            forecast_price = forecast_data['yhat'].iloc[-1]
                            forecast_change = forecast_price - current_price
                            forecast_change_pct = (forecast_change / current_price) * 100
                            
                            forecast_col1, forecast_col2 = st.columns(2)
                            
                            with forecast_col1:
                                period_text = {
                                    0: "End of Day",
                                    1: "Tomorrow",
                                    days_ahead: f"{days_ahead} Days Ahead" if days_ahead > 1 else "Tomorrow"
                                }.get(days_ahead, f"{days_ahead} Days Ahead")
                                
                                st.metric(
                                    f"Forecasted Price ({period_text})",
                                    format_currency(forecast_price),
                                    delta=f"{forecast_change:+.2f} ({forecast_change_pct:+.2f}%)"
                                )
                            
                            with forecast_col2:
                                confidence_lower = forecast_data['yhat_lower'].iloc[-1]
                                confidence_upper = forecast_data['yhat_upper'].iloc[-1]
                                st.metric(
                                    "Confidence Range",  
                                    f"{format_currency(confidence_lower)} - {format_currency(confidence_upper)}"
                                )
                            
                            # Forecast chart
                            forecast_chart = st.session_state.visualizer.create_forecast_chart(
                                company_data, forecast_data, f"{selected_company} Forecast"
                            )
                            st.plotly_chart(forecast_chart, use_container_width=True)
                            
                        else:
                            st.error("Unable to generate forecast. Insufficient data.")
                            
                    except Exception as e:
                        st.error(f"Forecasting error: {str(e)}")
                
            else:
                st.error(f"Unable to fetch {selected_company} data. Please try again later.")
                
        except Exception as e:
            st.error(f"Data fetching error: {str(e)}")

def display_database_overview():
    """Display database overview and management tools"""
    
    st.subheader("🗄️ Database Overview")
    st.markdown("Manage and view stored stock data, forecasts, and system information.")
    
    # Database statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Database Status", "Connected ✅")
    
    with col2:
        # Get market summary from database
        try:
            market_data = st.session_state.db_manager.get_market_summary_from_db()
            st.metric("Stored Symbols", len(market_data))
        except Exception as e:
            st.metric("Stored Symbols", "Error")
    
    with col3:
        st.metric("Data Source", "PostgreSQL")
    
    st.markdown("---")
    
    # Data management options
    tab1, tab2, tab3 = st.tabs(["📊 Stored Data", "🔮 Forecast History", "⚙️ Settings"])
    
    with tab1:
        st.subheader("Historical Stock Data")
        
        # Show available symbols
        try:
            market_data = st.session_state.db_manager.get_market_summary_from_db()
            if market_data:
                df_market = pd.DataFrame([
                    {
                        'Symbol': symbol,
                        'Latest Price': f"PKR {data['current_price']:,.2f}",
                        'Last Updated': data['date'].strftime('%Y-%m-%d %H:%M'),
                        'Volume': f"{data['volume']:,.0f}"
                    }
                    for symbol, data in market_data.items()
                ])
                st.dataframe(df_market, use_container_width=True)
            else:
                st.info("No historical data found in database. Start by fetching some stock data.")
        except Exception as e:
            st.error(f"Error retrieving market data: {str(e)}")
    
    with tab2:
        st.subheader("Forecast History")
        
        # Select symbol for forecast history
        try:
            market_data = st.session_state.db_manager.get_market_summary_from_db()
            if market_data:
                selected_symbol = st.selectbox(
                    "Select Symbol for Forecast History",
                    list(market_data.keys())
                )
                
                if st.button("Load Forecast History"):
                    forecast_history = st.session_state.db_manager.get_forecast_history(selected_symbol, days=30)
                    if forecast_history is not None and not forecast_history.empty:
                        st.dataframe(forecast_history, use_container_width=True)
                    else:
                        st.info(f"No forecast history found for {selected_symbol}")
            else:
                st.info("No symbols available. Generate some forecasts first.")
        except Exception as e:
            st.error(f"Error retrieving forecast history: {str(e)}")
    
    with tab3:
        st.subheader("Database Settings")
        
        # Database connection info
        st.write("**Connection Information:**")
        try:
            import os
            db_host = os.getenv('PGHOST', 'Not set')
            db_port = os.getenv('PGPORT', 'Not set')
            db_name = os.getenv('PGDATABASE', 'Not set')
            
            st.code(f"""
Host: {db_host}
Port: {db_port}
Database: {db_name}
            """)
        except Exception as e:
            st.error(f"Error retrieving connection info: {str(e)}")
        
        # Data management actions
        st.write("**Data Management:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Clear Old Data", help="Remove data older than 30 days"):
                # This would implement data cleanup
                st.info("Data cleanup feature - implementation needed")
        
        with col2:
            if st.button("📊 Database Stats", help="Show detailed database statistics"):
                # This would show detailed stats
                st.info("Database statistics feature - implementation needed")

if __name__ == "__main__":
    main()
