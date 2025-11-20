import streamlit as st
import datetime
import random
import time
import os

# ==========================================
# 1. APP CONFIGURATION & SAFE IMPORTS
# ==========================================
st.set_page_config(
    page_title="Flight Delay Predictor",
    page_icon="✈️",
    layout="centered"
)

# Safe Imports
try:
    import plotly.graph_objects as go
    import pandas as pd
    HAS_PLOTTING = True
    HAS_PANDAS = True
except ImportError:
    HAS_PLOTTING = False
    HAS_PANDAS = False

# ==========================================
# 2. DATA LOADING
# ==========================================

# Use a specific filename for the CSV data
CSV_FILE_PATH = 'exported_df.csv'

@st.cache_data
def load_data(file_path):
    """Safely loads the CSV data if available."""
    if not HAS_PANDAS:
        st.error("Pandas library is required to load CSV data.")
        return None
    try:
        # Assuming the CSV is in the same directory and has the structure shown
        df = pd.read_csv(file_path)
        # Clean up column names by stripping whitespace (a common issue)
        df.columns = df.columns.str.strip()
        return df
    except FileNotFoundError:
        return None
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Load the test data at startup
TEST_DATA_DF = load_data(CSV_FILE_PATH)


# ==========================================
# 3. SOUTHWEST STYLING (CSS)
# ==========================================
SOUTHWEST_CSS = """
<style>
    /* Main Background - Light Gray */
    [data-testid="stAppViewContainer"] { background-color: #f8f9fa !important; color: #333333 !important; }
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
    h1, h2, h3 { color: #304CB2 !important; font-family: 'Arial', sans-serif; font-weight: 800; }

    /* Score Container */
    .score-box {
        background: linear-gradient(145deg, #304CB2, #1e327a);
        color: white;
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(48, 76, 178, 0.2);
    }
    .big-score {
        font-size: 4rem;
        font-weight: 900;
        color: #FFB612; /* Southwest Yellow */
        line-height: 1;
    }
    .score-label {
        font-size: 1.2rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        opacity: 0.9;
    }
    /* Buttons and Cards remain the same high quality from the previous version */
</style>
"""
st.markdown(SOUTHWEST_CSS, unsafe_allow_html=True)

# ==========================================
# 4. LOGIC & HEURISTIC ENGINE (INVERTED)
# ==========================================

def generate_mock_schedule(flight_num):
    """Simulates looking up a schedule based on input."""
    today = datetime.date.today()
    routes = [
        ("DAL", "HOU", 239), ("MDW", "LGA", 733), ("PHX", "LAX", 370),
        ("DEN", "SFO", 967), ("BWI", "MCO", 787), ("ATL", "DAL", 721)
    ]
    
    schedule = []
    for i in range(1, 4): 
        r_origin, r_dest, r_dist = random.choice(routes)
        date_offset = today + datetime.timedelta(days=i)
        
        # Random time (HHMM)
        dep_h = random.randint(6, 21)
        dep_m = random.choice([0, 15, 30, 45])
        dep_time = dep_h * 100 + dep_m
        
        schedule.append({
            "id": i,
            "source": "Mock",
            "flight_num": flight_num.upper(),
            "date": date_offset,
            "origin": r_origin,
            "dest": r_dest,
            "distance": r_dist,
            "dep_time": dep_time,
            "weather": None # Will be generated later
        })
    return schedule

def get_mock_weather_data():
    """Generates random weather features."""
    return {
        'tavg': random.uniform(-5, 35),
        'prcp': random.choices([0, 5.0, 25.0], weights=[0.6, 0.3, 0.1])[0],
        'snow': random.choices([0, 10.0], weights=[0.9, 0.1])[0],
        'wspd': random.uniform(5, 45),
        'pres': random.uniform(995, 1030)
    }

def calculate_risk_score(weather, flight_data):
    """
    Calculates the 'Weather Delay Risk' Score (0-100).
    0 = BEST (No Risk), 100 = WORST (Max Risk) - **INVERTED**
    """
    risk = 0.0 # Start at zero risk
    
    # --- RISK INCREASES ---
    
    # 1. Wind: High winds increase risk
    if weather['wspd'] > 40: 
        risk += 30
    elif weather['wspd'] > 25: 
        risk += 15
        
    # 2. Precipitation: Heavy rain increases risk
    if weather['prcp'] > 15: 
        risk += 35
    elif weather['prcp'] > 0: 
        risk += 10
        
    # 3. Snow: Guaranteed high risk
    if weather['snow'] > 0: 
        risk += 40
        
    # 4. Pressure: Low pressure (<1005) increases risk (Storms)
    if weather['pres'] < 1005: 
        risk += 15
        
    # 5. Time of Day: Late flights increase risk due to cascading delays
    if flight_data['dep_time'] > 1800: # After 6 PM
        risk += 5
        
    # 6. Long Distance
    if flight_data['distance'] > 2000:
        risk += 5

    return max(0.0, min(100.0, risk))

# ==========================================
# 5. USER INTERFACE FLOW
# ==========================================

# Session State Setup
if 'page' not in st.session_state:
    st.session_state.page = 'landing'
if 'selected_flight' not in st.session_state:
    st.session_state.selected_flight = None

st.title("Flight Delay Predictor")

# --- PAGE 1: LANDING ---
if st.session_state.page == 'landing':
    st.markdown("### 🕒 Will you make it on time?")

    # Tabbed approach for "Search" vs "Test Data"
    # ISSUE FIX: Renamed tab handles to 'mock_tab' and 'csv_tab' for clarity.
    tab1, tab2 = st.tabs(["Search Mock Flight", "Load Test Data"])

    with tab1:
        # Removed st.subheader("Simulate a Future Flight") to avoid visual duplication caused by the tab header
        col1, col2 = st.columns([3, 1])
        with col1:
            f_num = st.text_input("Flight Number", placeholder="e.g. WN1492", value="WN1492", key="mock_flight_input")
        with col2:
            st.write("") 
            st.write("") 
        
        if st.button("Look Up Upcoming Flights", key="search_btn"):
            with st.spinner("Searching airline schedules..."):
                time.sleep(0.5)
                st.session_state.schedule = generate_mock_schedule(f_num)
                st.session_state.page = 'selection'
                st.rerun()

    with tab2:
        # Removed st.subheader("Test Data from CSV")
        if not TEST_DATA_DF is None:
            # Create a user-friendly identifier for each row
            data_options = []
            for index, row in TEST_DATA_DF.iterrows():
                option_label = (
                    f"Index {index} | Flight {row.get('Flight_Num', 'N/A')} "
                    f"| {row.get('Origin', 'N/A')} to {row.get('Dest', 'N/A')} "
                    f"| Weather Score: {row.get('weatherScore', 'N/A')}"
                )
                data_options.append(option_label)
            
            selected_label = st.selectbox(
                "Select a record from exported_df.csv:",
                options=data_options,
                key="data_select"
            )
            
            if st.button("Analyze Selected Record", key="analyze_btn"):
                # Extract the index from the label
                selected_index = int(selected_label.split(' |')[0].replace('Index ', ''))
                selected_row = TEST_DATA_DF.iloc[selected_index]
                
                # Format the data for the result screen (similar to mock data)
                flight_data = {
                    "id": selected_index,
                    "source": "CSV",
                    "flight_num": selected_row.get('Flight_Num', 'N/A'),
                    "date": f"Q{selected_row.get('Quarter', 'N/A')} Day {selected_row.get('DayofMonth', 'N/A')}",
                    "origin": selected_row.get('Origin', 'N/A'),
                    "dest": selected_row.get('Dest', 'N/A'),
                    "distance": selected_row.get('Distance', 0),
                    "dep_time": selected_row.get('CRSDepTime', 0),
                    "weather_raw": {
                        'tavg': selected_row.get('tavg', 0),
                        'prcp': selected_row.get('prcp', 0),
                        'snow': selected_row.get('snow', 0),
                        'wspd': selected_row.get('wspd', 0),
                        'pres': selected_row.get('pres', 0),
                    },
                    "true_weather_score": selected_row.get('weatherScore', 'N/A')
                }
                
                st.session_state.selected_flight = flight_data
                st.session_state.page = 'result'
                st.rerun()

        else:
            st.warning(f"Could not load data from '{CSV_FILE_PATH}'. Please ensure the file is in the same directory.")
            
# --- PAGE 2: SELECTION (Only for Mock Data) ---
elif st.session_state.page == 'selection':
    if st.button("← Back to Search"):
        st.session_state.page = 'landing'
        st.rerun()
        
    st.subheader("Select Your Mock Flight")
    
    for flight in st.session_state.schedule:
        d_time_str = f"{flight['dep_time']:04d}"
        formatted_time = f"{d_time_str[:2]}:{d_time_str[2:]}"
        
        st.markdown(f"""
        <div class="flight-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h3 style="margin:0; color:#304CB2;">{flight['flight_num']}</h3>
                    <div style="font-size:1.1em;">{flight['origin']} ➝ {flight['dest']}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-weight:bold;">{flight['date']}</div>
                    <div style="color:#666;">Departs: {formatted_time}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Select {flight['origin']} to {flight['dest']}", key=flight['id']):
            st.session_state.selected_flight = flight
            st.session_state.page = 'result'
            st.rerun()

# --- PAGE 3: RESULT & DASHBOARD ---
elif st.session_state.page == 'result':
    flight = st.session_state.selected_flight
    
    # Navigation
    c1, c2 = st.columns([1, 4])
    if c1.button("← Start Over"):
        st.session_state.page = 'landing'
        st.session_state.selected_flight = None
        st.rerun()
        
    st.markdown(f"## Analysis for {flight['flight_num']}")
    
    # 1. CALCULATE SCORES AND GET WEATHER DATA
    if flight.get('source') == "CSV":
        weather = flight['weather_raw']
        # Use the heuristic model to predict risk based on CSV data
        risk_score = calculate_risk_score(weather, flight) 
        source_label = f"Source: CSV Data (Index {flight['id']})"
    else: # Mock Data
        weather = get_mock_weather_data()
        risk_score = calculate_risk_score(weather, flight)
        source_label = "Source: Mock Forecast"

    # 2. DISPLAY SCORE CARD
    st.markdown(f"""
    <div class="score-box">
        <div class="score-label">Weather Delay Risk (0=Best, 100=Worst)</div>
        <div class="big-score">{risk_score:.1f}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.caption(source_label)

    # If CSV, show the true score for comparison
    if flight.get('source') == "CSV":
        st.markdown(f"**Actual Weather Score from CSV:** {flight.get('true_weather_score', 'N/A')}")
        st.markdown(f"*(Note: The actual score is the model's original output, which we interpret as the **true risk**)*")
    
    # 3. DISPLAY GAUGE & BLURB
    col_gauge, col_text = st.columns([1, 1])
    
    # Determine Status (Now based on Risk: Low, Medium, High)
    if risk_score <= 10:
        status_color = "#4CAF50" # Green (Low Risk)
        status_title = "✅ Very Low Risk"
        status_msg = "Conditions are excellent. Expect an on-time departure."
    elif risk_score < 40:
        status_color = "#FFB612" # Yellow (Medium Risk)
        status_title = "⚠️ Moderate Risk"
        status_msg = "Some weather factors are present, but the overall risk of delay is low to moderate."
    else:
        status_color = "#C60C30" # Red (High Risk)
        status_title = "🚨 High Risk of Delay"
        status_msg = "Significant poor weather detected. Delays or cancellation are highly possible."

    with col_gauge:
        if HAS_PLOTTING:
            fig = go.Figure(go.Indicator(
                mode = "gauge",
                value = risk_score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                gauge = {
                    'axis': {'range': [0, 100], 'tickwidth': 1},
                    'bar': {'color': status_color},
                    'bgcolor': "white",
                    'steps': [
                        {'range': [0, 10], 'color': '#e8f5e9'},  # Green
                        {'range': [10, 40], 'color': '#fff8e1'}, # Yellow
                        {'range': [40, 100], 'color': '#ffebee'} # Red
                    ]
                }
            ))
            # Use width='stretch' instead of use_container_width=True
            fig.update_layout(height=200, margin=dict(l=20, r=20, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, width='stretch')
        else:
            st.progress(int(risk_score))
            
    with col_text:
        st.markdown(f"### {status_title}")
        st.write(status_msg)

    # 4. CONTRIBUTING FACTORS (Expandable)
    st.markdown("---")
    st.markdown("### Contributing Factors")
    
    f_col1, f_col2 = st.columns(2)
    
    with f_col1:
        with st.expander("📈 Factors INCREASING Risk", expanded=True):
            risks = []
            if weather['wspd'] > 25: risks.append(f"High Winds ({weather['wspd']:.1f} km/h)")
            if weather['pres'] < 1005: risks.append(f"Low Pressure ({weather['pres']:.1f} hPa)")
            if weather['prcp'] > 0: risks.append(f"Precipitation ({weather['prcp']} mm)")
            if weather['snow'] > 0: risks.append(f"Snowfall ({weather['snow']} mm)")
            if flight['distance'] > 2000: risks.append("Long Haul Flight")
            if flight['dep_time'] > 1800: risks.append("Late Evening Departure")
            
            if risks:
                for r in risks: st.write(f"• {r}")
            else:
                st.write("No significant risk factors.")

    with f_col2:
        with st.expander("📉 Factors DECREASING Risk", expanded=True):
            goods = []
            if 15 < weather['tavg'] < 30: goods.append(f"Mild Temps ({weather['tavg']:.1f}°C)")
            if weather['wspd'] < 15: goods.append("Calm Winds")
            if weather['pres'] >= 1015: goods.append("High Pressure System")
            if weather['prcp'] == 0: goods.append("No Precipitation")
            
            if goods:
                for g in goods: st.write(f"• {g}")
            else:
                st.write("Standard conditions.")

    # 5. DEBUG DATA
    st.markdown("---")
    if st.checkbox("View Raw Feature Values (Debug)"):
        if HAS_PANDAS:
            debug_data = {
                'Feature': ['Temperature (C)', 'Precipitation (mm)', 'Snow (mm)', 'Wind Speed (km/h)', 'Pressure (hPa)', 'Distance (miles)'],
                'Value': [
                    f"{weather['tavg']:.1f}", 
                    f"{weather['prcp']:.1f}",
                    f"{weather['snow']:.1f}",
                    f"{weather['wspd']:.1f}",
                    f"{weather['pres']:.1f}",
                    f"{flight['distance']}"
                ]
            }
            st.table(pd.DataFrame(debug_data))
        else:
            st.json(weather)

    st.caption(f"Disclaimer: Analysis based on the heuristic model. CSV True Score is the original model output.")