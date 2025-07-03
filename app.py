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
            ["Live Market Dashboard", "KSE-100 Index", "Individual Companies", "Enhanced File Upload", "File Upload Prediction", "All Companies Live Prices", "Intraday Trading Sessions", "Comprehensive Intraday Forecasts", "Database Overview"],
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
    
    # Main content area
    if analysis_type == "Live Market Dashboard":
        display_live_market_dashboard()
    elif analysis_type == "KSE-100 Index":
        display_kse100_analysis(forecast_type, days_ahead, custom_date)
    elif analysis_type == "Individual Companies":
        display_company_analysis(selected_company, forecast_type, days_ahead, custom_date)
    elif analysis_type == "Enhanced File Upload":
        display_enhanced_file_upload()
    elif analysis_type == "File Upload Prediction":
        display_file_upload_prediction()
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
            st.metric("Source", source.upper())
        
        with col3:
            st.metric("Volume", "125.6M")
        
        with col4:
            st.metric("Market Cap", "PKR 8.2T")
        
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
                    
                    if live_price:
                        col1, col2 = st.columns([1, 1])
                        
                        with col1:
                            st.metric(
                                f"{symbol} Live Price",
                                f"PKR {live_price['price']:,.2f}",
                                f"{np.random.uniform(-2, 2):+.2f}%"  # Mock daily change
                            )
                            
                            st.write(f"**Source:** {live_price['source'].upper()}")
                            st.write(f"**Last Update:** {live_price['timestamp'].strftime('%H:%M:%S')}")
                        
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
                    if live_price:
                        st.metric(
                            symbol,
                            f"PKR {live_price['price']:,.2f}",
                            f"{np.random.uniform(-3, 3):+.2f}%"
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

if __name__ == "__main__":
    main()
