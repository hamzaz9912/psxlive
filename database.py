import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import json

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    st.error("Database URL not found. Please check your environment variables.")
    st.stop()

# SQLAlchemy setup with SSL configuration
try:
    # Configure SSL connection for PostgreSQL
    engine = create_engine(
        DATABASE_URL, 
        connect_args={
            "sslmode": "require",
            "sslcert": None,
            "sslkey": None,
            "sslrootcert": None
        },
        pool_pre_ping=True,
        pool_recycle=300
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except Exception as e:
    st.warning(f"Database connection issue: {str(e)}")
    # Fallback to simple connection
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()

class StockData(Base):
    """Table to store historical stock data"""
    __tablename__ = "stock_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), index=True)  # e.g., 'KSE-100', 'OGDC'
    company_name = Column(String(200))
    date = Column(DateTime, index=True)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class ForecastData(Base):
    """Table to store forecast predictions"""
    __tablename__ = "forecast_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), index=True)
    forecast_date = Column(DateTime, index=True)
    predicted_price = Column(Float)
    confidence_lower = Column(Float)
    confidence_upper = Column(Float)
    forecast_type = Column(String(50))  # 'intraday', 'next_day', 'custom'
    model_used = Column(String(50))  # 'prophet', 'moving_average', etc.
    created_at = Column(DateTime, default=datetime.now)

class UserSettings(Base):
    """Table to store user preferences and settings"""
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(100), unique=True, index=True)
    setting_value = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class MarketEvents(Base):
    """Table to store significant market events and alerts"""
    __tablename__ = "market_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50))  # 'price_alert', 'forecast_accuracy', 'market_news'
    symbol = Column(String(10))
    event_data = Column(Text)  # JSON string
    event_date = Column(DateTime, index=True)
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

class DatabaseManager:
    """Class to handle all database operations"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
        self.create_tables()
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
        except Exception as e:
            st.error(f"Error creating database tables: {str(e)}")
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def store_stock_data(self, symbol, company_name, data_df):
        """
        Store historical stock data in the database
        
        Args:
            symbol (str): Stock symbol
            company_name (str): Company name
            data_df (pd.DataFrame): Historical stock data
        """
        session = self.get_session()
        try:
            for _, row in data_df.iterrows():
                # Check if record already exists
                existing = session.query(StockData).filter(
                    StockData.symbol == symbol,
                    StockData.date == row['date']
                ).first()
                
                if not existing:
                    # Ensure datetime is timezone-naive
                    date_value = pd.to_datetime(row['date'])
                    if date_value.tz is not None:
                        date_value = date_value.tz_localize(None)
                    
                    stock_record = StockData(
                        symbol=symbol,
                        company_name=company_name,
                        date=date_value,
                        open_price=float(row['open']),
                        high_price=float(row['high']),
                        low_price=float(row['low']),
                        close_price=float(row['close']),
                        volume=float(row['volume']) if pd.notna(row['volume']) else 0
                    )
                    session.add(stock_record)
                else:
                    # Update existing record
                    existing.open_price = float(row['open'])
                    existing.high_price = float(row['high'])
                    existing.low_price = float(row['low'])
                    existing.close_price = float(row['close'])
                    existing.volume = float(row['volume']) if pd.notna(row['volume']) else 0
                    existing.updated_at = datetime.now()
            
            session.commit()
        except Exception as e:
            session.rollback()
            st.error(f"Error storing stock data: {str(e)}")
        finally:
            session.close()
    
    def get_stock_data(self, symbol, days=30):
        """
        Retrieve historical stock data from database
        
        Args:
            symbol (str): Stock symbol
            days (int): Number of days to retrieve
            
        Returns:
            pd.DataFrame: Historical stock data
        """
        try:
            session = self.get_session()
            try:
                query = session.query(StockData).filter(
                    StockData.symbol == symbol
                ).order_by(StockData.date.desc()).limit(days)
                
                records = query.all()
                
                if not records:
                    return self._generate_sample_data(symbol, days)
                
                data = []
                for record in reversed(records):  # Reverse to get chronological order
                    data.append({
                        'date': record.date,
                        'open': record.open_price,
                        'high': record.high_price,
                        'low': record.low_price,
                        'close': record.close_price,
                        'volume': record.volume
                    })
                
                return pd.DataFrame(data)
                
            except Exception as e:
                st.warning(f"Database connection issue: {str(e)}")
                return self._generate_sample_data(symbol, days)
            finally:
                session.close()
        except Exception as e:
            st.warning(f"Database session issue: {str(e)}")
            return self._generate_sample_data(symbol, days)
    
    def _generate_sample_data(self, symbol, days=30):
        """Generate sample data when database is unavailable"""
        from datetime import datetime, timedelta
        import numpy as np
        
        # Base prices for different symbols - updated to current market levels
        base_prices = {
            'KSE-100': 132920,  # Updated to current price
            'OGDC': 85,
            'PPL': 75,
            'PSO': 190,
            'HBL': 110,
            'UBL': 95,
            'MCB': 145
        }
        
        base_price = base_prices.get(symbol, 100)
        
        # Generate sample data
        data = []
        current_date = datetime.now() - timedelta(days=days)
        current_price = base_price
        
        for i in range(days):
            # Add some realistic price movement
            change = np.random.normal(0, 0.02)
            current_price = current_price * (1 + change)
            
            data.append({
                'date': current_date + timedelta(days=i),
                'open': current_price * 0.995,
                'high': current_price * 1.02,
                'low': current_price * 0.98,
                'close': current_price,
                'volume': np.random.randint(10000, 100000)
            })
        
        return pd.DataFrame(data)
    
    def store_forecast(self, symbol, forecast_date, predicted_price, confidence_lower, 
                      confidence_upper, forecast_type, model_used):
        """
        Store forecast prediction in database
        
        Args:
            symbol (str): Stock symbol
            forecast_date (datetime): Date of forecast
            predicted_price (float): Predicted price
            confidence_lower (float): Lower confidence bound
            confidence_upper (float): Upper confidence bound
            forecast_type (str): Type of forecast
            model_used (str): Model used for forecast
        """
        session = self.get_session()
        try:
            forecast_record = ForecastData(
                symbol=symbol,
                forecast_date=pd.to_datetime(forecast_date),
                predicted_price=float(predicted_price),
                confidence_lower=float(confidence_lower),
                confidence_upper=float(confidence_upper),
                forecast_type=forecast_type,
                model_used=model_used
            )
            session.add(forecast_record)
            session.commit()
        except Exception as e:
            session.rollback()
            st.error(f"Error storing forecast: {str(e)}")
        finally:
            session.close()
    
    def get_forecast_history(self, symbol, days=7):
        """
        Get forecast history for a symbol
        
        Args:
            symbol (str): Stock symbol
            days (int): Number of days to look back
            
        Returns:
            pd.DataFrame: Forecast history
        """
        session = self.get_session()
        try:
            cutoff_date = datetime.now() - pd.Timedelta(days=days)
            
            query = session.query(ForecastData).filter(
                ForecastData.symbol == symbol,
                ForecastData.created_at >= cutoff_date
            ).order_by(ForecastData.created_at.desc())
            
            records = query.all()
            
            if not records:
                return None
            
            data = []
            for record in records:
                data.append({
                    'forecast_date': record.forecast_date,
                    'predicted_price': record.predicted_price,
                    'confidence_lower': record.confidence_lower,
                    'confidence_upper': record.confidence_upper,
                    'forecast_type': record.forecast_type,
                    'model_used': record.model_used,
                    'created_at': record.created_at
                })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            st.error(f"Error retrieving forecast history: {str(e)}")
            return None
        finally:
            session.close()
    
    def save_user_setting(self, key, value):
        """
        Save user setting to database
        
        Args:
            key (str): Setting key
            value: Setting value (will be JSON serialized)
        """
        session = self.get_session()
        try:
            # Check if setting exists
            existing = session.query(UserSettings).filter(
                UserSettings.setting_key == key
            ).first()
            
            value_json = json.dumps(value) if not isinstance(value, str) else value
            
            if existing:
                existing.setting_value = value_json
                existing.updated_at = datetime.now()
            else:
                setting = UserSettings(
                    setting_key=key,
                    setting_value=value_json
                )
                session.add(setting)
            
            session.commit()
        except Exception as e:
            session.rollback()
            st.error(f"Error saving user setting: {str(e)}")
        finally:
            session.close()
    
    def get_user_setting(self, key, default=None):
        """
        Get user setting from database
        
        Args:
            key (str): Setting key
            default: Default value if not found
            
        Returns:
            Setting value or default
        """
        session = self.get_session()
        try:
            setting = session.query(UserSettings).filter(
                UserSettings.setting_key == key
            ).first()
            
            if setting:
                try:
                    return json.loads(setting.setting_value)
                except json.JSONDecodeError:
                    return setting.setting_value
            else:
                return default
                
        except Exception as e:
            st.error(f"Error retrieving user setting: {str(e)}")
            return default
        finally:
            session.close()
    
    def log_market_event(self, event_type, symbol, event_data):
        """
        Log market event to database
        
        Args:
            event_type (str): Type of event
            symbol (str): Stock symbol
            event_data (dict): Event data
        """
        session = self.get_session()
        try:
            event = MarketEvents(
                event_type=event_type,
                symbol=symbol,
                event_data=json.dumps(event_data),
                event_date=datetime.now()
            )
            session.add(event)
            session.commit()
        except Exception as e:
            session.rollback()
            st.error(f"Error logging market event: {str(e)}")
        finally:
            session.close()
    
    def get_market_summary_from_db(self):
        """
        Get market summary statistics from database
        
        Returns:
            dict: Market summary data
        """
        session = self.get_session()
        try:
            # Get latest prices for all symbols
            latest_prices = {}
            symbols = session.query(StockData.symbol).distinct().all()
            
            for (symbol,) in symbols:
                latest = session.query(StockData).filter(
                    StockData.symbol == symbol
                ).order_by(StockData.date.desc()).first()
                
                if latest:
                    latest_prices[symbol] = {
                        'current_price': latest.close_price,
                        'date': latest.date,
                        'volume': latest.volume
                    }
            
            return latest_prices
            
        except Exception as e:
            st.error(f"Error getting market summary: {str(e)}")
            return {}
        finally:
            session.close()

# Global database manager instance
@st.cache_resource
def get_database_manager():
    """Get cached database manager instance"""
    return DatabaseManager()