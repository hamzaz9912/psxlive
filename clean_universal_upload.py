"""
Clean Universal File Upload Function for the PSX Forecasting App
"""

import streamlit as st
import pandas as pd

def display_universal_file_upload():
    """Clean universal file upload functionality for any brand prediction"""
    st.subheader("📁 Universal File Upload & Prediction")
    
    st.markdown("""
    **🔮 Universal Financial Data Prediction System**
    
    Upload any financial instrument data and get comprehensive predictions with:
    - 📅 Next 7 Days detailed forecasts with trend indicators  
    - ⚡ Intraday 5-minute predictions with day selection
    - 📊 Technical analysis with moving averages and RSI
    - 📈 Interactive charts with confidence levels
    """)
    
    # Enhanced Brand/Instrument input with examples  
    col1, col2 = st.columns([3, 1])
    
    with col1:
        brand_name = st.text_input(
            "🏷️ Enter Brand/Instrument Name:",
            placeholder="XAUSD, BTC, OGDC, EUR/USD, FORCES, etc.",
            key="brand_name_input",
            help="Examples: XAUSD (Gold), BTC (Bitcoin), OGDC (PSX), EUR/USD (Forex), FORCES (Military stocks)"
        )
    
    with col2:
        st.markdown("**✅ Supported:**")
        st.markdown("• PSX Stocks")
        st.markdown("• Commodities") 
        st.markdown("• Crypto")
        st.markdown("• Forex")
    
    uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xlsx', 'xls'])
    
    if uploaded_file is not None and brand_name:
        try:
            # Process uploaded file using the simple file reader
            with st.spinner("Processing uploaded file..."):
                from simple_file_reader import read_any_file, analyze_dataframe
                
                # Reset file pointer to beginning
                uploaded_file.seek(0)
                
                # Read the file using simple file reader
                df, error_message = read_any_file(uploaded_file)
                
                if error_message:
                    st.error(f"**Processing Error:** {error_message}")
                    st.info("💡 **Tip:** Try uploading a CSV file with comma-separated values or Excel file (.xlsx)")
                    return
                
                # Analyze the dataframe
                analysis = analyze_dataframe(df, brand_name)
                analysis['data'] = df
                analysis['columns'] = df.columns.tolist()
                analysis['shape'] = df.shape
            
            # Show clean data analysis
            st.success("✅ File processed successfully!")
            
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
            
            # Show data preview
            st.subheader("📋 Data Preview")
            try:
                if isinstance(df, pd.DataFrame) and not df.empty:
                    st.dataframe(df.head(10), use_container_width=True)
                else:
                    st.warning("No data available for preview")
            except Exception as e:
                st.error(f"Error displaying data: {str(e)}")
                
            # Store for prediction
            st.session_state.universal_df = df
            st.session_state.universal_brand = brand_name
            st.session_state.universal_analysis = analysis
            
            # Generate predictions
            st.subheader(f"🔮 Predictions for {brand_name}")
            
            # Prediction buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📅 Generate 7-Day Forecast", key="seven_day_forecast"):
                    display_universal_predictions(df, brand_name, "7_day")
            
            with col2:
                if st.button("⚡ Generate Intraday Forecast", key="intraday_forecast"):
                    display_universal_predictions(df, brand_name, "intraday")
            
            with col3:
                if st.button("📊 Technical Analysis", key="technical_analysis"):
                    display_universal_predictions(df, brand_name, "technical")
            
            # Check if predictions are stored and display them
            if hasattr(st.session_state, 'universal_predictions') and st.session_state.universal_predictions:
                predictions = st.session_state.universal_predictions
                
                st.markdown("---")
                st.subheader("📈 Prediction Results")
                
                # Display prediction charts and metrics
                if 'forecast_chart' in predictions:
                    st.plotly_chart(predictions['forecast_chart'], use_container_width=True)
                
                if 'metrics' in predictions:
                    metrics = predictions['metrics']
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        if 'trend' in metrics:
                            st.metric("Trend", metrics['trend'])
                    
                    with col2:
                        if 'next_price' in metrics:
                            st.metric("Next Price", f"{metrics['next_price']:.4f}")
                    
                    with col3:
                        if 'change_percent' in metrics:
                            st.metric("Change %", f"{metrics['change_percent']:+.2f}%")
                    
                    with col4:
                        if 'confidence' in metrics:
                            st.metric("Confidence", f"{metrics['confidence']:.1%}")
                
                # Display additional insights
                if 'insights' in predictions:
                    st.markdown("### 💡 Key Insights")
                    for insight in predictions['insights']:
                        st.markdown(f"• {insight}")
        
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.info("Please try uploading a different file or check the file format")


def display_universal_predictions(df, brand_name, prediction_type):
    """Display universal predictions for any financial instrument"""
    try:
        from universal_predictor_new import UniversalPredictor
        
        predictor = UniversalPredictor()
        
        with st.spinner(f"Generating {prediction_type} predictions..."):
            if prediction_type == "7_day":
                predictions = predictor.generate_7_day_forecast(df, brand_name)
            elif prediction_type == "intraday": 
                predictions = predictor.generate_intraday_forecast(df, brand_name)
            elif prediction_type == "technical":
                predictions = predictor.generate_technical_analysis(df, brand_name)
            else:
                st.error("Unknown prediction type")
                return
        
        # Store predictions in session state
        st.session_state.universal_predictions = predictions
        
        # Trigger rerun to display results
        st.rerun()
        
    except Exception as e:
        st.error(f"Error generating predictions: {str(e)}")
        st.info("Please check your data format and try again")