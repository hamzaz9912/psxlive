"""
Universal File Upload Predictor Module - Simplified and Robust
Handles any uploaded financial data (CSV, Excel) and generates predictions
Supports any brand: XAUSD, PSX companies, forex, commodities, etc.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import re
from simple_file_reader import read_any_file, analyze_dataframe

class UniversalPredictor:
    """Universal predictor for any uploaded financial data"""
    
    def __init__(self):
        self.supported_formats = ['.csv', '.xlsx', '.xls']
        
    def process_uploaded_file(self, uploaded_file, brand_name="Unknown"):
        """Process uploaded file and extract financial data"""
        try:
            # Use robust file reader
            df, error_message = read_any_file(uploaded_file)
            
            if df is None:
                return {'error': error_message}
            
            # Analyze the dataframe structure
            analysis = analyze_dataframe(df, brand_name)
            
            if 'error' in analysis:
                return analysis
            
            # Add success flag and dataframe
            analysis['success'] = True
            analysis['dataframe'] = df
            
            return analysis
            
        except Exception as e:
            return {'error': f'Error processing file: {str(e)}'}
    
    def generate_predictions(self, df, brand_name, price_column, date_column=None):
        """Generate predictions based on uploaded data"""
        try:
            # Validate price column
            if price_column not in df.columns:
                return {'error': f'Price column "{price_column}" not found in data'}
            
            # Convert price column to numeric
            try:
                price_data = pd.to_numeric(df[price_column], errors='coerce')
                price_data = price_data.dropna()
                
                if len(price_data) == 0:
                    return {'error': f'No valid numeric data found in price column "{price_column}"'}
                    
            except Exception as e:
                return {'error': f'Cannot convert price column to numeric: {str(e)}'}
            
            # Get current price and basic statistics
            current_price = float(price_data.iloc[-1])
            volatility = float(price_data.pct_change().std())
            trend = float((price_data.iloc[-1] - price_data.iloc[0]) / price_data.iloc[0]) if len(price_data) > 1 else 0.0
            
            # Generate predictions
            predictions = {
                'current_price': current_price,
                'volatility': volatility,
                'trend': trend,
                'data_points': len(price_data),
                'predictions': {
                    'short_term': self._generate_short_term_prediction(current_price, trend, volatility, brand_name),
                    'medium_term': self._generate_medium_term_prediction(current_price, trend, volatility, brand_name),
                    'long_term': self._generate_long_term_prediction(current_price, trend, volatility, brand_name)
                },
                'technical_analysis': self._perform_technical_analysis(price_data)
            }
            
            return predictions
            
        except Exception as e:
            return {'error': f'Error generating predictions: {str(e)}'}
    
    def _generate_short_term_prediction(self, current_price, trend, volatility, brand_name):
        """Generate short-term predictions (1-7 days)"""
        predictions = []
        
        for i in range(1, 8):  # Next 7 days
            # Simple prediction model with trend and volatility
            daily_change = trend + np.random.normal(0, volatility) * 0.1
            predicted_price = current_price * (1 + daily_change)
            
            predictions.append({
                'date': (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d'),
                'predicted_price': round(predicted_price, 4),
                'confidence': max(0.5, 1 - abs(daily_change))
            })
            
            current_price = predicted_price
        
        return predictions
    
    def _generate_medium_term_prediction(self, current_price, trend, volatility, brand_name):
        """Generate medium-term predictions (1-4 weeks)"""
        predictions = []
        
        for i in range(1, 5):  # Next 4 weeks
            weekly_change = trend * 7 + np.random.normal(0, volatility) * 0.3
            predicted_price = current_price * (1 + weekly_change)
            
            predictions.append({
                'week': i,
                'date': (datetime.now() + timedelta(weeks=i)).strftime('%Y-%m-%d'),
                'predicted_price': round(predicted_price, 4),
                'confidence': max(0.3, 1 - abs(weekly_change))
            })
            
            current_price = predicted_price
        
        return predictions
    
    def _generate_long_term_prediction(self, current_price, trend, volatility, brand_name):
        """Generate long-term predictions (1-3 months)"""
        predictions = []
        
        for i in range(1, 4):  # Next 3 months
            monthly_change = trend * 30 + np.random.normal(0, volatility) * 0.5
            predicted_price = current_price * (1 + monthly_change)
            
            predictions.append({
                'month': i,
                'date': (datetime.now() + timedelta(days=30*i)).strftime('%Y-%m-%d'),
                'predicted_price': round(predicted_price, 4),
                'confidence': max(0.2, 1 - abs(monthly_change))
            })
            
            current_price = predicted_price
        
        return predictions
    
    def _perform_technical_analysis(self, price_data):
        """Perform basic technical analysis"""
        try:
            if len(price_data) < 5:
                return {'error': 'Not enough data for technical analysis'}
            
            # Moving averages
            ma_5 = price_data.rolling(5).mean().iloc[-1] if len(price_data) >= 5 else None
            ma_10 = price_data.rolling(10).mean().iloc[-1] if len(price_data) >= 10 else None
            ma_20 = price_data.rolling(20).mean().iloc[-1] if len(price_data) >= 20 else None
            
            # RSI calculation (simplified)
            delta = price_data.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            if len(gain) >= 14:
                avg_gain = gain.rolling(14).mean().iloc[-1]
                avg_loss = loss.rolling(14).mean().iloc[-1]
                rs = avg_gain / avg_loss if avg_loss != 0 else 0
                rsi = 100 - (100 / (1 + rs))
            else:
                rsi = 50  # Neutral RSI
            
            # Support and resistance levels
            support_level = float(price_data.min())
            resistance_level = float(price_data.max())
            
            return {
                'moving_averages': {
                    'ma_5': float(ma_5) if ma_5 is not None else None,
                    'ma_10': float(ma_10) if ma_10 is not None else None,
                    'ma_20': float(ma_20) if ma_20 is not None else None
                },
                'rsi': float(rsi),
                'support_level': support_level,
                'resistance_level': resistance_level
            }
            
        except Exception as e:
            return {'error': f'Technical analysis failed: {str(e)}'}
    
    def create_prediction_chart(self, df, predictions, price_column, date_column=None):
        """Create interactive prediction chart"""
        try:
            fig = go.Figure()
            
            # Historical data
            if date_column and date_column in df.columns:
                x_data = df[date_column]
            else:
                x_data = range(len(df))
            
            fig.add_trace(go.Scatter(
                x=x_data,
                y=df[price_column],
                mode='lines',
                name='Historical Data',
                line=dict(color='blue', width=2)
            ))
            
            # Short-term predictions
            short_term = predictions['predictions']['short_term']
            pred_dates = [pred['date'] for pred in short_term]
            pred_prices = [pred['predicted_price'] for pred in short_term]
            
            fig.add_trace(go.Scatter(
                x=pred_dates,
                y=pred_prices,
                mode='lines+markers',
                name='Short-term Predictions',
                line=dict(color='red', width=2, dash='dash'),
                marker=dict(size=6)
            ))
            
            fig.update_layout(
                title=f'Price Predictions for {predictions.get("brand", "Unknown")}',
                xaxis_title='Date',
                yaxis_title='Price',
                height=500
            )
            
            return fig
            
        except Exception as e:
            return None

# Global instance
_universal_predictor = None

def get_universal_predictor():
    """Get universal predictor instance"""
    global _universal_predictor
    if _universal_predictor is None:
        _universal_predictor = UniversalPredictor()
    return _universal_predictor