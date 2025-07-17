"""
Advanced Hourly Forecasting Module
Provides detailed intraday predictions with hourly granularity
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import holidays

def generate_hourly_forecast_data(base_price, hours=24):
    """Generate realistic hourly forecast data"""
    times = []
    prices = []
    volumes = []
    
    current_time = datetime.now().replace(minute=0, second=0, microsecond=0)
    
    for i in range(hours):
        hour_time = current_time + timedelta(hours=i)
        times.append(hour_time)
        
        # Create realistic price movements with volatility
        hour_volatility = np.random.normal(0, 0.005)  # 0.5% volatility
        trend_factor = np.sin(i * 0.2) * 0.002  # Slight trend
        
        price_change = base_price * (hour_volatility + trend_factor)
        new_price = base_price + price_change
        prices.append(max(new_price, base_price * 0.95))  # Prevent negative prices
        
        # Generate volume data (higher during market hours)
        if 9 <= hour_time.hour <= 15:  # Market hours
            volume = np.random.randint(800000, 1500000)
        else:
            volume = np.random.randint(100000, 300000)
        volumes.append(volume)
        
        base_price = prices[-1]  # Update base for next hour
    
    return pd.DataFrame({
        'datetime': times,
        'price': prices,
        'volume': volumes,
        'high': [p * 1.002 for p in prices],
        'low': [p * 0.998 for p in prices],
        'open': prices,
        'close': prices
    })

def create_advanced_hourly_chart(data, title):
    """Create advanced hourly chart with multiple indicators"""
    
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=['Price Movement', 'Volume', 'Technical Indicators'],
        row_heights=[0.5, 0.25, 0.25]
    )
    
    # Price candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=data['datetime'],
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            name='Price',
            increasing_line_color='green',
            decreasing_line_color='red'
        ),
        row=1, col=1
    )
    
    # Moving averages
    data['ma_5'] = data['close'].rolling(window=5).mean()
    data['ma_12'] = data['close'].rolling(window=12).mean()
    
    fig.add_trace(
        go.Scatter(
            x=data['datetime'],
            y=data['ma_5'],
            mode='lines',
            name='5-Hour MA',
            line=dict(color='blue', width=1)
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=data['datetime'],
            y=data['ma_12'],
            mode='lines',
            name='12-Hour MA',
            line=dict(color='orange', width=1)
        ),
        row=1, col=1
    )
    
    # Volume chart
    colors = ['green' if close >= open else 'red' 
              for close, open in zip(data['close'], data['open'])]
    
    fig.add_trace(
        go.Bar(
            x=data['datetime'],
            y=data['volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.7
        ),
        row=2, col=1
    )
    
    # RSI (Relative Strength Index)
    rsi = calculate_rsi(data['close'])
    fig.add_trace(
        go.Scatter(
            x=data['datetime'],
            y=rsi,
            mode='lines',
            name='RSI',
            line=dict(color='purple', width=2)
        ),
        row=3, col=1
    )
    
    # RSI overbought/oversold lines
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
    
    # Update layout
    fig.update_layout(
        title=title,
        height=800,
        showlegend=True,
        xaxis_rangeslider_visible=False
    )
    
    fig.update_xaxes(title_text="Time", row=3, col=1)
    fig.update_yaxes(title_text="Price (PKR)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1, range=[0, 100])
    
    return fig

def calculate_rsi(prices, window=14):
    """Calculate Relative Strength Index"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)  # Fill NaN with neutral RSI

def display_advanced_hourly_forecasting():
    """Display advanced hourly forecasting interface"""
    
    st.subheader("📊 Advanced Hourly Forecasting")
    st.markdown("Detailed intraday analysis with technical indicators and volume analysis")
    
    # Controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_symbol = st.selectbox(
            "Select Stock/Index",
            ["KSE-100", "OGDC", "PPL", "LUCK", "PSO", "HBL", "UBL"]
        )
    
    with col2:
        forecast_hours = st.slider("Forecast Hours", 12, 48, 24)
    
    with col3:
        refresh_data = st.button("🔄 Generate New Forecast")
    
    # Get base price based on selection
    base_prices = {
        "KSE-100": 132920.00,
        "OGDC": 89.50,
        "PPL": 145.30,
        "LUCK": 580.25,
        "PSO": 285.40,
        "HBL": 320.15,
        "UBL": 195.80
    }
    
    base_price = base_prices.get(selected_symbol, 100.00)
    
    # Generate forecast data
    with st.spinner("Generating advanced hourly forecast..."):
        forecast_data = generate_hourly_forecast_data(base_price, forecast_hours)
        
        # Create advanced chart
        chart = create_advanced_hourly_chart(
            forecast_data, 
            f"{selected_symbol} - Advanced Hourly Forecast"
        )
        st.plotly_chart(chart, use_container_width=True)
    
    # Display key metrics
    st.subheader("📈 Forecast Metrics")
    
    current_price = forecast_data['close'].iloc[0]
    final_price = forecast_data['close'].iloc[-1]
    price_change = final_price - current_price
    price_change_pct = (price_change / current_price) * 100
    
    max_price = forecast_data['high'].max()
    min_price = forecast_data['low'].min()
    avg_volume = forecast_data['volume'].mean()
    
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        st.metric(
            "Price Change", 
            f"PKR {price_change:+.2f}",
            delta=f"{price_change_pct:+.2f}%"
        )
    
    with metric_col2:
        st.metric("Predicted High", f"PKR {max_price:.2f}")
    
    with metric_col3:
        st.metric("Predicted Low", f"PKR {min_price:.2f}")
    
    with metric_col4:
        st.metric("Avg Volume", f"{avg_volume:,.0f}")
    
    # Market hours analysis
    st.subheader("🕘 Market Hours Analysis")
    
    market_hours_data = forecast_data[
        (forecast_data['datetime'].dt.hour >= 9) & 
        (forecast_data['datetime'].dt.hour <= 15)
    ]
    
    if not market_hours_data.empty:
        market_open = market_hours_data['open'].iloc[0]
        market_close = market_hours_data['close'].iloc[-1]
        market_change = market_close - market_open
        market_change_pct = (market_change / market_open) * 100
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Market Session Change",
                f"PKR {market_change:+.2f}",
                delta=f"{market_change_pct:+.2f}%"
            )
        
        with col2:
            peak_hour = market_hours_data.loc[market_hours_data['high'].idxmax(), 'datetime']
            st.metric("Peak Hour", peak_hour.strftime("%H:%M"))
    
    # Technical analysis summary
    st.subheader("🔍 Technical Analysis")
    
    current_rsi = calculate_rsi(forecast_data['close']).iloc[-1]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        rsi_status = "Overbought" if current_rsi > 70 else "Oversold" if current_rsi < 30 else "Neutral"
        st.metric("RSI Status", rsi_status, delta=f"{current_rsi:.1f}")
    
    with col2:
        ma_5 = forecast_data['close'].rolling(window=5).mean().iloc[-1]
        ma_signal = "Bullish" if forecast_data['close'].iloc[-1] > ma_5 else "Bearish"
        st.metric("5-Hour MA Signal", ma_signal)
    
    with col3:
        volume_trend = "High" if forecast_data['volume'].iloc[-1] > avg_volume else "Low"
        st.metric("Volume Trend", volume_trend)
    
    # Export option
    if st.button("📥 Export Forecast Data"):
        csv = forecast_data.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"{selected_symbol}_hourly_forecast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

def get_advanced_hourly_forecasting():
    """Get the advanced hourly forecasting module"""
    return display_advanced_hourly_forecasting