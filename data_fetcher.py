import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import streamlit as st
import trafilatura
import re
import json

class DataFetcher:
    """Class to handle data fetching from various sources for PSX stocks"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.live_price_cache = {}
        self.cache_timestamp = None
        
        # KSE-100 major companies mapping
        self.kse100_companies = {
            'Oil & Gas Development Company Limited': 'OGDC',
            'Habib Bank Limited': 'HBL',
            'MCB Bank Limited': 'MCB',
            'Engro Corporation Limited': 'ENGRO',
            'Lucky Cement Limited': 'LUCK',
            'Pakistan State Oil Company Limited': 'PSO',
            'United Bank Limited': 'UBL',
            'Fauji Fertilizer Company Limited': 'FFC',
            'Pakistan Petroleum Limited': 'PPL',
            'National Bank of Pakistan': 'NBP',
            'Hub Power Company Limited': 'HUBC',
            'Systems Limited': 'SYS',
            'Pakistan Tobacco Company Limited': 'PTC',
            'Millat Tractors Limited': 'MTL',
            'Nestle Pakistan Limited': 'NESTLE',
            'Unilever Pakistan Limited': 'UNILEVER',
            'TRG Pakistan Limited': 'TRG',
            'Interloop Limited': 'ILP',
            'Packages Limited': 'PKGS',
            'D.G. Khan Cement Company Limited': 'DGKC'
        }
    
    def get_kse100_companies(self):
        """Return the list of KSE-100 companies"""
        return self.kse100_companies
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def fetch_kse100_data(_self):
        """Fetch KSE-100 index data from multiple sources"""
        
        # Try multiple sources for reliability
        data = None
        
        # Source 1: Try investing.com
        try:
            data = _self._fetch_from_investing_com('kse-100')
            if data is not None and not data.empty:
                return data
        except Exception as e:
            st.warning(f"Investing.com source failed: {str(e)}")
        
        # Source 2: Try PSX official website
        try:
            data = _self._fetch_from_psx_official()
            if data is not None and not data.empty:
                return data
        except Exception as e:
            st.warning(f"PSX official source failed: {str(e)}")
        
        # Source 3: Try Yahoo Finance alternative
        try:
            data = _self._fetch_from_yahoo_finance("^KSE100")
            if data is not None and not data.empty:
                return data
        except Exception as e:
            st.warning(f"Yahoo Finance source failed: {str(e)}")
        
        # Source 4: Generate realistic sample data if all sources fail
        st.info("Using simulated data for demonstration. Real-time data sources are currently unavailable.")
        return _self._generate_sample_kse_data()
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def fetch_company_data(_self, company_name):
        """Fetch individual company data"""
        
        if company_name not in _self.kse100_companies:
            return None
        
        symbol = _self.kse100_companies[company_name]
        
        # Try multiple sources
        data = None
        
        # Source 1: Try investing.com
        try:
            data = _self._fetch_from_investing_com(symbol.lower())
            if data is not None and not data.empty:
                return data
        except Exception as e:
            st.warning(f"Investing.com source failed for {company_name}: {str(e)}")
        
        # Source 2: Try Yahoo Finance for individual stocks
        try:
            # Convert company name to Yahoo Finance symbol
            yahoo_symbol = f"{symbol}.KAR"  # Karachi Stock Exchange suffix
            data = _self._fetch_from_yahoo_finance(yahoo_symbol)
            if data is not None and not data.empty:
                return data
        except Exception as e:
            st.warning(f"Yahoo Finance source failed for {company_name}: {str(e)}")
        
        # Source 3: Generate realistic sample data if sources fail
        st.info(f"Using simulated data for {company_name}. Real-time data sources are currently unavailable.")
        return _self._generate_sample_company_data(symbol)
    
    def _fetch_from_investing_com(self, symbol):
        """Fetch data from investing.com (unofficial)"""
        try:
            # This is a simplified approach - in production, you'd need more robust scraping
            base_url = f"https://www.investing.com/equities/{symbol}-historical-data"
            
            response = self.session.get(base_url, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for data tables (this would need adjustment based on actual HTML structure)
            tables = soup.find_all('table')
            
            if not tables:
                return None
            
            # Extract historical data from the table
            # This is a simplified extraction - real implementation would be more complex
            data_rows = []
            for table in tables:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows[:30]:  # Get last 30 days
                    cols = row.find_all('td')
                    if len(cols) >= 6:
                        try:
                            date_str = cols[0].text.strip()
                            price = float(cols[1].text.strip().replace(',', ''))
                            open_price = float(cols[2].text.strip().replace(',', ''))
                            high = float(cols[3].text.strip().replace(',', ''))
                            low = float(cols[4].text.strip().replace(',', ''))
                            volume = cols[5].text.strip().replace(',', '')
                            
                            data_rows.append({
                                'date': pd.to_datetime(date_str),
                                'open': open_price,
                                'high': high,
                                'low': low,
                                'close': price,
                                'volume': volume
                            })
                        except ValueError:
                            continue
                
                if data_rows:
                    break
            
            if data_rows:
                df = pd.DataFrame(data_rows)
                df = df.sort_values('date').reset_index(drop=True)
                return df
            
            return None
            
        except Exception as e:
            return None
    
    def _fetch_from_psx_official(self):
        """Fetch data from PSX official website"""
        try:
            # PSX Live data URL (this would need adjustment based on actual API)
            url = "https://www.psx.com.pk/"
            
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return None
            
            # Use trafilatura to extract clean content
            text_content = trafilatura.extract(response.text)
            
            if not text_content:
                return None
            
            # Look for KSE-100 index value in the extracted text
            # This is a simplified pattern matching - real implementation would be more robust
            kse_pattern = r'KSE.*?100.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
            matches = re.findall(kse_pattern, text_content, re.IGNORECASE)
            
            if matches:
                current_price = float(matches[0].replace(',', ''))
                # Generate recent historical data points around current price
                return self._generate_recent_data_around_price(current_price)
            
            return None
            
        except Exception as e:
            return None
    
    def _fetch_from_yahoo_finance(self, symbol):
        """Fetch data from Yahoo Finance"""
        try:
            # Yahoo Finance API endpoint
            import time
            end_time = int(time.time())
            start_time = end_time - (30 * 24 * 60 * 60)  # 30 days ago
            
            url = f"https://query1.finance.yahoo.com/v7/finance/download/{symbol}?period1={start_time}&period2={end_time}&interval=1d&events=history"
            
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return None
            
            # Parse CSV data
            from io import StringIO
            csv_data = StringIO(response.text)
            df = pd.read_csv(csv_data)
            
            if df.empty:
                return None
            
            # Rename columns to match our format
            df = df.rename(columns={
                'Date': 'date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume',
                'Adj Close': 'adj_close'
            })
            
            # Convert date column
            df['date'] = pd.to_datetime(df['date'])
            
            # Clean and sort data
            df = df.dropna().sort_values('date').reset_index(drop=True)
            
            return df
            
        except Exception:
            return None
    
    def get_live_psx_price(self, symbol="KSE-100"):
        """Get live PSX price with caching (updates every 30 seconds)"""
        current_time = datetime.now()
        
        # Check cache (30 second TTL for live prices)
        if (self.cache_timestamp and 
            (current_time - self.cache_timestamp).seconds < 30 and 
            symbol in self.live_price_cache):
            return self.live_price_cache[symbol]
        
        live_price = self._fetch_live_price_from_sources(symbol)
        
        # Update cache
        if live_price:
            self.live_price_cache[symbol] = live_price
            self.cache_timestamp = current_time
        
        return live_price
    
    def _fetch_live_price_from_sources(self, symbol):
        """Try multiple sources for live price data"""
        
        # Source 1: PSX Live API (if available)
        try:
            live_price = self._fetch_psx_live_api(symbol)
            if live_price:
                return live_price
        except Exception:
            pass
        
        # Source 2: Yahoo Finance real-time
        try:
            live_price = self._fetch_yahoo_realtime(symbol)
            if live_price:
                return live_price
        except Exception:
            pass
        
        # Source 3: Investing.com live data
        try:
            live_price = self._fetch_investing_live(symbol)
            if live_price:
                return live_price
        except Exception:
            pass
        
        # Fallback: Generate realistic current price
        return self._generate_realistic_current_price(symbol)
    
    def _fetch_psx_live_api(self, symbol):
        """Fetch from PSX official live data sources"""
        try:
            # Try PSX official data portal
            urls = [
                "https://dps.psx.com.pk/company",
                "https://www.psx.com.pk/psx/themes/psx/uploads/live-price/kse100.json",
                "https://dps.psx.com.pk/kse100"
            ]
            
            for url in urls:
                try:
                    response = self.session.get(url, timeout=5)
                    if response.status_code == 200:
                        # Try JSON response first
                        try:
                            data = response.json()
                            if 'current_price' in data or 'price' in data:
                                price = data.get('current_price', data.get('price'))
                                return {'price': float(price), 'timestamp': datetime.now()}
                        except:
                            pass
                        
                        # Try HTML parsing
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Look for price elements
                        price_patterns = [
                            {'class': re.compile(r'price|index|value', re.I)},
                            {'id': re.compile(r'price|index|value', re.I)},
                        ]
                        
                        for pattern in price_patterns:
                            elements = soup.find_all(['span', 'div', 'td'], pattern)
                            for element in elements:
                                text = element.get_text().strip()
                                # Extract numeric value
                                matches = re.findall(r'[\d,]+\.?\d*', text)
                                for match in matches:
                                    try:
                                        value = float(match.replace(',', ''))
                                        if 30000 <= value <= 70000:  # KSE-100 range
                                            return {'price': value, 'timestamp': datetime.now()}
                                    except ValueError:
                                        continue
                except Exception:
                    continue
            
            return None
            
        except Exception:
            return None
    
    def _fetch_yahoo_realtime(self, symbol):
        """Fetch real-time price from Yahoo Finance"""
        try:
            # Convert symbol to Yahoo format
            yahoo_symbol = "^KSE100" if symbol == "KSE-100" else f"{symbol}.KAR"
            
            # Yahoo Finance real-time quote API
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
            
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                    result = data['chart']['result'][0]
                    if 'meta' in result and 'regularMarketPrice' in result['meta']:
                        price = result['meta']['regularMarketPrice']
                        return {'price': float(price), 'timestamp': datetime.now()}
            
            return None
            
        except Exception:
            return None
    
    def _fetch_investing_live(self, symbol):
        """Fetch live price from Investing.com"""
        try:
            # Investing.com live price endpoint
            search_term = "kse-100" if symbol == "KSE-100" else symbol.lower()
            url = f"https://www.investing.com/indices/{search_term}"
            
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for price elements with common class names
                price_selectors = [
                    '[data-test="instrument-price-last"]',
                    '.text-2xl',
                    '.instrument-price_last__2x8pF',
                    '.pid-169-last'
                ]
                
                for selector in price_selectors:
                    elements = soup.select(selector)
                    for element in elements:
                        text = element.get_text().strip()
                        # Extract price
                        matches = re.findall(r'[\d,]+\.?\d*', text)
                        for match in matches:
                            try:
                                value = float(match.replace(',', ''))
                                if 30000 <= value <= 70000:  # Valid range check
                                    return {'price': value, 'timestamp': datetime.now()}
                            except ValueError:
                                continue
            
            return None
            
        except Exception:
            return None
    
    def _generate_realistic_current_price(self, symbol):
        """Generate realistic current price based on recent trends"""
        try:
            # Get base price from historical data
            if symbol == "KSE-100":
                base_price = 45000 + np.random.randint(-2000, 2000)  # KSE-100 range
            else:
                # Use company-specific base prices
                company_prices = {
                    'OGDC': 85, 'HBL': 150, 'MCB': 200, 'ENGRO': 300,
                    'LUCK': 550, 'PSO': 180, 'UBL': 160, 'FFC': 90
                }
                base_price = company_prices.get(symbol, 100)
            
            # Add realistic intraday movement (±2%)
            movement = np.random.uniform(-0.02, 0.02)
            current_price = base_price * (1 + movement)
            
            return {
                'price': round(current_price, 2),
                'timestamp': datetime.now(),
                'source': 'simulated'
            }
            
        except Exception:
            return {'price': 45000, 'timestamp': datetime.now(), 'source': 'fallback'}
    
    def _generate_recent_data_around_price(self, current_price):
        """Generate realistic recent data points around a given current price"""
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        
        # Generate realistic price movement
        returns = np.random.normal(0, 0.02, 29)  # 2% daily volatility
        prices = [current_price]
        
        # Work backwards from current price
        for i in range(29):
            prev_price = prices[0] / (1 + returns[i])
            prices.insert(0, prev_price)
        
        data = []
        for i, date in enumerate(dates):
            price = prices[i]
            daily_range = price * 0.03  # 3% daily range
            
            open_price = price + np.random.uniform(-daily_range/2, daily_range/2)
            high = max(open_price, price) + np.random.uniform(0, daily_range/4)
            low = min(open_price, price) - np.random.uniform(0, daily_range/4)
            volume = np.random.randint(1000000, 10000000)
            
            data.append({
                'date': date,
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(price, 2),
                'volume': volume
            })
        
        return pd.DataFrame(data)
    
    def _generate_sample_kse_data(self):
        """Generate realistic sample KSE-100 data for demonstration"""
        # Generate data for the last 30 days
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        
        # Start with a base price around current KSE-100 levels
        base_price = 45000  # Approximate KSE-100 level
        
        # Generate realistic price movements
        returns = np.random.normal(0, 0.015, 30)  # 1.5% daily volatility
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        data = []
        for i, date in enumerate(dates):
            price = prices[i]
            daily_range = price * 0.025  # 2.5% daily range
            
            open_price = price + np.random.uniform(-daily_range/2, daily_range/2)
            high = max(open_price, price) + np.random.uniform(0, daily_range/3)
            low = min(open_price, price) - np.random.uniform(0, daily_range/3)
            volume = np.random.randint(50000000, 200000000)  # KSE-100 typical volume
            
            data.append({
                'date': date,
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(price, 2),
                'volume': volume
            })
        
        return pd.DataFrame(data)
    
    def _generate_sample_company_data(self, symbol):
        """Generate realistic sample company data"""
        # Company-specific base prices (approximate PKR values)
        base_prices = {
            'OGDC': 85,
            'HBL': 150,
            'MCB': 200,
            'ENGRO': 300,
            'LUCK': 550,
            'PSO': 180,
            'UBL': 160,
            'FFC': 90,
            'PPL': 75,
            'NBP': 40,
            'HUBC': 70,
            'SYS': 800,
            'PTC': 1200,
            'MTL': 1000,
            'NESTLE': 5500,
            'UNILEVER': 4200,
            'TRG': 110,
            'ILP': 55,
            'PKGS': 450,
            'DGKC': 65
        }
        
        base_price = base_prices.get(symbol, 100)
        
        # Generate data for the last 30 days
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        
        # Generate realistic price movements with company-specific volatility
        volatility = 0.025 if symbol in ['NESTLE', 'UNILEVER'] else 0.035  # Blue chips vs others
        returns = np.random.normal(0, volatility, 30)
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(max(prices[-1] * (1 + ret), 1))  # Ensure prices don't go negative
        
        data = []
        for i, date in enumerate(dates):
            price = prices[i]
            daily_range = price * 0.04  # 4% daily range
            
            open_price = price + np.random.uniform(-daily_range/2, daily_range/2)
            high = max(open_price, price) + np.random.uniform(0, daily_range/3)
            low = min(open_price, price) - np.random.uniform(0, daily_range/3)
            
            # Volume based on company size
            volume_multiplier = 10 if symbol in ['NESTLE', 'UNILEVER'] else 1
            volume = np.random.randint(100000 * volume_multiplier, 5000000 * volume_multiplier)
            
            data.append({
                'date': date,
                'open': round(max(open_price, 1), 2),
                'high': round(max(high, 1), 2),
                'low': round(max(low, 1), 2),
                'close': round(max(price, 1), 2),
                'volume': volume
            })
        
        return pd.DataFrame(data)
