"""
Universal File Upload Predictor Module
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

class UniversalPredictor:
    """Universal predictor for any uploaded financial data"""
    
    def __init__(self):
        self.supported_formats = ['.csv', '.xlsx', '.xls']
        self.common_price_columns = [
            'close', 'Close', 'CLOSE', 'price', 'Price', 'PRICE',
            'last', 'Last', 'LAST', 'value', 'Value', 'VALUE'
        ]
        self.common_date_columns = [
            'date', 'Date', 'DATE', 'time', 'Time', 'TIME',
            'datetime', 'DateTime', 'DATETIME', 'timestamp', 'Timestamp'
        ]
        
    def process_uploaded_file(self, uploaded_file, brand_name="Unknown"):
        """Process uploaded file and extract financial data"""
        try:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            if file_extension == 'csv':
                # Read CSV file
                df = pd.read_csv(uploaded_file)
            elif file_extension in ['xlsx', 'xls']:
                # Read Excel file
                df = pd.read_excel(uploaded_file)
            else:
                return {'error': f'Unsupported file format: {file_extension}'}
            
            # Analyze the data structure
            analysis = self._analyze_data_structure(df, brand_name)
            
            return analysis
            
        except Exception as e:
            return {'error': f'Error processing file: {str(e)}'}
    
    def _analyze_data_structure(self, df, brand_name):
        """Analyze the structure of uploaded data"""
        try:
            # Basic info
            analysis = {
                'brand_name': brand_name,
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'columns': list(df.columns),
                'data_types': df.dtypes.to_dict(),
                'has_price_data': False,
                'has_date_data': False,
                'price_column': None,
                'date_column': None,
                'data_range': None,
                'sample_data': df.head(3).to_dict('records')
            }
            
            # Identify price column
            for col in df.columns:
                if any(price_col.lower() in col.lower() for price_col in self.common_price_columns):
                    analysis['price_column'] = col
                    analysis['has_price_data'] = True
                    break
            
            # Identify date column
            for col in df.columns:
                if any(date_col.lower() in col.lower() for date_col in self.common_date_columns):
                    analysis['date_column'] = col
                    analysis['has_date_data'] = True
                    break
            
            # If price column found, get price statistics
            if analysis['price_column']:
                price_data = pd.to_numeric(df[analysis['price_column']], errors='coerce')
                price_data = price_data.dropna()
                
                if len(price_data) > 0:
                    analysis['price_stats'] = {
                        'min': float(price_data.min()),
                        'max': float(price_data.max()),
                        'mean': float(price_data.mean()),
                        'current': float(price_data.iloc[-1]),
                        'previous': float(price_data.iloc[-2]) if len(price_data) > 1 else None,
                        'change': float(price_data.iloc[-1] - price_data.iloc[-2]) if len(price_data) > 1 else 0
                    }
            
            # If date column found, get date range
            if analysis['date_column']:
                try:
                    date_data = pd.to_datetime(df[analysis['date_column']], errors='coerce')
                    date_data = date_data.dropna()
                    
                    if len(date_data) > 0:
                        analysis['data_range'] = {
                            'start': date_data.min().strftime('%Y-%m-%d'),
                            'end': date_data.max().strftime('%Y-%m-%d'),
                            'total_days': (date_data.max() - date_data.min()).days
                        }
                except Exception:
                    pass
            
            return analysis
            
        except Exception as e:
            return {'error': f'Error analyzing data: {str(e)}'}
    
    def generate_predictions(self, df, brand_name, price_column, date_column=None):
        """Generate predictions based on uploaded data"""
        try:
            # Prepare data
            price_data = pd.to_numeric(df[price_column], errors='coerce').dropna()
            
            if len(price_data) < 5:
                return {'error': 'Insufficient data for prediction (need at least 5 data points)'}
            
            # Calculate trends and patterns
            returns = price_data.pct_change().dropna()
            volatility = returns.std()
            trend = returns.mean()
            
            current_price = price_data.iloc[-1]
            
            # Generate different types of predictions
            predictions = {
                'brand_name': brand_name,
                'current_price': current_price,
                'data_points': len(price_data),
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'volatility': volatility,
                'trend': trend,
                'predictions': {}
            }
            
            # Short-term prediction (next 1-7 days)
            predictions['predictions']['short_term'] = self._generate_short_term_prediction(
                current_price, trend, volatility, brand_name
            )
            
            # Medium-term prediction (next 1-4 weeks)
            predictions['predictions']['medium_term'] = self._generate_medium_term_prediction(
                current_price, trend, volatility, brand_name
            )
            
            # Long-term prediction (next 1-3 months)
            predictions['predictions']['long_term'] = self._generate_long_term_prediction(
                current_price, trend, volatility, brand_name
            )
            
            # Technical analysis
            predictions['technical_analysis'] = self._perform_technical_analysis(price_data)
            
            return predictions
            
        except Exception as e:
            return {'error': f'Error generating predictions: {str(e)}'}
    
    def _generate_short_term_prediction(self, current_price, trend, volatility, brand_name):
        """Generate short-term predictions (1-7 days)"""
        predictions = []
        
        for day in range(1, 8):
            # Apply trend and volatility
            random_factor = np.random.normal(0, volatility)
            trend_factor = trend * day
            
            predicted_price = current_price * (1 + trend_factor + random_factor)
            
            predictions.append({
                'day': day,
                'date': (datetime.now() + timedelta(days=day)).strftime('%Y-%m-%d'),
                'predicted_price': round(predicted_price, 4),
                'change': round(predicted_price - current_price, 4),
                'change_percent': round(((predicted_price - current_price) / current_price) * 100, 2),
                'confidence': max(0.6, 0.9 - (day * 0.05))  # Decreasing confidence over time
            })
        
        return predictions
    
    def _generate_medium_term_prediction(self, current_price, trend, volatility, brand_name):
        """Generate medium-term predictions (1-4 weeks)"""
        predictions = []
        
        for week in range(1, 5):
            # Medium-term trend adjustment
            trend_adjustment = trend * week * 7 * 0.8  # Slightly damped
            volatility_adjustment = np.random.normal(0, volatility * 0.7)
            
            predicted_price = current_price * (1 + trend_adjustment + volatility_adjustment)
            
            predictions.append({
                'week': week,
                'date': (datetime.now() + timedelta(weeks=week)).strftime('%Y-%m-%d'),
                'predicted_price': round(predicted_price, 4),
                'change': round(predicted_price - current_price, 4),
                'change_percent': round(((predicted_price - current_price) / current_price) * 100, 2),
                'confidence': max(0.4, 0.8 - (week * 0.1))
            })
        
        return predictions
    
    def _generate_long_term_prediction(self, current_price, trend, volatility, brand_name):
        """Generate long-term predictions (1-3 months)"""
        predictions = []
        
        for month in range(1, 4):
            # Long-term trend with mean reversion
            trend_adjustment = trend * month * 30 * 0.6  # More damped
            volatility_adjustment = np.random.normal(0, volatility * 0.5)
            
            predicted_price = current_price * (1 + trend_adjustment + volatility_adjustment)
            
            predictions.append({
                'month': month,
                'date': (datetime.now() + timedelta(days=month*30)).strftime('%Y-%m-%d'),
                'predicted_price': round(predicted_price, 4),
                'change': round(predicted_price - current_price, 4),
                'change_percent': round(((predicted_price - current_price) / current_price) * 100, 2),
                'confidence': max(0.3, 0.7 - (month * 0.15))
            })
        
        return predictions
    
    def _perform_technical_analysis(self, price_data):
        """Perform basic technical analysis"""
        try:
            # Moving averages
            ma_5 = price_data.rolling(window=5).mean().iloc[-1] if len(price_data) >= 5 else None
            ma_10 = price_data.rolling(window=10).mean().iloc[-1] if len(price_data) >= 10 else None
            ma_20 = price_data.rolling(window=20).mean().iloc[-1] if len(price_data) >= 20 else None
            
            # RSI (simplified)
            delta = price_data.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1] if len(rsi) > 0 else 50
            
            # Support and resistance levels
            support = price_data.rolling(window=20).min().iloc[-1] if len(price_data) >= 20 else price_data.min()
            resistance = price_data.rolling(window=20).max().iloc[-1] if len(price_data) >= 20 else price_data.max()
            
            return {
                'moving_averages': {
                    'ma_5': round(ma_5, 4) if ma_5 is not None else None,
                    'ma_10': round(ma_10, 4) if ma_10 is not None else None,
                    'ma_20': round(ma_20, 4) if ma_20 is not None else None
                },
                'rsi': round(current_rsi, 2),
                'support_level': round(support, 4),
                'resistance_level': round(resistance, 4),
                'trend_signal': 'bullish' if current_rsi < 30 else 'bearish' if current_rsi > 70 else 'neutral'
            }
            
        except Exception as e:
            return {'error': f'Technical analysis error: {str(e)}'}
    
    def create_prediction_chart(self, df, predictions, price_column, date_column=None):
        """Create interactive prediction chart"""
        try:
            # Prepare historical data
            price_data = pd.to_numeric(df[price_column], errors='coerce').dropna()
            
            if date_column:
                date_data = pd.to_datetime(df[date_column], errors='coerce')
                dates = date_data.dropna()
            else:
                dates = pd.date_range(start=datetime.now() - timedelta(days=len(price_data)), 
                                     periods=len(price_data), freq='D')
            
            # Create subplot
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Price History & Predictions', 'Technical Indicators'),
                vertical_spacing=0.1,
                row_heights=[0.7, 0.3]
            )
            
            # Historical price data
            fig.add_trace(
                go.Scatter(
                    x=dates[:len(price_data)],
                    y=price_data,
                    mode='lines',
                    name='Historical Price',
                    line=dict(color='blue', width=2)
                ),
                row=1, col=1
            )
            
            # Short-term predictions
            if 'short_term' in predictions['predictions']:
                pred_dates = [datetime.strptime(pred['date'], '%Y-%m-%d') 
                             for pred in predictions['predictions']['short_term']]
                pred_prices = [pred['predicted_price'] 
                              for pred in predictions['predictions']['short_term']]
                
                fig.add_trace(
                    go.Scatter(
                        x=pred_dates,
                        y=pred_prices,
                        mode='lines+markers',
                        name='Short-term Prediction',
                        line=dict(color='red', width=2, dash='dash'),
                        marker=dict(size=6)
                    ),
                    row=1, col=1
                )
            
            # Add technical indicators
            if 'technical_analysis' in predictions:
                tech = predictions['technical_analysis']
                
                # Support and resistance lines
                fig.add_hline(
                    y=tech['support_level'],
                    line_dash="dot",
                    line_color="green",
                    annotation_text="Support",
                    row=1, col=1
                )
                
                fig.add_hline(
                    y=tech['resistance_level'],
                    line_dash="dot",
                    line_color="red",
                    annotation_text="Resistance",
                    row=1, col=1
                )
                
                # RSI indicator
                fig.add_trace(
                    go.Scatter(
                        x=[dates[-1]],
                        y=[tech['rsi']],
                        mode='markers',
                        name='RSI',
                        marker=dict(size=10, color='purple')
                    ),
                    row=2, col=1
                )
            
            # Update layout
            fig.update_layout(
                title=f"{predictions['brand_name']} - Price Analysis & Predictions",
                xaxis_title="Date",
                yaxis_title="Price",
                height=600,
                showlegend=True,
                hovermode='x unified'
            )
            
            return fig
            
        except Exception as e:
            print(f"Error creating prediction chart: {e}")
            return None

def get_universal_predictor():
    """Get universal predictor instance"""
    return UniversalPredictor()