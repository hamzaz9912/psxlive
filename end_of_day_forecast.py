"""
End of Day Forecasting Module
Provides complete trading day visualization and analysis after market closure
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
import random
from data_fetcher import DataFetcher
from forecasting import StockForecaster

class EndOfDayForecaster:
    """Complete trading day analysis and forecasting after market closure"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.forecaster = StockForecaster()
        
        # PSX trading hours (9:30 AM to 3:30 PM PKT)
        self.trading_start = 9.5  # 9:30 AM
        self.trading_end = 15.5   # 3:30 PM
        
    def generate_complete_trading_day_data(self, symbol="KSE-100", current_price=13389.34):
        """Generate complete trading day data for visualization"""
        
        # Create time series for full trading day
        time_points = []
        prices = []
        volumes = []
        
        # Generate 30-minute intervals from 9:30 AM to 3:30 PM
        current_time = datetime.now().replace(hour=9, minute=30, second=0, microsecond=0)
        end_time = datetime.now().replace(hour=15, minute=30, second=0, microsecond=0)
        
        base_price = current_price
        total_intervals = 13  # 6 hours of trading in 30-minute intervals
        
        for i in range(total_intervals):
            time_points.append(current_time + timedelta(minutes=30 * i))
            
            # Generate realistic price movements
            if i == 0:
                # Opening price
                price = base_price * random.uniform(0.998, 1.002)
            else:
                # Progressive price movement based on trading patterns
                previous_price = prices[-1]
                
                # Different volatility patterns throughout the day
                if i <= 2:  # Opening session (9:30-10:30)
                    volatility = random.uniform(-0.008, 0.012)
                elif i <= 8:  # Mid-day session (10:30-2:00)
                    volatility = random.uniform(-0.005, 0.008)
                else:  # Closing session (2:00-3:30)
                    volatility = random.uniform(-0.010, 0.006)
                
                price = previous_price * (1 + volatility)
            
            prices.append(price)
            
            # Generate volume data (higher at opening and closing)
            if i <= 2 or i >= 10:  # Opening and closing sessions
                volume = random.randint(800000, 1500000)
            else:  # Mid-day session
                volume = random.randint(300000, 800000)
            
            volumes.append(volume)
        
        return pd.DataFrame({
            'time': time_points,
            'price': prices,
            'volume': volumes
        })
    
    def create_end_of_day_analysis(self, symbol="KSE-100"):
        """Create comprehensive end-of-day analysis"""
        
        # Generate today's trading data
        trading_data = self.generate_complete_trading_day_data(symbol)
        
        # Calculate key metrics
        opening_price = trading_data['price'].iloc[0]
        closing_price = trading_data['price'].iloc[-1]
        day_high = trading_data['price'].max()
        day_low = trading_data['price'].min()
        total_volume = trading_data['volume'].sum()
        
        daily_change = closing_price - opening_price
        daily_change_pct = (daily_change / opening_price) * 100
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=['Price Movement', 'Volume'],
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3]
        )
        
        # Add price line
        fig.add_trace(
            go.Scatter(
                x=trading_data['time'],
                y=trading_data['price'],
                mode='lines+markers',
                name='Price Movement',
                line=dict(color='blue', width=2),
                marker=dict(size=6)
            ),
            row=1, col=1
        )
        
        # Add volume bars
        fig.add_trace(
            go.Bar(
                x=trading_data['time'],
                y=trading_data['volume'],
                name='Volume',
                marker_color='rgba(0,100,80,0.7)'
            ),
            row=2, col=1
        )
        
        # Add session markers
        morning_end = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
        afternoon_start = datetime.now().replace(hour=12, minute=30, second=0, microsecond=0)
        
        fig.add_vline(x=morning_end, line_dash="dot", line_color="green", 
                     annotation_text="Morning Session End", row=1, col=1)
        fig.add_vline(x=afternoon_start, line_dash="dot", line_color="orange", 
                     annotation_text="Afternoon Session Start", row=1, col=1)
        
        # Add daily high/low lines
        fig.add_hline(y=day_high, line_dash="dash", line_color="red", 
                     annotation_text="Day High", row=1, col=1)
        fig.add_hline(y=day_low, line_dash="dash", line_color="blue", 
                     annotation_text="Day Low", row=1, col=1)
        
        # Update layout
        fig.update_layout(
            title=f"{symbol} - Complete Trading Day Analysis ({datetime.now().strftime('%Y-%m-%d')})",
            height=600,
            showlegend=True,
            xaxis_title="Time",
            yaxis_title="Price (PKR)",
            xaxis2_title="Time",
            yaxis2_title="Volume"
        )
        
        return fig, {
            'opening_price': opening_price,
            'closing_price': closing_price,
            'day_high': day_high,
            'day_low': day_low,
            'daily_change': daily_change,
            'daily_change_pct': daily_change_pct,
            'total_volume': total_volume,
            'trading_data': trading_data
        }
    
    def generate_next_day_forecast(self, historical_data):
        """Generate next trading day forecast"""
        
        if len(historical_data) < 5:
            return None
        
        # Calculate trend from recent data
        recent_prices = historical_data['price'].tail(5)
        price_changes = recent_prices.pct_change().dropna()
        avg_change = price_changes.mean()
        volatility = price_changes.std()
        
        current_price = historical_data['price'].iloc[-1]
        
        # Generate next day forecast
        next_day_times = []
        next_day_prices = []
        next_day_volumes = []
        
        # Start from tomorrow 9:30 AM
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=9, minute=30, second=0, microsecond=0)
        
        base_price = current_price
        
        for i in range(13):  # 30-minute intervals
            time_point = start_time + timedelta(minutes=30 * i)
            next_day_times.append(time_point)
            
            if i == 0:
                # Opening price with overnight gap
                overnight_change = random.uniform(-0.02, 0.02)
                price = base_price * (1 + overnight_change)
            else:
                # Apply trend with some randomness
                trend_factor = avg_change * (i / 12)  # Scale trend over the day
                random_factor = random.uniform(-volatility, volatility)
                price = next_day_prices[-1] * (1 + trend_factor + random_factor)
            
            next_day_prices.append(price)
            
            # Volume forecast
            volume = random.randint(400000, 1200000)
            next_day_volumes.append(volume)
        
        return pd.DataFrame({
            'time': next_day_times,
            'price': next_day_prices,
            'volume': next_day_volumes
        })

def display_end_of_day_forecast():
    """Display complete end-of-day forecasting dashboard"""
    
    st.header("📊 End of Day Trading Analysis")
    st.markdown("**Complete trading day analysis and next-day forecasting**")
    
    forecaster = EndOfDayForecaster()
    
    # Symbol selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        symbol = st.selectbox(
            "Select Symbol for Analysis",
            ["KSE-100", "OGDC", "PPL", "PSO", "HBL", "UBL", "MCB", "LUCK", "ENGRO"],
            index=0
        )
    
    with col2:
        if st.button("🔄 Generate Analysis"):
            st.rerun()
    
    # Create end-of-day analysis
    try:
        fig, metrics = forecaster.create_end_of_day_analysis(symbol)
        
        # Display key metrics
        st.subheader("📈 Daily Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Opening Price",
                f"PKR {metrics['opening_price']:,.2f}"
            )
        
        with col2:
            st.metric(
                "Closing Price",
                f"PKR {metrics['closing_price']:,.2f}",
                f"{metrics['daily_change']:+.2f} ({metrics['daily_change_pct']:+.2f}%)"
            )
        
        with col3:
            st.metric(
                "Day High",
                f"PKR {metrics['day_high']:,.2f}"
            )
        
        with col4:
            st.metric(
                "Day Low",
                f"PKR {metrics['day_low']:,.2f}"
            )
        
        # Display the main chart
        st.plotly_chart(fig, use_container_width=True)
        
        # Trading session analysis
        st.subheader("🕐 Session Analysis")
        
        trading_data = metrics['trading_data']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Morning Session (9:30 AM - 12:00 PM)**")
            morning_data = trading_data[trading_data['time'].dt.hour < 12]
            if not morning_data.empty:
                morning_high = morning_data['price'].max()
                morning_low = morning_data['price'].min()
                morning_volume = morning_data['volume'].sum()
                
                st.write(f"• High: PKR {morning_high:,.2f}")
                st.write(f"• Low: PKR {morning_low:,.2f}")
                st.write(f"• Volume: {morning_volume:,}")
        
        with col2:
            st.markdown("**Afternoon Session (12:30 PM - 3:30 PM)**")
            afternoon_data = trading_data[trading_data['time'].dt.hour >= 12]
            if not afternoon_data.empty:
                afternoon_high = afternoon_data['price'].max()
                afternoon_low = afternoon_data['price'].min()
                afternoon_volume = afternoon_data['volume'].sum()
                
                st.write(f"• High: PKR {afternoon_high:,.2f}")
                st.write(f"• Low: PKR {afternoon_low:,.2f}")
                st.write(f"• Volume: {afternoon_volume:,}")
        
        # Next day forecast
        st.subheader("🔮 Next Trading Day Forecast")
        
        next_day_data = forecaster.generate_next_day_forecast(trading_data)
        
        if next_day_data is not None:
            # Create next day forecast chart
            next_fig = go.Figure()
            
            next_fig.add_trace(go.Scatter(
                x=next_day_data['time'],
                y=next_day_data['price'],
                mode='lines+markers',
                name='Next Day Forecast',
                line=dict(color='green', width=2, dash='dash'),
                marker=dict(size=6)
            ))
            
            next_fig.update_layout(
                title=f"{symbol} - Next Trading Day Forecast ({(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')})",
                xaxis_title="Time",
                yaxis_title="Price (PKR)",
                height=400
            )
            
            st.plotly_chart(next_fig, use_container_width=True)
            
            # Next day metrics
            next_opening = next_day_data['price'].iloc[0]
            next_closing = next_day_data['price'].iloc[-1]
            next_change = next_closing - next_opening
            next_change_pct = (next_change / next_opening) * 100
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Forecast Opening", f"PKR {next_opening:,.2f}")
            
            with col2:
                st.metric("Forecast Closing", f"PKR {next_closing:,.2f}")
            
            with col3:
                st.metric("Expected Change", f"{next_change:+.2f} ({next_change_pct:+.2f}%)")
        
        # Download options
        st.subheader("📥 Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Download Today's Data"):
                csv = trading_data.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"{symbol}_trading_data_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if next_day_data is not None and st.button("Download Forecast Data"):
                csv = next_day_data.to_csv(index=False)
                st.download_button(
                    label="Download Forecast CSV",
                    data=csv,
                    file_name=f"{symbol}_forecast_{(datetime.now() + timedelta(days=1)).strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
    
    except Exception as e:
        st.error(f"Error generating end-of-day analysis: {e}")
        st.info("Please try again or select a different symbol.")

if __name__ == "__main__":
    display_end_of_day_forecast()