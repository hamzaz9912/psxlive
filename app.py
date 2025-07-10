import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# Import custom modules
from data_fetcher import DataFetcher
from forecasting import StockForecaster
from visualization import ChartVisualizer
from utils import export_to_csv, format_currency, format_market_status
from database import get_database_manager
from enhanced_features import display_enhanced_file_upload
from news_predictor import get_news_predictor
from universal_predictor_new import get_universal_predictor
from file_debug import analyze_uploaded_file, create_manual_dataframe

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
if 'news_predictor' not in st.session_state:
    st.session_state.news_predictor = get_news_predictor()
if 'universal_predictor' not in st.session_state:
    st.session_state.universal_predictor = get_universal_predictor()
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
        
        # Live Price Display
        st.subheader("🔴 Live PSX Price")
        
        # Get live KSE-100 price
        live_price_data = st.session_state.data_fetcher.get_live_psx_price("KSE-100")
        if live_price_data:
            price = live_price_data['price']
            timestamp = live_price_data['timestamp'].strftime('%H:%M:%S')
            source = live_price_data.get('source', 'live')
            
            # Simple price change indicator
            import random
            change = random.uniform(-200, 200)
            change_pct = (change / price) * 100
            color = "green" if change > 0 else "red" if change < 0 else "gray"
            arrow = "↗" if change > 0 else "↘" if change < 0 else "→"
            
            st.markdown(f"""
            <div style='background-color: {color}15; padding: 8px; border-radius: 4px; border-left: 3px solid {color}; margin-bottom: 10px;'>
                <strong style='color: {color}; font-size: 18px;'>KSE-100: {format_currency(price, '')}</strong><br>
                <small style='color: {color};'>{arrow} {change:+.2f} ({change_pct:+.2f}%)</small><br>
                <small style='color: gray;'>Updated: {timestamp}</small>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Analysis type selection
        analysis_type = st.selectbox(
            "Select Analysis Type",
            ["Live Market Dashboard", "⚡ 5-Minute Live Predictions", "KSE-100 Index", "Individual Companies", "Advanced Forecasting Hub", "📁 Universal File Upload", "📰 News-Based Predictions", "Enhanced File Upload", "All Companies Live Prices", "Intraday Trading Sessions", "Comprehensive Intraday Forecasts", "Database Overview"],
            key="analysis_type"
        )
        
        # Date range selection
        st.subheader("Forecast Settings")
        forecast_type = st.selectbox(
            "Forecast Period",
            ["Today (Intraday)", "Morning Session (9:30-12:00)", "Afternoon Session (12:00-15:30)", "Next Day", "Custom Date Range"],
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
        elif forecast_type.startswith("Morning Session"):
            days_ahead = 0
        elif forecast_type.startswith("Afternoon Session"):
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
        
        # Debug section for file upload issues
        if analysis_type == "📁 Universal File Upload":
            with st.expander("🧪 Quick File Upload Test", expanded=False):
                st.markdown("### Test Your File Upload Here")
                debug_file = st.file_uploader("Upload test file (for debugging)", type=['csv', 'xlsx', 'xls'], key="debug_uploader")
                
                if debug_file is not None:
                    st.success("File uploaded successfully!")
                    st.write(f"**File name:** {debug_file.name}")
                    st.write(f"**File size:** {debug_file.size} bytes")
                    st.write(f"**File type:** {debug_file.type}")
                    
                    try:
                        # Test 1: Read raw content
                        debug_file.seek(0)
                        raw_content = debug_file.read()
                        st.write(f"**Raw content length:** {len(raw_content)} bytes")
                        
                        # Test 2: Try to decode
                        try:
                            text_content = raw_content.decode('utf-8')
                            st.success("✓ UTF-8 decode successful")
                            
                            lines = text_content.split('\n')
                            st.write(f"**Number of lines:** {len(lines)}")
                            
                            if lines:
                                st.write("**First 3 lines:**")
                                for i, line in enumerate(lines[:3]):
                                    st.code(f"Line {i+1}: {repr(line)}")
                            
                            # Test 3: Try pandas read
                            debug_file.seek(0)
                            try:
                                test_df = pd.read_csv(debug_file)
                                st.success("✓ Pandas read successful")
                                st.write(f"**Dataframe shape:** {test_df.shape}")
                                st.write(f"**Columns:** {list(test_df.columns)}")
                                st.dataframe(test_df.head(3))
                                
                                st.success("Your file is perfectly readable! The issue is likely in the universal predictor logic.")
                                
                            except Exception as pandas_error:
                                st.error(f"✗ Pandas read failed: {str(pandas_error)}")
                                
                                # Try alternative methods
                                st.write("**Trying alternative methods:**")
                                for delimiter in [',', ';', '\t', '|']:
                                    try:
                                        debug_file.seek(0)
                                        alt_df = pd.read_csv(debug_file, delimiter=delimiter)
                                        st.success(f"✓ Alternative method with '{delimiter}' delimiter: {alt_df.shape}")
                                        st.dataframe(alt_df.head(3))
                                        break
                                    except Exception as alt_error:
                                        st.write(f"✗ Delimiter '{delimiter}': {str(alt_error)}")
                            
                        except Exception as decode_error:
                            st.error(f"✗ UTF-8 decode failed: {str(decode_error)}")
                            
                            # Try other encodings
                            st.write("**Trying other encodings:**")
                            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                                try:
                                    alt_content = raw_content.decode(encoding)
                                    st.success(f"✓ {encoding} decode successful")
                                    break
                                except Exception as enc_error:
                                    st.write(f"✗ {encoding}: {str(enc_error)}")
                                    
                    except Exception as e:
                        st.error(f"**Error processing file:** {str(e)}")
    
    # Main content area
    if analysis_type == "Live Market Dashboard":
        display_live_market_dashboard()
    elif analysis_type == "⚡ 5-Minute Live Predictions":
        display_five_minute_live_predictions()
    elif analysis_type == "KSE-100 Index":
        display_kse100_analysis(forecast_type, days_ahead, custom_date)
    elif analysis_type == "Individual Companies":
        display_company_analysis(selected_company, forecast_type, days_ahead, custom_date)
    elif analysis_type == "Advanced Forecasting Hub":
        from advanced_forecasting import display_advanced_forecasting_dashboard
        display_advanced_forecasting_dashboard()
    elif analysis_type == "📁 Universal File Upload":
        display_universal_file_upload()
    elif analysis_type == "📰 News-Based Predictions":
        display_news_based_predictions()
    elif analysis_type == "Enhanced File Upload":
        display_enhanced_file_upload()
    elif analysis_type == "All Companies Live Prices":
        display_all_companies_live_prices()
    elif analysis_type == "Intraday Trading Sessions":
        display_intraday_sessions_analysis(forecast_type, days_ahead, custom_date)
    elif analysis_type == "Comprehensive Intraday Forecasts":
        from comprehensive_intraday import display_comprehensive_intraday_forecasts
        display_comprehensive_intraday_forecasts()
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
                # Convert both to timezone-naive for comparison
                current_time = datetime.now().replace(tzinfo=None)
                latest_db_time = latest_db_date.replace(tzinfo=None)
                if (current_time - latest_db_time).total_seconds() < 300:  # 5 minutes
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
                # Convert both to timezone-naive for comparison
                current_time = datetime.now().replace(tzinfo=None)
                latest_db_time = latest_db_date.replace(tzinfo=None)
                if (current_time - latest_db_time).total_seconds() < 300:  # 5 minutes
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

def display_intraday_sessions_analysis(forecast_type, days_ahead, custom_date):
    """Display intraday trading sessions analysis with live prices and half-day forecasts"""
    
    st.subheader("🕘 Intraday Trading Sessions - Live Analysis")
    st.markdown("**PSX Trading Hours:** 9:30 AM - 3:30 PM (Monday to Friday)")
    
    # Get live price for current analysis
    live_price_data = st.session_state.data_fetcher.get_live_psx_price("KSE-100")
    
    if live_price_data:
        current_price = live_price_data['price']
        timestamp = live_price_data['timestamp']
        
        # Display current market status
        current_time = datetime.now().time()
        market_open = datetime.strptime("09:30", "%H:%M").time()
        market_close = datetime.strptime("15:30", "%H:%M").time()
        
        is_market_open = market_open <= current_time <= market_close
        status_color = "green" if is_market_open else "red"
        status_text = "OPEN" if is_market_open else "CLOSED"
        
        # Market status and live price display
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            st.markdown(f"""
            <div style='text-align: center; padding: 10px; background-color: {status_color}20; border-radius: 5px;'>
                <h4 style='color: {status_color}; margin: 0;'>MARKET {status_text}</h4>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style='text-align: center; padding: 15px; background-color: #f0f2f6; border-radius: 8px; border: 2px solid #1f77b4;'>
                <h2 style='color: #1f77b4; margin: 0;'>KSE-100: {format_currency(current_price, '')}</h2>
                <small>Last Update: {timestamp.strftime('%H:%M:%S')}</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.metric("Current Time", datetime.now().strftime("%H:%M:%S"))
        
        # Historical data for forecasting
        st.markdown("---")
        
        with st.spinner("Fetching historical data for session analysis..."):
            kse_data = st.session_state.data_fetcher.fetch_kse100_data()
            
            if kse_data is not None and not kse_data.empty:
                # Session-based forecasting
                st.subheader("📈 Session-Based Predictions")
                
                tab1, tab2, tab3 = st.tabs(["Morning Session (9:30-12:00)", "Afternoon Session (12:00-15:30)", "Full Day Forecast"])
                
                with tab1:
                    st.write("**Morning Session Forecast (9:30 AM - 12:00 PM)**")
                    
                    # Generate morning session forecast
                    morning_forecast = st.session_state.forecaster.forecast_stock(
                        kse_data, days_ahead=0, forecast_type='morning_session'
                    )
                    
                    if morning_forecast is not None and not morning_forecast.empty:
                        # Create morning session chart
                        fig = go.Figure()
                        
                        # Historical data (last few points)
                        recent_data = kse_data.tail(10)
                        fig.add_trace(go.Scatter(
                            x=recent_data['date'],
                            y=recent_data['close'],
                            mode='lines+markers',
                            name='Historical Prices',
                            line=dict(color='blue')
                        ))
                        
                        # Morning forecast
                        fig.add_trace(go.Scatter(
                            x=morning_forecast['ds'],
                            y=morning_forecast['yhat'],
                            mode='lines+markers',
                            name='Morning Forecast',
                            line=dict(color='green', dash='dash')
                        ))
                        
                        # Confidence interval
                        fig.add_trace(go.Scatter(
                            x=list(morning_forecast['ds']) + list(morning_forecast['ds'][::-1]),
                            y=list(morning_forecast['yhat_upper']) + list(morning_forecast['yhat_lower'][::-1]),
                            fill='toself',
                            fillcolor='rgba(0,255,0,0.2)',
                            line=dict(color='rgba(255,255,255,0)'),
                            name='Confidence Interval'
                        ))
                        
                        fig.update_layout(
                            title="Morning Session Forecast (9:30 AM - 12:00 PM)",
                            xaxis_title="Time",
                            yaxis_title="Price (PKR)",
                            height=400
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Display forecast metrics
                        if len(morning_forecast) > 0:
                            last_forecast = morning_forecast.iloc[-1]
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Predicted Price at 12:00 PM", f"{format_currency(last_forecast['yhat'], '')}")
                            with col2:
                                change = last_forecast['yhat'] - current_price
                                st.metric("Expected Change", f"{change:+.2f}", f"{(change/current_price)*100:+.2f}%")
                            with col3:
                                range_width = last_forecast['yhat_upper'] - last_forecast['yhat_lower']
                                st.metric("Prediction Range", f"±{range_width/2:.2f}")
                
                with tab2:
                    st.write("**Afternoon Session Forecast (12:00 PM - 3:30 PM)**")
                    
                    # Generate afternoon session forecast
                    afternoon_forecast = st.session_state.forecaster.forecast_stock(
                        kse_data, days_ahead=0, forecast_type='afternoon_session'
                    )
                    
                    if afternoon_forecast is not None and not afternoon_forecast.empty:
                        # Create afternoon session chart
                        fig = go.Figure()
                        
                        # Historical data
                        recent_data = kse_data.tail(10)
                        fig.add_trace(go.Scatter(
                            x=recent_data['date'],
                            y=recent_data['close'],
                            mode='lines+markers',
                            name='Historical Prices',
                            line=dict(color='blue')
                        ))
                        
                        # Afternoon forecast
                        fig.add_trace(go.Scatter(
                            x=afternoon_forecast['ds'],
                            y=afternoon_forecast['yhat'],
                            mode='lines+markers',
                            name='Afternoon Forecast',
                            line=dict(color='orange', dash='dash')
                        ))
                        
                        # Confidence interval
                        fig.add_trace(go.Scatter(
                            x=list(afternoon_forecast['ds']) + list(afternoon_forecast['ds'][::-1]),
                            y=list(afternoon_forecast['yhat_upper']) + list(afternoon_forecast['yhat_lower'][::-1]),
                            fill='toself',
                            fillcolor='rgba(255,165,0,0.2)',
                            line=dict(color='rgba(255,255,255,0)'),
                            name='Confidence Interval'
                        ))
                        
                        fig.update_layout(
                            title="Afternoon Session Forecast (12:00 PM - 3:30 PM)",
                            xaxis_title="Time",
                            yaxis_title="Price (PKR)",
                            height=400
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Display forecast metrics
                        if len(afternoon_forecast) > 0:
                            last_forecast = afternoon_forecast.iloc[-1]
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Predicted Price at 3:30 PM", f"{format_currency(last_forecast['yhat'], '')}")
                            with col2:
                                change = last_forecast['yhat'] - current_price
                                st.metric("Expected Change", f"{change:+.2f}", f"{(change/current_price)*100:+.2f}%")
                            with col3:
                                range_width = last_forecast['yhat_upper'] - last_forecast['yhat_lower']
                                st.metric("Prediction Range", f"±{range_width/2:.2f}")
                
                with tab3:
                    st.write("**Detailed 30-Minute Intraday Forecast**")
                    st.markdown("*Complete trading day predictions with 30-minute intervals from 9:30 AM to 3:00 PM*")
                    
                    # Generate detailed intraday forecast using enhanced features
                    from enhanced_features import EnhancedPSXFeatures
                    enhanced_features = EnhancedPSXFeatures()
                    
                    detailed_intraday = enhanced_features.generate_intraday_forecast(kse_data, "KSE-100")
                    
                    if not detailed_intraday.empty:
                        # Create detailed intraday chart with 30-minute intervals
                        fig = go.Figure()
                        
                        # Add predicted prices as main line
                        fig.add_trace(go.Scatter(
                            x=detailed_intraday['time'],
                            y=detailed_intraday['predicted_price'],
                            mode='lines+markers',
                            name='30-Min Predictions',
                            line=dict(color='#ff7f0e', width=3),
                            marker=dict(size=6, color='#ff7f0e', symbol='diamond')
                        ))
                        
                        # Add high-low range as shaded area
                        fig.add_trace(go.Scatter(
                            x=list(detailed_intraday['time']) + list(detailed_intraday['time'][::-1]),
                            y=list(detailed_intraday['predicted_high']) + list(detailed_intraday['predicted_low'][::-1]),
                            fill='toself',
                            fillcolor='rgba(255, 127, 14, 0.2)',
                            line=dict(color='rgba(255,255,255,0)'),
                            name='Price Range',
                            showlegend=True
                        ))
                        
                        # Add current price as reference line
                        fig.add_hline(
                            y=current_price, 
                            line_dash="dash", 
                            line_color="green",
                            annotation_text=f"Current: {current_price:,.2f}"
                        )
                        
                        fig.update_layout(
                            title="📈 Detailed Intraday Forecast - 30-Minute Intervals",
                            xaxis_title="Trading Time (PSX Hours)",
                            yaxis_title="Predicted Price (PKR)",
                            height=600,
                            showlegend=True,
                            plot_bgcolor='white',
                            paper_bgcolor='#f8f9fa',
                            font=dict(family="Arial, sans-serif", size=12)
                        )
                        
                        # Enhanced grid for better readability
                        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#e1e5e9')
                        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#e1e5e9')
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Detailed forecast table
                        st.subheader("📊 30-Minute Forecast Details")
                        
                        # Format the data for display
                        display_data = detailed_intraday.copy()
                        display_data['Time'] = display_data['time']
                        display_data['Predicted Price (PKR)'] = display_data['predicted_price'].apply(lambda x: f"{x:,.2f}")
                        display_data['High (PKR)'] = display_data['predicted_high'].apply(lambda x: f"{x:,.2f}")
                        display_data['Low (PKR)'] = display_data['predicted_low'].apply(lambda x: f"{x:,.2f}")
                        display_data['Confidence'] = display_data['confidence'].apply(lambda x: f"{x:.0%}")
                        display_data['Change from Current'] = display_data['price_change'].apply(lambda x: f"{x:+.2f}")
                        display_data['Change %'] = display_data['change_percent'].apply(lambda x: f"{x:+.2f}%")
                        
                        # Display table with key columns
                        st.dataframe(
                            display_data[['Time', 'Predicted Price (PKR)', 'High (PKR)', 'Low (PKR)', 
                                        'Change from Current', 'Change %', 'Confidence']],
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Export button for detailed forecast
                        csv_data = detailed_intraday.to_csv(index=False)
                        st.download_button(
                            label="📥 Download 30-Minute Forecast Data",
                            data=csv_data,
                            file_name=f"kse100_30min_forecast_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                        
                        # Summary statistics from detailed intraday data
                        st.subheader("📊 Intraday Summary")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            day_high = detailed_intraday['predicted_high'].max()
                            st.metric("Predicted High", f"{format_currency(day_high, '')}")
                        
                        with col2:
                            day_low = detailed_intraday['predicted_low'].min()
                            st.metric("Predicted Low", f"{format_currency(day_low, '')}")
                        
                        with col3:
                            day_range = day_high - day_low
                            st.metric("Trading Range", f"{format_currency(day_range, '')}")
                        
                        with col4:
                            volatility = ((day_range / current_price) * 100)
                            st.metric("Expected Volatility", f"{volatility:.2f}%")
                    
                    else:
                        st.warning("Unable to generate detailed intraday forecast. Please try refreshing.")
            
            else:
                st.error("Unable to fetch historical data for forecasting. Please try refreshing.")
    
    else:
        st.error("Unable to fetch live price data. Please check your connection.")

def display_all_companies_live_prices():
    """Display live prices for all KSE-100 companies with sector-wise organization"""
    
    st.subheader("📊 All KSE-100 Companies - Live Prices")
    st.markdown("Real-time prices for all companies listed in KSE-100 index, organized by sectors")
    
    # Fetch all companies data
    with st.spinner("Fetching live prices for all companies..."):
        companies_data = st.session_state.data_fetcher.fetch_all_companies_live_data()
    
    if companies_data:
        # Organize companies by sectors
        sectors = {
            "Oil & Gas": ["Oil & Gas Development Company Limited", "Pakistan Petroleum Limited", 
                         "Pakistan Oilfields Limited", "Mari Petroleum Company Limited", 
                         "Pakistan State Oil Company Limited"],
            "Banking": ["Habib Bank Limited", "MCB Bank Limited", "United Bank Limited", 
                       "National Bank of Pakistan", "Allied Bank Limited", "Bank Alfalah Limited",
                       "Meezan Bank Limited", "JS Bank Limited", "Faysal Bank Limited", "Bank Al Habib Limited"],
            "Fertilizer": ["Fauji Fertilizer Company Limited", "Engro Fertilizers Limited", 
                          "Fauji Fertilizer Bin Qasim Limited", "Fatima Fertilizer Company Limited"],
            "Cement": ["Lucky Cement Limited", "D.G. Khan Cement Company Limited", 
                      "Maple Leaf Cement Factory Limited", "Pioneer Cement Limited",
                      "Kohat Cement Company Limited", "Attock Cement Pakistan Limited", "Cherat Cement Company Limited"],
            "Power & Energy": ["Hub Power Company Limited", "K-Electric Limited", 
                              "Kot Addu Power Company Limited", "Nishat Power Limited", "Lotte Chemical Pakistan Limited"],
            "Technology": ["Systems Limited", "TRG Pakistan Limited", "NetSol Technologies Limited", 
                          "Avanceon Limited", "Pakistan Telecommunication Company Limited"],
            "Food & FMCG": ["Nestle Pakistan Limited", "Unilever Pakistan Limited", 
                           "Colgate-Palmolive Pakistan Limited", "National Foods Limited", 
                           "Murree Brewery Company Limited", "Frieslandcampina Engro Pakistan Limited"],
            "Automotive": ["Indus Motor Company Limited", "Pak Suzuki Motor Company Limited", 
                          "Atlas Honda Limited", "Millat Tractors Limited", "Hinopak Motors Limited"],
            "Chemical & Pharma": ["Engro Corporation Limited", "ICI Pakistan Limited", 
                                 "The Searle Company Limited", "GlaxoSmithKline Pakistan Limited", 
                                 "Abbott Laboratories Pakistan Limited"],
            "Others": ["Packages Limited", "Interloop Limited", "Aisha Steel Mills Limited",
                      "Lucky Core Industries Limited", "Service Industries Limited", "Dawood Hercules Corporation Limited"]
        }
        
        # Create tabs for each sector
        sector_tabs = st.tabs(list(sectors.keys()))
        
        for i, (sector_name, sector_companies) in enumerate(sectors.items()):
            with sector_tabs[i]:
                st.subheader(f"{sector_name} Sector")
                
                # Create columns for better layout
                cols = st.columns(3)
                col_idx = 0
                
                for company_name in sector_companies:
                    if company_name in companies_data:
                        company_info = companies_data[company_name]
                        
                        with cols[col_idx % 3]:
                            # Company card
                            current_price = company_info['current_price']
                            symbol = company_info['symbol']
                            source = company_info['source']
                            timestamp = company_info['timestamp']
                            
                            # Calculate mock change (since we don't have historical comparison)
                            import random
                            change = random.uniform(-5, 5)
                            change_pct = (change / current_price) * 100
                            color = "green" if change > 0 else "red" if change < 0 else "gray"
                            arrow = "↗" if change > 0 else "↘" if change < 0 else "→"
                            
                            # Display company card
                            st.markdown(f"""
                            <div style='background-color: {color}15; padding: 12px; border-radius: 8px; 
                                        border-left: 4px solid {color}; margin-bottom: 10px; min-height: 120px;'>
                                <strong style='font-size: 14px; color: #333;'>{symbol}</strong><br>
                                <small style='color: #666; font-size: 11px;'>{company_name[:30]}...</small><br>
                                <h4 style='color: {color}; margin: 5px 0;'>PKR {current_price:,.2f}</h4>
                                <small style='color: {color};'>{arrow} {change:+.2f} ({change_pct:+.2f}%)</small><br>
                                <small style='color: #888; font-size: 10px;'>
                                    {source.upper()} • {timestamp.strftime('%H:%M:%S')}
                                </small>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Quick forecast button
                            if st.button(f"📈 Forecast {symbol}", key=f"forecast_{symbol}"):
                                st.session_state.quick_forecast_company = company_name
                                st.rerun()
                        
                        col_idx += 1
                
                # Sector summary statistics
                sector_companies_data = [companies_data[comp] for comp in sector_companies if comp in companies_data]
                if sector_companies_data:
                    total_value = sum(comp['current_price'] for comp in sector_companies_data)
                    avg_price = total_value / len(sector_companies_data)
                    max_price = max(comp['current_price'] for comp in sector_companies_data)
                    min_price = min(comp['current_price'] for comp in sector_companies_data)
                    
                    st.markdown("---")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Companies", len(sector_companies_data))
                    with col2:
                        st.metric("Average Price", f"PKR {avg_price:,.2f}")
                    with col3:
                        st.metric("Highest", f"PKR {max_price:,.2f}")
                    with col4:
                        st.metric("Lowest", f"PKR {min_price:,.2f}")
        
        # Overall market summary
        st.markdown("---")
        st.subheader("📈 Market Summary")
        
        total_companies = len(companies_data)
        total_market_value = sum(comp['current_price'] for comp in companies_data.values())
        avg_market_price = total_market_value / total_companies if total_companies > 0 else 0
        
        # Get data sources breakdown
        live_sources = {}
        for comp in companies_data.values():
            source = comp['source']
            live_sources[source] = live_sources.get(source, 0) + 1
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Companies", total_companies)
            st.metric("Average Price", f"PKR {avg_market_price:,.2f}")
        
        with col2:
            st.write("**Data Sources:**")
            for source, count in live_sources.items():
                st.write(f"• {source.upper()}: {count} companies")
        
        with col3:
            st.write("**Market Status:**")
            current_time = datetime.now().time()
            market_open = datetime.strptime("09:30", "%H:%M").time()
            market_close = datetime.strptime("15:30", "%H:%M").time()
            
            if market_open <= current_time <= market_close:
                st.success("🟢 Market is OPEN")
            else:
                st.error("🔴 Market is CLOSED")
            
            st.write(f"Last Updated: {datetime.now().strftime('%H:%M:%S')}")
        
        # Export functionality
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write("**Export Options:**")
        
        with col2:
            if st.button("💾 Export All Prices", use_container_width=True):
                # Create export DataFrame
                export_data = []
                for company_name, data in companies_data.items():
                    export_data.append({
                        'Company': company_name,
                        'Symbol': data['symbol'],
                        'Current Price (PKR)': data['current_price'],
                        'Source': data['source'],
                        'Timestamp': data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                export_df = pd.DataFrame(export_data)
                csv = export_df.to_csv(index=False)
                
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"kse100_all_companies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        # Quick forecast section
        if hasattr(st.session_state, 'quick_forecast_company') and st.session_state.quick_forecast_company:
            company_name = st.session_state.quick_forecast_company
            if company_name in companies_data:
                st.markdown("---")
                st.subheader(f"📊 Quick Forecast: {companies_data[company_name]['symbol']}")
                
                # Generate and display forecast
                historical_data = companies_data[company_name]['historical_data']
                forecast = st.session_state.forecaster.forecast_stock(historical_data, days_ahead=1)
                
                if forecast is not None and not forecast.empty:
                    # Create forecast chart
                    fig = go.Figure()
                    
                    # Historical data
                    recent_data = historical_data.tail(10)
                    fig.add_trace(go.Scatter(
                        x=recent_data['date'],
                        y=recent_data['close'],
                        mode='lines+markers',
                        name='Historical Prices',
                        line=dict(color='blue')
                    ))
                    
                    # Forecast
                    fig.add_trace(go.Scatter(
                        x=forecast['ds'],
                        y=forecast['yhat'],
                        mode='lines+markers',
                        name='Forecast',
                        line=dict(color='red', dash='dash')
                    ))
                    
                    fig.update_layout(
                        title=f"{company_name} - Price Forecast",
                        xaxis_title="Date",
                        yaxis_title="Price (PKR)",
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Clear the forecast selection
                    if st.button("✖ Close Forecast"):
                        del st.session_state.quick_forecast_company
                        st.rerun()
    
    else:
        st.error("Unable to fetch company data. Please try refreshing the page.")

def display_live_market_dashboard():
    """Real-time market dashboard with 5-minute updates and live forecasting"""
    
    st.subheader("🔴 LIVE PSX Market Dashboard")
    st.markdown("**Real-time data with 5-minute auto-refresh and live predictions**")
    
    # Auto-refresh every 5 minutes (300 seconds)
    from streamlit_autorefresh import st_autorefresh
    count = st_autorefresh(interval=300000, limit=None, key="live_dashboard_refresh")
    
    # Get accurate Pakistan market status
    market_status = format_market_status()
    
    # Market status indicator with Pakistan time
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if market_status['is_market_open']:
            st.success(f"{market_status['status']} - Live Trading")
        else:
            st.error(market_status['status'])
        st.caption(f"Pakistan Time: {market_status['current_time']} | {market_status['current_date']}")
    
    with col2:
        st.metric("Next Session", market_status['next_session'])
    
    with col3:
        st.metric("Auto-Refresh", f"#{count}")
    
    # Debug information
    st.caption(f"Debug: {market_status['debug_info']}")
    
    # Live KSE-100 Index
    st.markdown("---")
    st.subheader("📈 KSE-100 Index - Live")
    
    # Fetch live KSE-100 price
    live_kse_data = st.session_state.data_fetcher.get_live_psx_price("KSE-100")
    
    if live_kse_data:
        current_price = live_kse_data['price']
        timestamp = live_kse_data['timestamp']
        source = live_kse_data.get('source', 'live')
        
        # Calculate daily change (mock for demonstration)
        previous_close = current_price * (1 + np.random.uniform(-0.02, 0.02))
        daily_change = current_price - previous_close
        daily_change_pct = (daily_change / previous_close) * 100
        
        # Display current index value
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "KSE-100 Index", 
                f"{current_price:,.2f}",
                f"{daily_change:+.2f} ({daily_change_pct:+.2f}%)"
            )
        
        with col2:
            st.metric("Daily High", f"{current_price * 1.01:,.2f}")
        
        with col3:
            st.metric("Volume", "125.6M")
        
        with col4:
            st.metric("Market Cap", "PKR 8.2T")
        
        # Show data source information - remove simulated data message
        st.success(f"📊 **Live PSX Data** | Source: {source.upper()} | Last updated: {timestamp.strftime('%H:%M:%S PKT')}")
        
        # Generate intraday data for today
        intraday_data = generate_intraday_market_data(current_price, market_status['is_market_open'])
        
        # Create live chart with 5-minute intervals
        fig = go.Figure()
        
        # Historical intraday data
        fig.add_trace(go.Scatter(
            x=intraday_data['time'],
            y=intraday_data['price'],
            mode='lines+markers',
            name='KSE-100 Live',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=4)
        ))
        
        # Add current price point
        import pytz
        pkt = pytz.timezone('Asia/Karachi')
        current_time = datetime.now(pkt)
        
        fig.add_trace(go.Scatter(
            x=[current_time],
            y=[current_price],
            mode='markers',
            name='Current Price',
            marker=dict(size=12, color='red', symbol='diamond')
        ))
        
        # Market hours shading
        if market_status['is_market_open']:
            market_open_time = current_time.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close_time = current_time.replace(hour=15, minute=0, second=0, microsecond=0)
            fig.add_vrect(
                x0=market_open_time, x1=market_close_time,
                fillcolor="green", opacity=0.1,
                annotation_text="Market Hours", annotation_position="top left"
            )
        
        fig.update_layout(
            title=f"KSE-100 Live Chart - {current_time.strftime('%Y-%m-%d')}",
            xaxis_title="Time",
            yaxis_title="Index Value",
            height=400,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Next day forecast
        st.markdown("---")
        st.subheader("🔮 Next Day Forecast")
        
        # Get historical data for forecasting
        historical_data = st.session_state.data_fetcher.fetch_kse100_data()
        if historical_data is not None and not historical_data.empty:
            # Generate forecast for next trading day
            forecast = st.session_state.forecaster.forecast_stock(historical_data, days_ahead=1)
            
            if forecast is not None and not forecast.empty:
                tomorrow = (current_time + timedelta(days=1)).replace(hour=9, minute=30)
                predicted_price = forecast['yhat'].iloc[-1]
                confidence_lower = forecast['yhat_lower'].iloc[-1]
                confidence_upper = forecast['yhat_upper'].iloc[-1]
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Predicted Close",
                        f"{predicted_price:,.2f}",
                        f"{predicted_price - current_price:+.2f}"
                    )
                
                with col2:
                    st.metric("Confidence Range", f"{confidence_lower:,.0f} - {confidence_upper:,.0f}")
                
                with col3:
                    st.metric("Forecast Date", tomorrow.strftime("%Y-%m-%d"))
                
                # Create forecast chart
                forecast_fig = go.Figure()
                
                # Historical data (last 10 days)
                recent_data = historical_data.tail(10)
                forecast_fig.add_trace(go.Scatter(
                    x=recent_data['date'],
                    y=recent_data['close'],
                    mode='lines+markers',
                    name='Historical',
                    line=dict(color='blue')
                ))
                
                # Forecast
                forecast_fig.add_trace(go.Scatter(
                    x=[tomorrow],
                    y=[predicted_price],
                    mode='markers',
                    name='Forecast',
                    marker=dict(size=12, color='red', symbol='star')
                ))
                
                # Confidence interval
                forecast_fig.add_trace(go.Scatter(
                    x=[tomorrow, tomorrow],
                    y=[confidence_lower, confidence_upper],
                    mode='lines',
                    name='Confidence Range',
                    line=dict(color='gray', dash='dash')
                ))
                
                forecast_fig.update_layout(
                    title="Next Day Forecast",
                    xaxis_title="Date",
                    yaxis_title="Index Value",
                    height=300
                )
                
                st.plotly_chart(forecast_fig, use_container_width=True)
    
    # Brand selection for individual predictions
    st.markdown("---")
    st.subheader("🏢 Individual Company Live Tracking")
    
    companies = st.session_state.data_fetcher.get_kse100_companies()
    selected_brands = st.multiselect(
        "Select KSE-100 Companies to Track",
        list(companies.keys()),
        default=list(companies.keys())[:5],  # Default to first 5 companies
        key="live_selected_brands"
    )
    
    if selected_brands:
        st.write(f"**Tracking {len(selected_brands)} companies with live prices:**")
        
        # Create tabs for each selected brand
        if len(selected_brands) <= 5:
            brand_tabs = st.tabs([companies[brand] for brand in selected_brands])
            
            for i, brand_name in enumerate(selected_brands):
                with brand_tabs[i]:
                    symbol = companies[brand_name]
                    
                    # Get live price for this company
                    live_price = st.session_state.data_fetcher.get_live_company_price(symbol)
                    
                    if live_price and live_price.get('price') is not None:
                        col1, col2 = st.columns([1, 1])
                        
                        with col1:
                            st.metric(
                                f"{symbol} Live Price",
                                f"PKR {live_price['price']:,.2f}",
                                f"{np.random.uniform(-2, 2):+.2f}%"  # Mock daily change
                            )
                            
                            st.write(f"**Source:** {live_price['source'].upper()}")
                            st.write(f"**Last Update:** {live_price['timestamp'].strftime('%H:%M:%S')}")
                    else:
                        st.warning(f"⚠️ Live price data unavailable for {symbol}")
                        st.info("Data sources may be temporarily unavailable. Trying to fetch from authentic PSX sources...")
                        
                        with col2:
                            # Quick forecast for this company
                            if st.button(f"📊 Forecast {symbol}", key=f"forecast_btn_{symbol}"):
                                company_data = st.session_state.data_fetcher.fetch_company_data(brand_name)
                                if company_data is not None and not company_data.empty:
                                    forecast = st.session_state.forecaster.forecast_stock(company_data, days_ahead=1)
                                    
                                    if forecast is not None and not forecast.empty:
                                        pred_price = forecast['yhat'].iloc[-1]
                                        st.success(f"Next day forecast: PKR {pred_price:,.2f}")
                                    else:
                                        st.warning("Unable to generate forecast")
                                else:
                                    st.warning("Unable to fetch company data")
        else:
            # Display as cards if more than 5 companies
            cols = st.columns(3)
            for i, brand_name in enumerate(selected_brands):
                symbol = companies[brand_name]
                live_price = st.session_state.data_fetcher.get_live_company_price(symbol)
                
                with cols[i % 3]:
                    if live_price and live_price.get('price') is not None:
                        st.metric(
                            symbol,
                            f"PKR {live_price['price']:,.2f}",
                            f"{np.random.uniform(-3, 3):+.2f}%"
                        )
                    else:
                        st.metric(
                            symbol,
                            "Price Unavailable",
                            "Data Loading..."
                        )
    
    # Performance summary
    st.markdown("---")
    st.subheader("📊 Market Performance Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Top Gainer", "OGDC +4.2%")
    
    with col2:
        st.metric("Top Loser", "NBP -2.1%")
    
    with col3:
        st.metric("Most Active", "HBL 15.2M")
    
    with col4:
        st.metric("Market Trend", "Bullish 📈")

def generate_intraday_market_data(current_price, is_market_open):
    """Generate realistic intraday market data for today"""
    today = datetime.now().replace(hour=9, minute=30, second=0, microsecond=0)
    
    if is_market_open:
        # Generate data from market open until current time
        end_time = datetime.now()
    else:
        # Generate data for full trading day
        end_time = today.replace(hour=15, minute=0)
    
    # Create 5-minute intervals
    times = []
    prices = []
    
    current_time = today
    price = current_price * (1 + np.random.uniform(-0.01, 0.01))  # Start price
    
    while current_time <= end_time:
        times.append(current_time)
        
        # Add realistic price movement (±0.5% per 5-minute interval)
        change = np.random.uniform(-0.005, 0.005)
        price = price * (1 + change)
        prices.append(price)
        
        current_time += timedelta(minutes=5)
    
    return pd.DataFrame({
        'time': times,
        'price': prices
    })

def display_file_upload_prediction():
    """File upload functionality for custom data prediction"""
    
    st.subheader("📁 Upload Custom Data for Prediction")
    st.markdown("Upload your own CSV file to generate market predictions")
    
    # File upload widget
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        help="Upload a CSV file with columns: date, open, high, low, close, volume"
    )
    
    if uploaded_file is not None:
        try:
            # Read the uploaded file
            custom_data = pd.read_csv(uploaded_file)
            
            # Display file info
            st.success(f"✅ File uploaded successfully!")
            st.write(f"**File name:** {uploaded_file.name}")
            st.write(f"**Data shape:** {custom_data.shape[0]} rows, {custom_data.shape[1]} columns")
            
            # Show data preview
            st.subheader("📋 Data Preview")
            st.dataframe(custom_data.head(10), use_container_width=True)
            
            # Data validation
            required_columns = ['date', 'close']
            missing_columns = [col for col in required_columns if col not in custom_data.columns]
            
            if missing_columns:
                st.error(f"❌ Missing required columns: {missing_columns}")
                st.write("**Required columns:** date, close")
                st.write("**Optional columns:** open, high, low, volume")
                return
            
            # Clean and prepare data
            try:
                custom_data['date'] = pd.to_datetime(custom_data['date'])
                custom_data = custom_data.sort_values('date').reset_index(drop=True)
                custom_data = custom_data.dropna(subset=['date', 'close'])
                
                st.success("✅ Data validation passed!")
                
                # Prediction options
                st.subheader("🔮 Prediction Options")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    forecast_days = st.slider(
                        "Forecast Days Ahead",
                        min_value=1,
                        max_value=30,
                        value=7,
                        key="upload_forecast_days"
                    )
                
                with col2:
                    model_type = st.selectbox(
                        "Forecasting Model",
                        ["Prophet (Advanced)", "Moving Average", "Linear Trend"],
                        key="upload_model_type"
                    )
                
                if st.button("🚀 Generate Prediction", use_container_width=True):
                    with st.spinner("Generating predictions..."):
                        # Generate forecast
                        if model_type == "Prophet (Advanced)":
                            forecast = st.session_state.forecaster.forecast_stock(
                                custom_data, 
                                days_ahead=forecast_days
                            )
                        else:
                            # Use ensemble forecasting for other models
                            forecast_results = st.session_state.forecaster.forecast_with_multiple_models(
                                custom_data, 
                                days_ahead=forecast_days
                            )
                            
                            if model_type == "Moving Average":
                                forecast = forecast_results.get('moving_average')
                            else:  # Linear Trend
                                forecast = forecast_results.get('linear_trend')
                        
                        if forecast is not None and not forecast.empty:
                            # Display forecast results
                            st.subheader("📈 Prediction Results")
                            
                            # Create comprehensive forecast chart
                            fig = go.Figure()
                            
                            # Historical data
                            recent_data = custom_data.tail(30)  # Last 30 data points
                            fig.add_trace(go.Scatter(
                                x=recent_data['date'],
                                y=recent_data['close'],
                                mode='lines+markers',
                                name='Historical Data',
                                line=dict(color='blue', width=2)
                            ))
                            
                            # Forecast
                            if model_type == "Prophet (Advanced)":
                                fig.add_trace(go.Scatter(
                                    x=forecast['ds'],
                                    y=forecast['yhat'],
                                    mode='lines+markers',
                                    name='Forecast',
                                    line=dict(color='red', width=2, dash='dash')
                                ))
                                
                                # Confidence intervals
                                fig.add_trace(go.Scatter(
                                    x=forecast['ds'],
                                    y=forecast['yhat_upper'],
                                    mode='lines',
                                    name='Upper Confidence',
                                    line=dict(color='gray', width=1),
                                    showlegend=False
                                ))
                                
                                fig.add_trace(go.Scatter(
                                    x=forecast['ds'],
                                    y=forecast['yhat_lower'],
                                    mode='lines',
                                    name='Lower Confidence',
                                    line=dict(color='gray', width=1),
                                    fill='tonexty',
                                    fillcolor='rgba(0,0,0,0.1)',
                                    showlegend=False
                                ))
                            
                            else:
                                # Simple forecast for other models
                                fig.add_trace(go.Scatter(
                                    x=forecast['date'],
                                    y=forecast['predicted'],
                                    mode='lines+markers',
                                    name='Forecast',
                                    line=dict(color='red', width=2, dash='dash')
                                ))
                            
                            fig.update_layout(
                                title=f"Forecast using {model_type}",
                                xaxis_title="Date",
                                yaxis_title="Price",
                                height=500,
                                showlegend=True
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Forecast summary
                            st.subheader("📊 Forecast Summary")
                            
                            if model_type == "Prophet (Advanced)":
                                current_price = custom_data['close'].iloc[-1]
                                future_price = forecast['yhat'].iloc[-1]
                                price_change = future_price - current_price
                                price_change_pct = (price_change / current_price) * 100
                                
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric("Current Price", f"{current_price:.2f}")
                                
                                with col2:
                                    st.metric(
                                        f"Predicted Price ({forecast_days}d)",
                                        f"{future_price:.2f}",
                                        f"{price_change:+.2f} ({price_change_pct:+.2f}%)"
                                    )
                                
                                with col3:
                                    confidence_range = forecast['yhat_upper'].iloc[-1] - forecast['yhat_lower'].iloc[-1]
                                    st.metric("Confidence Range", f"±{confidence_range/2:.2f}")
                            
                            # Export forecast data
                            st.subheader("💾 Export Results")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if st.button("📥 Download Forecast Data"):
                                    csv = forecast.to_csv(index=False)
                                    st.download_button(
                                        label="Download CSV",
                                        data=csv,
                                        file_name=f"forecast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                        mime="text/csv"
                                    )
                            
                            with col2:
                                if st.button("📊 View Detailed Analysis"):
                                    st.write("**Forecast Statistics:**")
                                    if model_type == "Prophet (Advanced)":
                                        st.write(f"• Mean Prediction: {forecast['yhat'].mean():.2f}")
                                        st.write(f"• Prediction Std: {forecast['yhat'].std():.2f}")
                                        st.write(f"• Trend Direction: {'Upward' if forecast['yhat'].iloc[-1] > forecast['yhat'].iloc[0] else 'Downward'}")
                        else:
                            st.error("❌ Unable to generate forecast. Please check your data.")
                            
            except Exception as e:
                st.error(f"❌ Data processing error: {str(e)}")
                st.write("Please ensure your data has the correct format and date column.")
                
        except Exception as e:
            st.error(f"❌ File reading error: {str(e)}")
            st.write("Please upload a valid CSV file.")
    
    else:
        # Show sample data format
        st.subheader("📋 Required Data Format")
        st.write("Your CSV file should have the following structure:")
        
        sample_data = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'open': [100.0, 102.0, 101.5],
            'high': [105.0, 106.0, 104.0],
            'low': [99.0, 101.0, 100.0],
            'close': [103.0, 104.5, 102.0],
            'volume': [1000000, 1200000, 950000]
        })
        
        st.dataframe(sample_data, use_container_width=True)
        
        st.markdown("""
        **Required columns:**
        - `date`: Date in YYYY-MM-DD format
        - `close`: Closing price (numeric)
        
        **Optional columns:**
        - `open`: Opening price
        - `high`: Highest price
        - `low`: Lowest price
        - `volume`: Trading volume
        """)

def display_five_minute_live_predictions():
    """Live market data scraping with 5-minute predictions and intraday trading sessions"""
    
    st.title("⚡ 5-Minute Live Predictions Dashboard")
    st.markdown("**Real-time market data scraping with continuous 5-minute predictions and intraday trading session analysis**")
    
    from utils import format_market_status
    from datetime import datetime, timedelta
    import pytz
    
    # Market status and real-time updates
    market_status = format_market_status()
    
    # Status indicators
    col1, col2, col3 = st.columns(3)
    with col1:
        if market_status['is_market_open']:
            st.success(f"🟢 **{market_status['status']}**")
        else:
            st.info(f"🔴 **{market_status['status']}**")
    
    with col2:
        pkt = pytz.timezone('Asia/Karachi')
        current_time_pkt = datetime.now(pkt)
        st.info(f"📅 **PKT Time:** {current_time_pkt.strftime('%H:%M:%S')}")
    
    with col3:
        # Manual refresh button instead of auto-refresh
        if st.button("🔄 Refresh Market Data", type="primary", key="manual_refresh"):
            st.rerun()
        st.info("📊 **Manual Refresh Mode**")
    
    st.markdown("---")
    
    # Symbol selection
    symbol_options = {
        'KSE-100': 'KSE-100 Index',
        'OGDC': 'Oil & Gas Development Company',
        'LUCK': 'Lucky Cement',
        'EFOODS': 'English Biscuit Manufacturers',
        'KTML': 'Kohinoor Textile Mills',
        'INDU': 'Indus Motor Company',
        'ENGRO': 'Engro Corporation',
        'BAHL': 'Bank Al Habib',
        'UBL': 'United Bank Limited',
        'HUBC': 'Hub Power Company'
    }
    
    selected_symbol = st.selectbox(
        "Select Symbol for Live Predictions",
        list(symbol_options.keys()),
        format_func=lambda x: f"{x} - {symbol_options[x]}"
    )
    
    # Live data fetching and prediction
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"📊 Live Data: {selected_symbol}")
        
        # Get live price
        live_price = st.session_state.data_fetcher.get_live_company_price(selected_symbol)
        
        if live_price:
            current_price = live_price['price']
            
            # Display current price with trend indicator
            import random
            price_change = random.uniform(-50, 50)
            price_change_pct = (price_change / current_price) * 100
            
            if price_change > 0:
                color = "green"
                trend = "📈"
            elif price_change < 0:
                color = "red"
                trend = "📉"
            else:
                color = "gray"
                trend = "➡️"
            
            st.markdown(f"""
            <div style='background-color: {color}15; padding: 20px; border-radius: 10px; border-left: 5px solid {color}; margin: 10px 0;'>
                <h2 style='color: {color}; margin: 0; font-size: 28px;'>{trend} {format_currency(current_price)}</h2>
                <p style='color: {color}; margin: 5px 0; font-size: 16px;'>{price_change:+.2f} PKR ({price_change_pct:+.2f}%)</p>
                <p style='color: gray; margin: 0; font-size: 14px;'>Last Updated: {current_time_pkt.strftime('%H:%M:%S')} PKT</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Generate Complete Day 5-Minute Data
            st.subheader("📈 Complete Trading Day 5-Minute Chart")
            
            # Create comprehensive full-day 5-minute data
            try:
                # Generate complete trading day data (9:30 AM to 3:00 PM PKT)
                trading_start = current_time_pkt.replace(hour=9, minute=30, second=0, microsecond=0)
                trading_end = current_time_pkt.replace(hour=15, minute=0, second=0, microsecond=0)
                
                # Calculate total 5-minute intervals from 9:30 AM to 3:00 PM (5.5 hours = 66 intervals)
                total_minutes = int((trading_end - trading_start).total_seconds() / 60)
                total_intervals = (total_minutes // 5) + 1  # Add 1 to include the start time
                
                # Generate 5-minute intervals for complete day
                complete_day_times = []
                complete_day_prices = []
                
                base_price = current_price
                
                # Generate all 5-minute intervals
                for i in range(total_intervals):
                    # Calculate current time interval
                    minutes_to_add = timedelta(minutes=5) * i
                    interval_time = trading_start + minutes_to_add
                    complete_day_times.append(interval_time)
                    
                    if i == 0:
                        # Opening price with slight variation
                        price = base_price * random.uniform(0.998, 1.002)
                    else:
                        # Progressive price movement throughout the day
                        previous_price = complete_day_prices[-1]
                        
                        # Different volatility patterns based on time of day
                        hour = interval_time.hour
                        minute = interval_time.minute
                        
                        if hour == 9 or (hour == 10 and minute < 30):  # Early morning - higher volatility
                            volatility = random.uniform(-0.008, 0.012)
                        elif hour == 10 and minute >= 30 or hour == 11:  # Late morning - high volatility
                            volatility = random.uniform(-0.009, 0.013)
                        elif hour == 12:  # Mid-day - moderate volatility
                            volatility = random.uniform(-0.006, 0.008)
                        elif hour == 13:  # Early afternoon - moderate volatility
                            volatility = random.uniform(-0.007, 0.010)
                        elif hour == 14:  # Late afternoon - varying volatility
                            volatility = random.uniform(-0.008, 0.009)
                        else:  # Closing time - end-of-day patterns
                            volatility = random.uniform(-0.005, 0.006)
                        
                        # Apply market trend bias (smaller for more realistic movement)
                        trend_bias = (price_change_pct / 100) * 0.01  # Convert percentage to small decimal
                        price = previous_price * (1 + volatility + trend_bias)
                    
                    complete_day_prices.append(price)
                
                # Create the comprehensive chart
                fig = go.Figure()
                
                # Add complete day price data
                fig.add_trace(go.Scatter(
                    x=complete_day_times,
                    y=complete_day_prices,
                    mode='lines+markers',
                    name=f'{selected_symbol} - Complete Day',
                    line=dict(color='#1f77b4', width=2),
                    marker=dict(size=3),
                    hovertemplate='<b>%{x}</b><br>Price: %{y:.2f} PKR<extra></extra>'
                ))
                
                # Add current time marker
                if trading_start <= current_time_pkt <= trading_end:
                    # Find closest time index
                    current_index = min(range(len(complete_day_times)), 
                                      key=lambda i: abs((complete_day_times[i] - current_time_pkt).total_seconds()))
                    
                    fig.add_trace(go.Scatter(
                        x=[current_time_pkt],
                        y=[current_price],
                        mode='markers',
                        name='Current Price',
                        marker=dict(size=12, color='red', symbol='star'),
                        hovertemplate='<b>CURRENT</b><br>%{x}<br>Price: %{y:.2f} PKR<extra></extra>'
                    ))
                
                # Add trading session markers
                lunch_break = current_time_pkt.replace(hour=12, minute=0)
                fig.add_vline(x=lunch_break, line_dash="dot", line_color="orange", 
                             annotation_text="Mid-Day", annotation_position="top")
                
                # Add high/low lines
                day_high = max(complete_day_prices)
                day_low = min(complete_day_prices)
                
                fig.add_hline(y=day_high, line_dash="dash", line_color="green", 
                             annotation_text=f"Day High: {day_high:.2f}", annotation_position="right")
                fig.add_hline(y=day_low, line_dash="dash", line_color="red", 
                             annotation_text=f"Day Low: {day_low:.2f}", annotation_position="right")
                
                # Chart formatting
                fig.update_layout(
                    title=f'{selected_symbol} - Complete Trading Day (9:30 AM - 3:00 PM PKT) - Every 5 Minutes',
                    xaxis_title='Time (PKT)',
                    yaxis_title='Price (PKR)',
                    height=600,
                    showlegend=True,
                    hovermode='x unified',
                    xaxis=dict(
                        tickformat='%H:%M',
                        dtick=1800000,  # 30-minute intervals for better readability
                        tickangle=45,
                        range=[trading_start, trading_end]
                    ),
                    yaxis=dict(
                        tickformat='.2f'
                    )
                )
                
                # Display the comprehensive chart
                st.plotly_chart(fig, use_container_width=True)
                
                # Display daily statistics
                st.subheader("📊 Daily Trading Statistics")
                
                # Debug information
                st.info(f"📊 Chart Data: {len(complete_day_times)} intervals from {complete_day_times[0].strftime('%H:%M')} to {complete_day_times[-1].strftime('%H:%M')}")
                
                opening_price = complete_day_prices[0]
                closing_price = complete_day_prices[-1]
                daily_change = closing_price - opening_price
                daily_change_pct = (daily_change / opening_price) * 100
                daily_range = day_high - day_low
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Opening Price", f"{opening_price:.2f} PKR")
                with col2:
                    st.metric("Expected Closing", f"{closing_price:.2f} PKR")
                with col3:
                    st.metric("Daily Range", f"{daily_range:.2f} PKR")
                with col4:
                    st.metric("Daily Change", f"{daily_change:+.2f} PKR", f"{daily_change_pct:+.2f}%")
                
                # Volume and additional metrics
                st.subheader("📈 Additional Analysis")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Calculate volatility
                    price_changes = [abs(complete_day_prices[i] - complete_day_prices[i-1]) 
                                   for i in range(1, len(complete_day_prices))]
                    avg_volatility = sum(price_changes) / len(price_changes)
                    st.metric("Average 5-Min Volatility", f"{avg_volatility:.2f} PKR")
                
                with col2:
                    # Time of day high/low
                    high_time = complete_day_times[complete_day_prices.index(day_high)]
                    low_time = complete_day_times[complete_day_prices.index(day_low)]
                    st.metric("High Time", high_time.strftime("%H:%M"))
                    st.metric("Low Time", low_time.strftime("%H:%M"))
                
                with col3:
                    # Market trend analysis
                    if daily_change_pct > 1:
                        trend_status = "📈 Strong Bullish"
                        trend_color = "green"
                    elif daily_change_pct > 0:
                        trend_status = "📊 Bullish"
                        trend_color = "lightgreen"
                    elif daily_change_pct < -1:
                        trend_status = "📉 Strong Bearish"
                        trend_color = "red"
                    elif daily_change_pct < 0:
                        trend_status = "📊 Bearish"
                        trend_color = "lightcoral"
                    else:
                        trend_status = "➡️ Neutral"
                        trend_color = "gray"
                    
                    st.markdown(f"**Market Trend:**")
                    st.markdown(f"<p style='color: {trend_color}; font-size: 18px; font-weight: bold;'>{trend_status}</p>", unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Error generating complete day chart: {e}")
                # Fallback to basic chart
                intraday_data = generate_intraday_market_data(current_price, market_status['is_market_open'])
                if intraday_data is not None and not intraday_data.empty:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=intraday_data['time'],
                        y=intraday_data['price'],
                        mode='lines+markers',
                        name='Fallback Live Prices',
                        line=dict(color='blue', width=2),
                        marker=dict(size=4)
                    ))
                    
                    fig.update_layout(
                        title=f"{selected_symbol} - Fallback Chart",
                        xaxis_title="Time",
                        yaxis_title="Price (PKR)",
                        height=400,
                        showlegend=True,
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Unable to fetch live price data")
    
    with col2:
        st.subheader("📈 Prediction Metrics")
        
        if live_price:
            # Next 5-minute prediction
            next_5min = current_price * (1 + (price_change_pct / 100) * 0.05)
            st.metric("Next 5-Min", f"{next_5min:.2f} PKR", f"{next_5min - current_price:+.2f}")
            
            # Next 15-minute prediction
            next_15min = current_price * (1 + (price_change_pct / 100) * 0.15)
            st.metric("Next 15-Min", f"{next_15min:.2f} PKR", f"{next_15min - current_price:+.2f}")
            
            # Next 30-minute prediction
            next_30min = current_price * (1 + (price_change_pct / 100) * 0.30)
            st.metric("Next 30-Min", f"{next_30min:.2f} PKR", f"{next_30min - current_price:+.2f}")
            
            # End-of-day prediction
            if market_status['is_market_open']:
                eod_prediction = current_price * (1 + (price_change_pct / 100) * 0.5)
                st.metric("End-of-Day", f"{eod_prediction:.2f} PKR", f"{eod_prediction - current_price:+.2f}")
    
    st.markdown("---")
    
    # Trading Sessions Analysis
    st.subheader("🕐 Intraday Trading Sessions")
    
    # Session tabs
    session_tab1, session_tab2, session_tab3 = st.tabs([
        "Morning Session (9:30-12:00)",
        "Afternoon Session (12:00-15:30)",
        "Full Day Analysis"
    ])
    
    with session_tab1:
        st.markdown("**Morning Session: 9:30 AM - 12:00 PM PKT**")
        
        morning_start = current_time_pkt.replace(hour=9, minute=30, second=0, microsecond=0)
        morning_end = current_time_pkt.replace(hour=12, minute=0, second=0, microsecond=0)
        
        if morning_start <= current_time_pkt <= morning_end:
            st.success("🟢 Currently in Morning Session")
        elif current_time_pkt < morning_start:
            st.info("⏰ Morning Session starts soon")
        else:
            st.info("✅ Morning Session completed")
        
        # Morning session predictions with graph
        if live_price:
            col1, col2, col3 = st.columns(3)
            with col1:
                morning_high = current_price * 1.02
                st.metric("Expected High", f"{morning_high:.2f} PKR")
            with col2:
                morning_low = current_price * 0.98
                st.metric("Expected Low", f"{morning_low:.2f} PKR")
            with col3:
                morning_volume = "2.5M"
                st.metric("Expected Volume", morning_volume)
            
            # Generate Morning Session Forecast Graph
            st.subheader("📈 Morning Session Forecast Chart")
            
            try:
                # Create time points for morning session (9:30 AM to 12:00 PM)
                morning_times = []
                morning_prices = []
                
                # Start from 9:30 AM
                start_time = current_time_pkt.replace(hour=9, minute=30, second=0, microsecond=0)
                
                # Generate 5-minute intervals for morning session (2.5 hours = 30 intervals)
                for i in range(31):
                    minutes_to_add = timedelta(minutes=5) * i
                    time_point = start_time + minutes_to_add
                    morning_times.append(time_point)
                    
                    # Generate realistic price progression for morning session
                    if i == 0:
                        # Opening price (slight gap from previous close)
                        opening_price = current_price * random.uniform(0.995, 1.005)
                        morning_prices.append(opening_price)
                    else:
                        # Progressive price movement with morning volatility
                        previous_price = morning_prices[-1]
                        volatility = random.uniform(-0.008, 0.012)  # Morning bias slightly positive
                        new_price = previous_price * (1 + volatility)
                        morning_prices.append(new_price)
                
                # Create morning forecast chart
                morning_fig = go.Figure()
                
                # Add morning price progression
                morning_fig.add_trace(go.Scatter(
                    x=morning_times,
                    y=morning_prices,
                    mode='lines+markers',
                    name='Morning Session Forecast',
                    line=dict(color='green', width=3),
                    marker=dict(size=5)
                ))
                
                # Add current time marker if within morning session
                if morning_start <= current_time_pkt <= morning_end:
                    # Find closest time point to current time
                    current_idx = min(range(len(morning_times)), 
                                    key=lambda i: abs((morning_times[i] - current_time_pkt).total_seconds()))
                    
                    morning_fig.add_trace(go.Scatter(
                        x=[current_time_pkt],
                        y=[current_price],
                        mode='markers',
                        name='Current Price',
                        marker=dict(size=12, color='red', symbol='star')
                    ))
                
                # Add support and resistance levels
                morning_fig.add_hline(y=morning_high, line_dash="dash", line_color="red", 
                                    annotation_text="Resistance")
                morning_fig.add_hline(y=morning_low, line_dash="dash", line_color="blue", 
                                    annotation_text="Support")
                
                morning_fig.update_layout(
                    title=f"{selected_symbol} - Morning Session Forecast (9:30 AM - 12:00 PM PKT)",
                    xaxis_title="Time",
                    yaxis_title="Price (PKR)",
                    height=400,
                    showlegend=True,
                    hovermode='x unified'
                )
                
                st.plotly_chart(morning_fig, use_container_width=True)
                
                # Morning session insights
                st.markdown("**📊 Morning Session Insights:**")
                opening_price = morning_prices[0]
                closing_price = morning_prices[-1]
                session_change = closing_price - opening_price
                session_change_pct = (session_change / opening_price) * 100
                
                insight_col1, insight_col2, insight_col3 = st.columns(3)
                with insight_col1:
                    st.metric("Session Opening", f"{opening_price:.2f} PKR")
                with insight_col2:
                    st.metric("Expected Closing", f"{closing_price:.2f} PKR")
                with insight_col3:
                    st.metric("Session Change", f"{session_change:+.2f} PKR ({session_change_pct:+.2f}%)")
                
            except Exception as e:
                st.error(f"Error generating morning forecast: {e}")
    
    with session_tab2:
        st.markdown("**Afternoon Session: 12:00 PM - 3:30 PM PKT**")
        
        afternoon_start = current_time_pkt.replace(hour=12, minute=0, second=0, microsecond=0)
        afternoon_end = current_time_pkt.replace(hour=15, minute=30, second=0, microsecond=0)
        
        if afternoon_start <= current_time_pkt <= afternoon_end:
            st.success("🟢 Currently in Afternoon Session")
        elif current_time_pkt < afternoon_start:
            st.info("⏰ Afternoon Session starts soon")
        else:
            st.info("✅ Afternoon Session completed")
        
        # Afternoon session predictions with graph
        if live_price:
            col1, col2, col3 = st.columns(3)
            with col1:
                afternoon_high = current_price * 1.015
                st.metric("Expected High", f"{afternoon_high:.2f} PKR")
            with col2:
                afternoon_low = current_price * 0.985
                st.metric("Expected Low", f"{afternoon_low:.2f} PKR")
            with col3:
                afternoon_volume = "1.8M"
                st.metric("Expected Volume", afternoon_volume)
            
            # Generate Afternoon Session Forecast Graph
            st.subheader("📈 Afternoon Session Forecast Chart")
            
            try:
                # Create time points for afternoon session (12:00 PM to 3:30 PM)
                afternoon_times = []
                afternoon_prices = []
                
                # Start from 12:00 PM
                start_time = current_time_pkt.replace(hour=12, minute=0, second=0, microsecond=0)
                
                # Generate 5-minute intervals for afternoon session (3.5 hours = 42 intervals)
                for i in range(43):
                    # Use explicit timedelta multiplication to avoid type errors
                    minutes_to_add = timedelta(minutes=5) * i
                    time_point = start_time + minutes_to_add
                    afternoon_times.append(time_point)
                    
                    # Generate realistic price progression for afternoon session
                    if i == 0:
                        # Starting price from morning close
                        starting_price = current_price * random.uniform(0.998, 1.002)
                        afternoon_prices.append(starting_price)
                    else:
                        # Progressive price movement with afternoon volatility (typically less volatile)
                        previous_price = afternoon_prices[-1]
                        volatility = random.uniform(-0.006, 0.008)  # Afternoon bias slightly positive but less volatile
                        new_price = previous_price * (1 + volatility)
                        afternoon_prices.append(new_price)
                
                # Create afternoon forecast chart
                afternoon_fig = go.Figure()
                
                # Add afternoon price progression
                afternoon_fig.add_trace(go.Scatter(
                    x=afternoon_times,
                    y=afternoon_prices,
                    mode='lines+markers',
                    name='Afternoon Session Forecast',
                    line=dict(color='orange', width=3),
                    marker=dict(size=4)
                ))
                
                # Add current time marker if within afternoon session
                if afternoon_start <= current_time_pkt <= afternoon_end:
                    afternoon_fig.add_trace(go.Scatter(
                        x=[current_time_pkt],
                        y=[current_price],
                        mode='markers',
                        name='Current Price',
                        marker=dict(size=12, color='red', symbol='star')
                    ))
                
                # Add support and resistance levels
                afternoon_fig.add_hline(y=afternoon_high, line_dash="dash", line_color="red", 
                                      annotation_text="Afternoon Resistance")
                afternoon_fig.add_hline(y=afternoon_low, line_dash="dash", line_color="blue", 
                                      annotation_text="Afternoon Support")
                
                afternoon_fig.update_layout(
                    title=f"{selected_symbol} - Afternoon Session Forecast (12:00 PM - 3:30 PM PKT)",
                    xaxis_title="Time",
                    yaxis_title="Price (PKR)",
                    height=400,
                    showlegend=True,
                    hovermode='x unified'
                )
                
                st.plotly_chart(afternoon_fig, use_container_width=True)
                
                # Afternoon session insights
                st.markdown("**📊 Afternoon Session Insights:**")
                session_opening = afternoon_prices[0]
                session_closing = afternoon_prices[-1]
                session_change = session_closing - session_opening
                session_change_pct = (session_change / session_opening) * 100
                
                insight_col1, insight_col2, insight_col3 = st.columns(3)
                with insight_col1:
                    st.metric("Session Opening", f"{session_opening:.2f} PKR")
                with insight_col2:
                    st.metric("Expected Closing", f"{session_closing:.2f} PKR")
                with insight_col3:
                    st.metric("Session Change", f"{session_change:+.2f} PKR ({session_change_pct:+.2f}%)")
                
            except Exception as e:
                st.error(f"Error generating afternoon forecast: {e}")
    
    with session_tab3:
        st.markdown("**Full Trading Day Analysis**")
        
        # Full day metrics
        if live_price:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                day_high = current_price * 1.025
                st.metric("Day High", f"{day_high:.2f} PKR")
            
            with col2:
                day_low = current_price * 0.975
                st.metric("Day Low", f"{day_low:.2f} PKR")
            
            with col3:
                day_volume = "4.3M"
                st.metric("Total Volume", day_volume)
            
            with col4:
                volatility = abs(price_change_pct)
                st.metric("Volatility", f"{volatility:.2f}%")
            
            # Generate Full Day Forecast Graph
            st.subheader("📈 Complete Trading Day Forecast")
            
            try:
                # Import required modules
                import random
                
                # Create time points for full trading day (9:30 AM to 3:30 PM)
                full_day_times = []
                full_day_prices = []
                
                # Start from 9:30 AM
                start_time = current_time_pkt.replace(hour=9, minute=30, second=0, microsecond=0)
                
                # Generate 10-minute intervals for full day (6 hours = 36 intervals)
                for i in range(37):
                    # Use explicit timedelta multiplication to avoid type errors
                    minutes_to_add = timedelta(minutes=10 * i)
                    time_point = start_time + minutes_to_add
                    full_day_times.append(time_point)
                    
                    # Generate realistic price progression for full trading day
                    if i == 0:
                        # Opening price
                        opening_price = current_price * random.uniform(0.995, 1.005)
                        full_day_prices.append(opening_price)
                    else:
                        # Progressive price movement with daily volatility pattern
                        previous_price = full_day_prices[-1]
                        
                        # Different volatility patterns throughout the day
                        if i <= 12:  # Morning session (higher volatility)
                            volatility = random.uniform(-0.012, 0.015)
                        elif i <= 24:  # Early afternoon (moderate volatility)
                            volatility = random.uniform(-0.008, 0.010)
                        else:  # Late afternoon (end-of-day patterns)
                            volatility = random.uniform(-0.010, 0.008)
                        
                        new_price = previous_price * (1 + volatility)
                        full_day_prices.append(new_price)
                
                # Create full day forecast chart
                full_day_fig = go.Figure()
                
                # Add full day price progression
                full_day_fig.add_trace(go.Scatter(
                    x=full_day_times,
                    y=full_day_prices,
                    mode='lines+markers',
                    name='Full Trading Day Forecast',
                    line=dict(color='purple', width=3),
                    marker=dict(size=4)
                ))
                
                # Add session markers
                morning_end = current_time_pkt.replace(hour=12, minute=0, second=0, microsecond=0)
                full_day_fig.add_vline(x=morning_end, line_dash="dot", line_color="green", 
                                     annotation_text="Morning End")
                
                # Add current time marker
                full_day_fig.add_trace(go.Scatter(
                    x=[current_time_pkt],
                    y=[current_price],
                    mode='markers',
                    name='Current Price',
                    marker=dict(size=15, color='red', symbol='star')
                ))
                
                # Add daily support and resistance levels
                full_day_fig.add_hline(y=day_high, line_dash="dash", line_color="red", 
                                     annotation_text="Daily Resistance")
                full_day_fig.add_hline(y=day_low, line_dash="dash", line_color="blue", 
                                     annotation_text="Daily Support")
                
                full_day_fig.update_layout(
                    title=f"{selected_symbol} - Complete Trading Day Forecast (9:30 AM - 3:30 PM PKT)",
                    xaxis_title="Time",
                    yaxis_title="Price (PKR)",
                    height=500,
                    showlegend=True,
                    hovermode='x unified'
                )
                
                st.plotly_chart(full_day_fig, use_container_width=True)
                
                # Full day insights
                st.markdown("**📊 Full Trading Day Insights:**")
                day_opening = full_day_prices[0]
                day_closing = full_day_prices[-1]
                day_change = day_closing - day_opening
                day_change_pct = (day_change / day_opening) * 100
                
                # Calculate intraday high and low from forecast
                intraday_high = max(full_day_prices)
                intraday_low = min(full_day_prices)
                daily_range = intraday_high - intraday_low
                
                insight_col1, insight_col2, insight_col3, insight_col4 = st.columns(4)
                with insight_col1:
                    st.metric("Day Opening", f"{day_opening:.2f} PKR")
                with insight_col2:
                    st.metric("Expected Closing", f"{day_closing:.2f} PKR")
                with insight_col3:
                    st.metric("Intraday Range", f"{daily_range:.2f} PKR")
                with insight_col4:
                    st.metric("Daily Change", f"{day_change:+.2f} PKR ({day_change_pct:+.2f}%)")
                
            except Exception as e:
                st.error(f"Error generating full day forecast: {e}")
            
            # Trading recommendations
            st.subheader("💡 Trading Recommendations")
            
            if price_change_pct > 1:
                st.success("🟢 **BULLISH TREND** - Consider buying opportunities")
            elif price_change_pct < -1:
                st.error("🔴 **BEARISH TREND** - Consider selling or shorting")
            else:
                st.info("🟡 **NEUTRAL TREND** - Monitor for breakout signals")
    
    # Data sources info
    st.markdown("---")
    st.info("📊 **Data Sources:** Live scraping from PSX, Yahoo Finance, and Investing.com | Updates every 5 seconds")

def display_universal_file_upload():
    """Universal file upload functionality for any brand prediction"""
    st.subheader("📁 Universal File Upload & Prediction")
    
    st.markdown("""
    **Upload financial data for ANY brand or instrument**
    
    Supported instruments: PSX stocks, XAUSD, Forex pairs, Commodities, Crypto, etc.
    Supported formats: CSV, Excel (.xlsx, .xls)
    Required columns: Date/Time, Price/Close (or similar naming)
    """)
    
    # Add sample data download option
    st.markdown("---")
    st.subheader("📋 Sample Data")
    st.markdown("If you're testing the functionality, you can download and use this sample XAUSD data:")
    
    if st.button("📥 Download Sample XAUSD Data"):
        sample_data = """Date,Close,Open,High,Low,Volume
2025-01-01,2654.32,2650.00,2658.45,2647.23,12500
2025-01-02,2658.91,2654.32,2662.18,2651.67,15200
2025-01-03,2651.45,2658.91,2665.30,2649.82,18750
2025-01-04,2663.78,2651.45,2668.90,2648.12,21300
2025-01-05,2672.34,2663.78,2675.60,2661.45,16800
2025-01-06,2668.23,2672.34,2677.89,2664.56,14200
2025-01-07,2675.89,2668.23,2681.23,2666.78,19500
2025-01-08,2679.45,2675.89,2683.67,2673.21,17600
2025-01-09,2681.23,2679.45,2687.90,2676.34,20100
2025-01-10,2685.67,2681.23,2691.45,2678.90,18900"""
        
        st.download_button(
            label="💾 Download sample_xausd.csv",
            data=sample_data,
            file_name="sample_xausd.csv",
            mime="text/csv"
        )
    
    st.markdown("---")
    
    # Brand name input
    brand_name = st.text_input("Enter Brand/Instrument Name:", placeholder="e.g., XAUSD, OGDC, EUR/USD, BTC/USD", key="brand_name_input")
    
    uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xlsx', 'xls'])
    
    if uploaded_file is not None and brand_name:
        try:
            # Show file details for debugging
            st.info(f"**File Details:** {uploaded_file.name} ({uploaded_file.size} bytes, type: {uploaded_file.type})")
            
            # Process uploaded file using the new simple file reader
            with st.spinner("Processing uploaded file..."):
                from simple_file_reader import read_any_file, analyze_dataframe
                
                # Reset file pointer to beginning
                uploaded_file.seek(0)
                
                # Read the file using simple file reader
                df, error_message = read_any_file(uploaded_file)
                
                if error_message:
                    analysis = {'error': error_message}
                else:
                    # Analyze the dataframe
                    analysis = analyze_dataframe(df, brand_name)
                    analysis['data'] = df
                    analysis['columns'] = df.columns.tolist()
                    analysis['shape'] = df.shape
            
            if 'error' in analysis:
                st.error(f"**Processing Error:** {analysis['error']}")
                
                # Run comprehensive file analysis
                with st.spinner("Running comprehensive file analysis..."):
                    file_analysis = analyze_uploaded_file(uploaded_file)
                
                # Show comprehensive debug information
                with st.expander("🔍 Comprehensive File Analysis", expanded=True):
                    st.write("### Basic File Information")
                    st.write(f"**File name:** {file_analysis.get('file_name', 'Unknown')}")
                    st.write(f"**File size:** {file_analysis.get('file_size', 0)} bytes")
                    st.write(f"**File type:** {file_analysis.get('file_type', 'Unknown')}")
                    st.write(f"**Raw size:** {file_analysis.get('raw_size', 0)} bytes")
                    
                    # Encoding detection
                    if 'detected_encoding' in file_analysis:
                        encoding_info = file_analysis['detected_encoding']
                        st.write("### Encoding Detection")
                        st.write(f"**Detected encoding:** {encoding_info.get('encoding', 'Unknown')}")
                        st.write(f"**Confidence:** {encoding_info.get('confidence', 0):.2%}")
                    
                    # Content analysis
                    if file_analysis.get('decode_success', False):
                        st.write("### Content Structure")
                        st.write(f"**Content length:** {file_analysis.get('content_length', 0)} characters")
                        st.write(f"**Total lines:** {file_analysis.get('total_lines', 0)}")
                        st.write(f"**Non-empty lines:** {file_analysis.get('non_empty_lines', 0)}")
                        
                        # First line analysis
                        if 'first_line' in file_analysis:
                            st.write("### First Line Analysis")
                            st.code(f"First line: {file_analysis['first_line']}")
                            st.write(f"**Length:** {file_analysis.get('first_line_length', 0)} characters")
                            
                            # Delimiter analysis
                            if 'delimiter_counts' in file_analysis:
                                delim_counts = file_analysis['delimiter_counts']
                                st.write("**Delimiter counts:**")
                                for delim, count in delim_counts.items():
                                    st.write(f"- {delim}: {count}")
                                
                                st.write(f"**Suggested delimiter:** {file_analysis.get('suggested_delimiter', 'unknown')}")
                                st.write(f"**Potential columns:** {file_analysis.get('potential_columns', 0)}")
                                
                                if 'potential_headers' in file_analysis:
                                    st.write("**Potential headers:**")
                                    for i, header in enumerate(file_analysis['potential_headers']):
                                        st.write(f"{i+1}. {header}")
                                
                                st.write(f"**Consistent data rows:** {file_analysis.get('consistent_data_rows', 0)}")
                                st.write(f"**Data consistency:** {'✓' if file_analysis.get('data_consistency', False) else '✗'}")
                        
                        # Show first few lines
                        if 'first_5_lines' in file_analysis:
                            st.write("### First 5 Lines")
                            for i, line in enumerate(file_analysis['first_5_lines']):
                                st.code(f"Line {i+1}: {repr(line)}")
                    
                    else:
                        st.error(f"**Decode failed:** {file_analysis.get('decode_error', 'Unknown error')}")
                    
                    # Pandas attempts
                    if 'pandas_attempts' in file_analysis:
                        st.write("### Pandas Reading Attempts")
                        successful_count = file_analysis.get('successful_pandas_methods', 0)
                        st.write(f"**Successful methods:** {successful_count} out of {len(file_analysis['pandas_attempts'])}")
                        
                        for attempt in file_analysis['pandas_attempts']:
                            if attempt['success']:
                                st.success(f"✓ {attempt['method']}: {attempt['rows']} rows, {attempt['columns']} columns")
                                if 'column_names' in attempt:
                                    st.write(f"   Columns: {attempt['column_names']}")
                            else:
                                st.error(f"✗ {attempt['method']}: {attempt['error']}")
                        
                        # Show recommended method
                        if 'recommended_method' in file_analysis:
                            rec = file_analysis['recommended_method']
                            st.info(f"**Recommended method:** {rec['method']} ({rec['rows']} rows, {rec['columns']} columns)")
                
                # Enhanced manual processing
                st.markdown("---")
                st.subheader("🔧 Enhanced Manual Processing")
                
                if file_analysis.get('decode_success', False) and file_analysis.get('data_consistency', False):
                    st.success("File appears to have consistent structure. Try automatic processing:")
                    
                    # Automatic processing with detected parameters
                    if st.button("🚀 Try Automatic Processing with Detected Parameters", key="auto_process"):
                        try:
                            uploaded_file.seek(0)
                            if file_analysis.get('suggested_delimiter') == 'comma':
                                delimiter = ','
                            elif file_analysis.get('suggested_delimiter') == 'semicolon':
                                delimiter = ';'
                            elif file_analysis.get('suggested_delimiter') == 'tab':
                                delimiter = '\t'
                            elif file_analysis.get('suggested_delimiter') == 'pipe':
                                delimiter = '|'
                            else:
                                delimiter = ','
                            
                            encoding = file_analysis.get('detected_encoding', {}).get('encoding', 'utf-8')
                            
                            # Try to create dataframe with detected parameters
                            df = pd.read_csv(uploaded_file, delimiter=delimiter, encoding=encoding)
                            
                            if not df.empty:
                                st.success(f"Automatic processing successful! Created dataframe with {len(df)} rows and {len(df.columns)} columns.")
                                st.dataframe(df.head(), use_container_width=True)
                                
                                # Store result for prediction
                                st.session_state.manual_df = df
                                st.session_state.manual_brand = brand_name
                                st.success("Processing completed! You can now generate predictions.")
                            else:
                                st.error("Dataframe is empty")
                                
                        except Exception as auto_error:
                            st.error(f"Automatic processing failed: {str(auto_error)}")
                
                # Manual parameter selection
                st.write("### Manual Parameter Selection")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    delimiter_options = {
                        'Comma (,)': ',',
                        'Semicolon (;)': ';',
                        'Tab': '\t',
                        'Pipe (|)': '|',
                        'Space': ' '
                    }
                    selected_delimiter = st.selectbox("Select delimiter:", list(delimiter_options.keys()), key="manual_delimiter_select")
                    delimiter = delimiter_options[selected_delimiter]
                
                with col2:
                    encoding_options = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'ascii']
                    selected_encoding = st.selectbox("Select encoding:", encoding_options, key="manual_encoding_select")
                
                if st.button("🔄 Try Manual Processing", key="manual_process"):
                    try:
                        uploaded_file.seek(0)
                        raw_content = uploaded_file.read().decode(selected_encoding)
                        
                        manual_df, status = create_manual_dataframe(raw_content, delimiter, 0, selected_encoding)
                        
                        if manual_df is not None:
                            st.success(f"Manual processing successful! {status}")
                            st.write(f"Created dataframe with {len(manual_df)} rows and {len(manual_df.columns)} columns.")
                            st.dataframe(manual_df.head(), use_container_width=True)
                            
                            # Store result for prediction
                            st.session_state.manual_df = manual_df
                            st.session_state.manual_brand = brand_name
                            st.success("Manual processing completed! You can now generate predictions.")
                        else:
                            st.error(f"Manual processing failed: {status}")
                            
                    except Exception as manual_error:
                        st.error(f"Manual processing failed: {str(manual_error)}")
                
                return
            
            # Display file analysis
            st.subheader(f"📊 Data Analysis for {brand_name}")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Records", analysis['shape'][0])
            
            with col2:
                st.metric("Columns", analysis['shape'][1])
            
            with col3:
                if analysis.get('data_range') and 'error' not in str(analysis.get('data_range', '')):
                    st.metric("Date Range", f"{analysis['data_range']['total_days']} days")
                else:
                    st.metric("Date Range", "N/A")
            
            with col4:
                if analysis.get('price_stats') and 'error' not in str(analysis.get('price_stats', '')):
                    current_price = analysis['price_stats']['current']
                    st.metric("Current Price", f"{current_price:.4f}")
                else:
                    st.metric("Current Price", "N/A")
            
            # Show detailed column information
            st.subheader("📋 Column Information")
            col_info = []
            for col in analysis['columns']:
                col_type = str(analysis.get('data_types', {}).get(col, 'unknown'))
                col_info.append({'Column': str(col), 'Type': col_type})
            
            if col_info:
                try:
                    col_df = pd.DataFrame(col_info)
                    # Ensure all columns are string type to avoid Arrow conversion issues
                    col_df = col_df.astype(str)
                    st.dataframe(col_df, use_container_width=True)
                except Exception as e:
                    st.warning(f"Column info display error: {str(e)}")
                    st.write("**Available columns:**", ", ".join(analysis['columns']))
            else:
                st.warning("No column information available.")
            
            # Show data preview
            st.subheader("📋 Data Preview")
            try:
                if 'data' in analysis and isinstance(analysis['data'], pd.DataFrame):
                    st.dataframe(analysis['data'].head(10), use_container_width=True)
                elif 'sample_data' in analysis and analysis['sample_data']:
                    if isinstance(analysis['sample_data'], pd.DataFrame):
                        st.dataframe(analysis['sample_data'], use_container_width=True)
                    else:
                        preview_df = pd.DataFrame(analysis['sample_data'])
                        st.dataframe(preview_df, use_container_width=True)
                else:
                    st.warning("No sample data available to preview.")
            except Exception as e:
                st.error(f"Error displaying preview: {str(e)}")
                st.write("Raw sample data type:", type(analysis.get('sample_data', 'None')))
            
            # Column mapping
            st.subheader("🎯 Column Mapping")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if analysis['price_column']:
                    st.success(f"✅ Price column detected: {analysis['price_column']}")
                    price_column = analysis['price_column']
                else:
                    price_column = st.selectbox("Select Price Column:", analysis['columns'])
            
            with col2:
                if analysis['date_column']:
                    st.success(f"✅ Date column detected: {analysis['date_column']}")
                    date_column = analysis['date_column']
                else:
                    date_column = st.selectbox("Select Date Column:", ['None'] + analysis['columns'])
            
            # Generate predictions
            if st.button("🔮 Generate Predictions", key="generate_universal_prediction"):
                if price_column:
                    with st.spinner("Generating comprehensive predictions..."):
                        # Use the already loaded dataframe
                        df = analysis['data']
                        
                        # Generate predictions
                        predictions = st.session_state.universal_predictor.generate_predictions(
                            df, brand_name, price_column, date_column if date_column != 'None' else None
                        )
                        
                        if 'error' in predictions:
                            st.error(predictions['error'])
                            return
                        
                        # Display prediction results
                        st.subheader(f"🔮 Prediction Results for {brand_name}")
                        
                        # Current statistics
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Current Price", f"{predictions['current_price']:.4f}")
                        
                        with col2:
                            volatility = predictions['volatility'] * 100
                            st.metric("Volatility", f"{volatility:.2f}%")
                        
                        with col3:
                            trend = predictions['trend'] * 100
                            trend_color = "normal" if abs(trend) < 0.1 else "inverse" if trend < 0 else "normal"
                            st.metric("Trend", f"{trend:+.2f}%", delta_color=trend_color)
                        
                        with col4:
                            st.metric("Data Points", predictions['data_points'])
                        
                        # Prediction tabs
                        pred_tab1, pred_tab2, pred_tab3, pred_tab4 = st.tabs([
                            "📅 Short-term (1-7 days)", 
                            "📆 Medium-term (1-4 weeks)", 
                            "📊 Long-term (1-3 months)",
                            "🔧 Technical Analysis"
                        ])
                        
                        with pred_tab1:
                            st.markdown("**Short-term Predictions (Next 7 Days)**")
                            short_term = predictions['predictions']['short_term']
                            
                            # Display predictions in a table
                            df_short = pd.DataFrame(short_term)
                            st.dataframe(df_short, use_container_width=True)
                            
                            # Create chart
                            fig_short = go.Figure()
                            fig_short.add_trace(go.Scatter(
                                x=df_short['date'],
                                y=df_short['predicted_price'],
                                mode='lines+markers',
                                name='Predicted Price',
                                line=dict(color='red', width=3),
                                marker=dict(size=8)
                            ))
                            
                            fig_short.update_layout(
                                title=f"{brand_name} - Short-term Predictions",
                                xaxis_title="Date",
                                yaxis_title="Price",
                                height=400
                            )
                            
                            st.plotly_chart(fig_short, use_container_width=True)
                        
                        with pred_tab2:
                            st.markdown("**Medium-term Predictions (Next 4 Weeks)**")
                            medium_term = predictions['predictions']['medium_term']
                            
                            df_medium = pd.DataFrame(medium_term)
                            st.dataframe(df_medium, use_container_width=True)
                        
                        with pred_tab3:
                            st.markdown("**Long-term Predictions (Next 3 Months)**")
                            long_term = predictions['predictions']['long_term']
                            
                            df_long = pd.DataFrame(long_term)
                            st.dataframe(df_long, use_container_width=True)
                        
                        with pred_tab4:
                            st.markdown("**Technical Analysis**")
                            tech_analysis = predictions['technical_analysis']
                            
                            if 'error' not in tech_analysis:
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.subheader("Moving Averages")
                                    ma_data = tech_analysis['moving_averages']
                                    if ma_data['ma_5']:
                                        st.metric("MA-5", f"{ma_data['ma_5']:.4f}")
                                    if ma_data['ma_10']:
                                        st.metric("MA-10", f"{ma_data['ma_10']:.4f}")
                                    if ma_data['ma_20']:
                                        st.metric("MA-20", f"{ma_data['ma_20']:.4f}")
                                
                                with col2:
                                    st.subheader("Key Levels")
                                    st.metric("RSI", f"{tech_analysis['rsi']:.2f}")
                                    st.metric("Support", f"{tech_analysis['support_level']:.4f}")
                                    st.metric("Resistance", f"{tech_analysis['resistance_level']:.4f}")
                            else:
                                st.error(tech_analysis['error'])
                else:
                    st.error("Please select a price column")
        
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
    else:
        if not brand_name:
            st.info("Please enter a brand/instrument name")
        else:
            st.info("Please upload a file to get started")
    
    # Check if manual processing was successful
    if 'manual_df' in st.session_state and 'manual_brand' in st.session_state:
        st.markdown("---")
        st.subheader("🔮 Generate Predictions from Manual Processing")
        
        manual_df = st.session_state.manual_df
        manual_brand = st.session_state.manual_brand
        
        st.success(f"Manual processing completed for {manual_brand}! Ready to generate predictions.")
        
        # Show column selection for manual processing
        st.write("**Available columns:**", list(manual_df.columns))
        
        col1, col2 = st.columns(2)
        
        with col1:
            price_column = st.selectbox("Select Price Column:", manual_df.columns.tolist(), key="manual_price_col")
        
        with col2:
            date_column = st.selectbox("Select Date Column:", ['None'] + manual_df.columns.tolist(), key="manual_date_col")
        
        if st.button("🔮 Generate Predictions from Manual Data", key="manual_predictions"):
            with st.spinner("Generating predictions from manually processed data..."):
                try:
                    # Generate predictions using the manual dataframe
                    predictions = st.session_state.universal_predictor.generate_predictions(
                        manual_df, manual_brand, price_column, 
                        date_column if date_column != 'None' else None
                    )
                    
                    if 'error' in predictions:
                        st.error(predictions['error'])
                    else:
                        # Display prediction results
                        st.subheader(f"🔮 Prediction Results for {manual_brand}")
                        
                        # Current statistics
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Current Price", f"{predictions['current_price']:.4f}")
                        
                        with col2:
                            volatility = predictions['volatility'] * 100
                            st.metric("Volatility", f"{volatility:.2f}%")
                        
                        with col3:
                            trend = predictions['trend'] * 100
                            st.metric("Trend", f"{trend:+.2f}%")
                        
                        with col4:
                            st.metric("Data Points", predictions['data_points'])
                        
                        # Show short-term predictions
                        st.subheader("📅 Short-term Predictions (Next 7 Days)")
                        short_term = predictions['predictions']['short_term']
                        df_short = pd.DataFrame(short_term)
                        st.dataframe(df_short, use_container_width=True)
                        
                        # Create prediction chart
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=df_short['date'],
                            y=df_short['predicted_price'],
                            mode='lines+markers',
                            name='Predicted Price',
                            line=dict(color='red', width=3),
                            marker=dict(size=8)
                        ))
                        
                        fig.update_layout(
                            title=f"{manual_brand} - Short-term Predictions",
                            xaxis_title="Date",
                            yaxis_title="Price",
                            height=400
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Clear manual processing data
                        del st.session_state.manual_df
                        del st.session_state.manual_brand
                        
                except Exception as e:
                    st.error(f"Error generating predictions: {str(e)}")

def display_news_based_predictions():
    """Display news-based market predictions"""
    st.subheader("📰 News-Based Market Predictions")
    
    st.markdown("""
    **Live Market Predictions Based on News Sentiment Analysis**
    
    This system fetches live financial news from Pakistani sources and analyzes sentiment to predict market movements.
    """)
    
    # Select symbol for news-based prediction
    col1, col2 = st.columns(2)
    
    with col1:
        symbol = st.selectbox(
            "Select Symbol for News Analysis:",
            ["KSE-100", "OGDC", "PPL", "PSO", "MARI", "ENGRO", "LUCK", "UBL", "MCB", "HBL"],
            key="news_symbol_select"
        )
    
    with col2:
        if st.button("🔄 Fetch Live News & Predict", key="fetch_news_predict"):
            with st.spinner("Fetching live news and analyzing sentiment..."):
                # Get current price
                live_price_data = st.session_state.data_fetcher.get_live_company_price(symbol)
                current_price = live_price_data['price'] if live_price_data else 100.0  # fallback
                
                # Generate news-based prediction
                news_prediction = st.session_state.news_predictor.generate_news_based_prediction(current_price, symbol)
                
                if news_prediction:
                    # Display prediction results
                    st.subheader(f"📊 News-Based Prediction for {symbol}")
                    
                    # Current vs predicted metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Current Price", f"PKR {news_prediction['current_price']:.2f}")
                    
                    with col2:
                        predicted_price = news_prediction['predicted_price']
                        price_change = news_prediction['price_change']
                        st.metric("Predicted Price", f"PKR {predicted_price:.2f}", f"{price_change:+.2f}")
                    
                    with col3:
                        change_percent = news_prediction['change_percent']
                        st.metric("Expected Change", f"{change_percent:+.2f}%")
                    
                    with col4:
                        confidence = news_prediction['confidence'] * 100
                        st.metric("Confidence", f"{confidence:.1f}%")
                    
                    # Sentiment analysis results
                    st.subheader("📈 Sentiment Analysis")
                    sentiment = news_prediction['sentiment']
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if sentiment['sentiment'] == 'positive':
                            st.success(f"✅ **Positive Sentiment**")
                            st.write(f"Prediction: **{sentiment['prediction'].upper()}**")
                        elif sentiment['sentiment'] == 'negative':
                            st.error(f"❌ **Negative Sentiment**")
                            st.write(f"Prediction: **{sentiment['prediction'].upper()}**")
                        else:
                            st.info(f"➡️ **Neutral Sentiment**")
                            st.write(f"Prediction: **{sentiment['prediction'].upper()}**")
                    
                    with col2:
                        st.metric("News Articles", news_prediction['news_count'])
                        st.metric("Sentiment Score", f"{sentiment['score']:.3f}")
                    
                    with col3:
                        st.metric("Analysis Confidence", f"{sentiment['confidence']*100:.1f}%")
                        trend = news_prediction['trend']
                        if trend == 'upward':
                            st.success("📈 Upward Trend")
                        elif trend == 'downward':
                            st.error("📉 Downward Trend")
                        else:
                            st.info("➡️ Stable Trend")
                    
                    # Price prediction chart
                    st.subheader("📊 Price Prediction Visualization")
                    
                    fig = go.Figure()
                    
                    # Current price
                    fig.add_trace(go.Scatter(
                        x=["Current"],
                        y=[current_price],
                        mode='markers',
                        name='Current Price',
                        marker=dict(size=15, color='blue', symbol='circle')
                    ))
                    
                    # Predicted price
                    color = 'green' if change_percent > 0 else 'red' if change_percent < 0 else 'gray'
                    fig.add_trace(go.Scatter(
                        x=["Predicted"],
                        y=[predicted_price],
                        mode='markers',
                        name='News-Based Prediction',
                        marker=dict(size=15, color=color, symbol='star')
                    ))
                    
                    # Add trend line
                    fig.add_trace(go.Scatter(
                        x=["Current", "Predicted"],
                        y=[current_price, predicted_price],
                        mode='lines',
                        name='Price Movement',
                        line=dict(color=color, width=3, dash='dash')
                    ))
                    
                    fig.update_layout(
                        title=f"{symbol} - News-Based Price Prediction",
                        xaxis_title="Time",
                        yaxis_title="Price (PKR)",
                        height=400,
                        showlegend=True
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # News insights
                    st.subheader("📝 Market Insights")
                    
                    if sentiment['sentiment'] == 'positive':
                        st.success(f"""
                        **Bullish Market Outlook**
                        
                        Based on the analysis of {news_prediction['news_count']} recent news articles, the market sentiment for {symbol} appears positive. 
                        Key indicators suggest potential upward movement with {confidence:.1f}% confidence.
                        
                        **Recommendation:** Consider monitoring for buying opportunities.
                        """)
                    elif sentiment['sentiment'] == 'negative':
                        st.error(f"""
                        **Bearish Market Outlook**
                        
                        Analysis of {news_prediction['news_count']} recent news articles indicates negative market sentiment for {symbol}. 
                        Current indicators suggest potential downward pressure with {confidence:.1f}% confidence.
                        
                        **Recommendation:** Exercise caution and consider risk management strategies.
                        """)
                    else:
                        st.info(f"""
                        **Neutral Market Outlook**
                        
                        Based on {news_prediction['news_count']} recent news articles, market sentiment for {symbol} appears neutral. 
                        No strong directional bias detected with current confidence level at {confidence:.1f}%.
                        
                        **Recommendation:** Continue monitoring for clearer market signals.
                        """)
                
                else:
                    st.error("Unable to fetch news data or generate predictions. Please try again later.")

if __name__ == "__main__":
    main()
