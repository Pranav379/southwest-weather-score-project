import streamlit as st
import datetime
import random
import time

# ==========================================
# 1. APP CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Flight Delay Predictor",
    page_icon="✈️",
    layout="centered"
)

# Try importing plotting libraries (Safe Mode handling)
try:
    import plotly.graph_objects as go
    import pandas as pd
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False

# ==========================================
# 2. SOUTHWEST STYLING (CSS)S
# ==========================================
# Colors: Blue #304CB2, Yellow #FFB612, Red #C60C30
SOUTHWEST_CSS = """
<style>
    /* Main Background - Light Gray */
    [data-testid="stAppViewContainer"] {
        background-color: #f8f9fa !important;
        color: #333333 !important;
    }
    
    /* Header Transparency */
    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0) !important;
    }

    /* Headings - Southwest Blue */
    h1, h2, h3 {
        color: #304CB2 !important;
        font-family: 'Arial', sans-serif;
        font-weight: 800;
    }

    /* Southwest Buttons */
    .stButton > button {
        background-color: #FFB612 !important;
        color: #304CB2 !important;
        border-radius: 25px;
        border: none;
        font-weight: bold;
        font-size: 18px;
        padding: 0.5rem 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        width: 100%;
        transition: transform 0.1s;
    }
    .stButton > button:hover {
        background-color: #e0a10f !important;
        transform: scale(1.02);
        color: #304CB2 !important;
    }

    /* Flight Cards */
    .flight-card {
        background-color: white;
        border-left: 8px solid #304CB2;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        color: #333;
        transition: transform 0.2s;
    }
    .flight-card:hover {
        transform: translateX(5px);
        border-left: 8px solid #FFB612;
    }

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
        color: #FFB612;
        line-height: 1;
    }
    .score-label {
        font-size: 1.2rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        opacity: 0.9;
    }
</style>
"""
st.markdown(SOUTHWEST_CSS, unsafe_allow_html=True)

# ==========================================
# 3. MOCK LOGIC & "MODEL"
# ==========================================

def generate_mock_schedule(flight_num):
    """Simulates looking up a schedule based on input."""
    today = datetime.date.today()
    # Realistic mock routes
    routes = [
        ("DAL", "HOU", 239), ("MDW", "LGA", 733), ("PHX", "LAX", 370),
        ("DEN", "SFO", 967), ("BWI", "MCO", 787), ("ATL", "DAL", 721)
    ]
    
    schedule = []
    for i in range(1, 4): # Generate 3 flights
        r_origin, r_dest, r_dist = random.choice(routes)
        date_offset = today + datetime.timedelta(days=i)
        
        # Random time (HHMM)
        dep_h = random.randint(6, 21)
        dep_m = random.choice([0, 15, 30, 45])
        dep_time = dep_h * 100 + dep_m
        
        schedule.append({
            "id": i,
            "flight_num": flight_num.upper(),
            "date": date_offset,
            "origin": r_origin,
            "dest": r_dest,
            "distance": r_dist,
            "dep_time": dep_time,
            "airline": "WN" if "WN" in flight_num.upper() else "AA"
        })
    return schedule

def get_mock_weather_data():
    """Generates weather features for the model inputs."""
    # We randomize this to show different outcomes
    return {
        'tavg': random.uniform(-5, 35),  # Temp Celsius
        'tmin': random.uniform(-10, 25),
        'tmax': random.uniform(0, 40),
        'prcp': random.choices([0, 5.0, 25.0], weights=[0.7, 0.2, 0.1])[0], # Rain mm
        'snow': random.choices([0, 10.0], weights=[0.9, 0.1])[0], # Snow mm
        'wspd': random.uniform(5, 45),   # Wind km/h
        'pres': random.uniform(995, 1030) # Pressure hPa
    }

def heuristic_model_predict(weather, flight_data):
    """
    Simulates the ML Model. 
    Returns a score 0-100 (100 = Perfect, 0 = Cancelled).
    """
    score = 100.0
    
    # --- PENALTIES ---
    # 1. Wind
    if weather['wspd'] > 40: score -= 25
    elif weather['wspd'] > 25: score -= 10
        
    # 2. Precipitation
    if weather['prcp'] > 15: score -= 30
    elif weather['prcp'] > 0: score -= 10
        
    # 3. Snow (Major killer)
    if weather['snow'] > 0: score -= 40
        
    # 4. Pressure (Storm system)
    if weather['pres'] < 1000: score -= 15
        
    # 5. Late flights
    if flight_data['dep_time'] > 1900: score -= 5
        
    # Add random noise for "model uncertainty"
    score += random.uniform(-3, 3)
    
    return max(0.0, min(100.0, score))

# ==========================================
# 4. UI FLOW
# ==========================================

# Session State Initialization
if 'page' not in st.session_state:
    st.session_state.page = 'landing'
if 'selected_flight' not in st.session_state:
    st.session_state.selected_flight = None

# --- PAGE 1: LANDING ---
if st.session_state.page == 'landing':
    st.markdown("<div style='text-align: center; padding: 20px;'>", unsafe_allow_html=True)
    st.title("Flight Delay Predictor")
    st.markdown("### 🕒 Will you make it on time?")
    st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        col1, col2 = st.columns([3, 1])
        with col1:
            f_num = st.text_input("Flight Number", placeholder="e.g. WN1492", value="WN1492")
        with col2:
            st.write("") # Spacer
            st.write("") 
        
        if st.button("Look Up Upcoming Flights"):
            with st.spinner("Searching airline schedules..."):
                time.sleep(0.8) # Fake API delay
                st.session_state.schedule = generate_mock_schedule(f_num)
                st.session_state.page = 'selection'
                st.rerun()

# --- PAGE 2: FLIGHT SELECTION ---
elif st.session_state.page == 'selection':
    if st.button("← Back to Search"):
        st.session_state.page = 'landing'
        st.rerun()
        
    st.subheader("Select Your Flight")
    st.markdown("Found the following upcoming matches:")
    
    for flight in st.session_state.schedule:
        # Format time nicely
        d_time = f"{flight['dep_time']:04d}"
        d_time_fmt = f"{d_time[:2]}:{d_time[2:]}"
        
        # Card UI
        st.markdown(f"""
        <div class="flight-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h3 style="margin:0; color:#304CB2;">{flight['flight_num']}</h3>
                    <div style="font-size:1.1em;">{flight['origin']} ➝ {flight['dest']}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-weight:bold;">{flight['date']}</div>
                    <div style="color:#666;">Departs: {d_time_fmt}</div>
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
    
    # Top Nav
    c1, c2 = st.columns([1, 4])
    if c1.button("← Start Over"):
        st.session_state.page = 'landing'
        st.session_state.selected_flight = None
        st.rerun()
        
    st.markdown(f"## Forecast: {flight['flight_num']}")
    
    # Run "Model"
    weather = get_mock_weather_data()
    score = heuristic_model_predict(weather, flight)
    
    # 1. SCORE CARD
    st.markdown(f"""
    <div class="score-box">
        <div class="score-label">On-Time Probability Score</div>
        <div class="big-score">{score:.1f}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. GAUGE & INTERPRETATION
    col_gauge, col_text = st.columns([1, 1])
    
    with col_gauge:
        if HAS_PLOTTING:
            # Determine color
            if score >= 90: g_color = "#4CAF50"
            elif score >= 70: g_color = "#FFB612"
            else: g_color = "#C60C30"
            
            fig = go.Figure(go.Indicator(
                mode = "gauge",
                value = score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                gauge = {
                    'axis': {'range': [0, 100], 'tickwidth': 1},
                    'bar': {'color': g_color},
                    'bgcolor': "white",
                    'steps': [
                        {'range': [0, 70], 'color': '#fce4e4'},
                        {'range': [70, 90], 'color': '#fff8e1'},
                        {'range': [90, 100], 'color': '#e8f5e9'}]
                }
            ))
            fig.update_layout(height=180, margin=dict(l=20, r=20, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.progress(int(score))
            
    with col_text:
        if score >= 90:
            st.success("✅ **Good Conditions**")
            st.write("Skies look clear. On-time departure is highly likely.")
        elif score >= 70:
            st.warning("⚠️ **Moderate Risk**")
            st.write("Weather conditions indicate a moderate delay risk. Keep an eye on winds.")
        else:
            st.error("🚨 **High Risk**")
            st.write("Significant weather impact detected. Expect cancellations or long delays.")

    # 3. CONTRIBUTING FACTORS
    st.markdown("### Contributing Factors")
    
    f_col1, f_col2 = st.columns(2)
    
    with f_col1:
        with st.expander("📉 Risk Factors", expanded=True):
            risks = []
            if weather['wspd'] > 25: risks.append(f"High Winds ({weather['wspd']:.1f} km/h)")
            if weather['prcp'] > 0: risks.append(f"Precipitation ({weather['prcp']} mm)")
            if weather['pres'] < 1005: risks.append("Low Pressure System")
            if weather['snow'] > 0: risks.append("Snow / Ice")
            if flight['dep_time'] > 1800: risks.append("Late Evening Flight")
            
            if risks:
                for r in risks: st.write(f"• {r}")
            else:
                st.write("No significant risks detected.")

    with f_col2:
        with st.expander("📈 Good Conditions", expanded=True):
            goods = []
            if weather['tavg'] > 15: goods.append(f"Mild Temperature ({weather['tavg']:.1f}°C)")
            if weather['wspd'] < 15: goods.append("Calm Winds")
            if weather['pres'] >= 1015: goods.append("High Pressure Area")
            if weather['prcp'] == 0: goods.append("No Precipitation")
            
            if goods:
                for g in goods: st.write(f"• {g}")
            else:
                st.write("Standard conditions.")

    # 4. DEBUG / RAW DATA
    st.markdown("---")
    if st.checkbox("View Feature Values (Debug)"):
        if HAS_PLOTTING:
            # Create a nice dataframe view
            features = {
                'Feature': ['Temperature', 'Precipitation', 'Snow', 'Wind Speed', 'Pressure', 'Distance'],
                'Value': [
                    f"{weather['tavg']:.1f}°C", 
                    f"{weather['prcp']:.1f} mm",
                    f"{weather['snow']:.1f} mm",
                    f"{weather['wspd']:.1f} km/h",
                    f"{weather['pres']:.1f} hPa",
                    f"{flight['distance']} miles"
                ]
            }
            st.table(pd.DataFrame(features))
        else:
            st.json(weather)

    st.caption("Disclaimer: Model accuracy dependent on historical data. Weather conditions may change.")