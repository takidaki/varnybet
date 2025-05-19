import streamlit as st
import pandas as pd
import io
from pymongo import MongoClient
import hashlib

# --- Configuration and Styling ---
st.set_page_config(layout="wide", page_title="VarnyBet")

# Custom CSS to mimic Stake.com/bet365 style with smaller elements
GLOBAL_STYLE = """
    <style>
        /* --- General Body and Font --- */
        body {
            font-family: 'Roboto', sans-serif;
            color: #E2E8F0;
        }
        .stApp {
            background-color: #121820;
        }

        /* --- Main Title --- */
        h1 {
            color: #FFFFFF;
            text-align: center;
            padding-bottom: 20px;
            border-bottom: 1px solid #4A5568;
            background: linear-gradient(to right, #4CAF50, #FFEB3B, #FFFFFF);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* --- League/Category Headers --- */
        .league-header {
            font-size: 1.7em;
            color: #FFFFFF;
            margin-top: 25px;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #3A4250;
            text-align: left;
            background: linear-gradient(to right, #4CAF50, #FFEB3B, #FFFFFF);
        }

        /* --- Player Bet Card --- */
        .bet-card {
            background-color: #1A2430;
            border-radius: 6px; /* Slightly smaller radius */
            padding: 15px; /* Reduced padding */
            margin-bottom: 15px; /* Adjusted margin */
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.25); /* Adjusted shadow */
            border: 1px solid #2D3748;
        }

        /* --- Player Name --- */
        .player-name {
            font-size: 1.0em; /* Further reduced font size */
            font-weight: 600;
            color: #FFFFFF;
            margin-bottom: 6px; /* Further reduced margin */
        }
        
        /* --- Match/Event Info (Date/Time) --- */
        .match-info {
            font-size: 0.7em; /* Further reduced font size */
            color: #718096;
            margin-bottom: 10px; /* Further reduced margin */
        }

        /* --- Odds Container and Buttons --- */
        .odds-container {
            display: flex;
            justify-content: space-around;
            align-items: center;
            margin-top: 6px; /* Further reduced margin */
        }
        .odds-button {
            background-color: #2D3748;
            color: #E2E8F0;
            padding: 6px 10px;
            border-radius: 4px;
            text-align: center;
            cursor: pointer;
            transition: background-color 0.3s ease, transform 0.2s ease;
            font-weight: 500;
            font-size: 0.85em;
            min-width: 75px;
            border: 1px solid #4A5568;
        }
        .odds-button:hover {
            background-color: #4A5568;
            transform: translateY(-1px);
        }
        .odds-label {
            font-size: 0.65em;
            color: #A0AEC0;
            display: block;
            margin-bottom: 3px;
        }
        .bet-slip {
            background-color: #2D3748; /* Changed background color */
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.25);
            border: 1px solid #2D3748;
        }
        .bet-slip-item {
            font-size: 0.9em;
            color: #6b8a73;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .bet-slip-remove {
            background-color: #E53E3E;
            color: white;
            border: none;
            padding: 3px 8px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 0.7em;
        }
        .odds-value {
            font-size: 1.1em;
            font-weight: 700;
            color: #F6E05E;
        }
        /* Style for the Streamlit button to look like odds-button */
        div.stButton > button:first-child {
            background-color: #2D3748;
            color: #E2E8F0;
            padding: 6px 10px;
            border-radius: 4px;
            text-align: center;
            cursor: pointer;
            transition: background-color 0.3s ease, transform 0.2s ease;
            font-weight: 500;
            font-size: 0.85em;
            min-width: 75px;
            border: 1px solid #4A5568;
        }
        div.stButton > button:first-child:hover {
            background-color: #4A5568;
            transform: translateY(-1px);
        }
        .team-icon {
            font-size: 1.2em;
            margin-right: 5px;
        }

        /* Mobile-specific styles */
        @media screen and (max-width: 768px) {
            .bet-slip {
                padding: 10px;
                margin-bottom: 10px;
            }
            .bet-slip-item {
                font-size: 0.8em;
                margin-bottom: 5px;
            }
        }
    </style>
"""
st.markdown(GLOBAL_STYLE, unsafe_allow_html=True)

# --- CSV Data (Fallback) ---
CSV_CONTENT = """Datum;Vreme;Sifra;Domacin;Gost;1;X;2;GR;U;O;Yes;No
MATCH_NAME:Xtip Strelci;;;;;;;;;;;;
LEAGUE_NAME: Kvoteri;;;;;;;;;;;;
19.5.2025;20:00;;Varnicic D.;;;;;2,5;1,9;1,8;;
170 | 19.5.2025;20:00;;Jajcevic D.;;;;;1,5;2;1,7;;
171 | 19.5.2025;20:00;;Mikic D.;;;;;0,5;1,7;2,0;;
172 | 19.5.2025;20:00;;Petkovic J.;;;;;1,5;1,7;2;;
173 | 175 | 19.5.2025;20:00;;Trifunovic A.;;;;;1,5;1,85;1,85;;
174 | 176 | 19.5.2025;20:00;;Marjanovic M.;;;;;1,5;1,8;1,9;;
175 | 177 | 19.5.2025;20:00;;;;;;;;;;;
LEAGUE_NAME: Gaucosi;;;;;;;;;;;;
177 | 179 | 19.5.2025;20:00;;Jakovljevic M.;;;;;1,5;1,85;1,85;;
178 | 180 | 19.5.2025;20:00;;Jovanovic N.;;;;;0,5;2,2;1,6;;
179 | 181 | 19.5.2025;20:00;;Bocarac N.;;;;;2,5;1,75;1,95;;
180 | 182 | 19.5.2025;20:00;;Lozo N.;;;;;0,5;1,85;1,85;;
181 | 183 | 19.5.2025;20:00;;Cmiljanic A.;;;;;0,5;1,85;1,85;;
182 | 184 | 19.5.2025;20:00;;Jukovic H.;;;;;1,5;1,75;1,95;;
183 | 185 | 19.5.2025;20:00;;Prodanov B.;;;;;0,5;1,8;1,9;;
184 | 186 | """

# --- Helper Functions ---
def parse_csv_data(input_source):
    """
    Parses the CSV data from a file-like object or a string.
    Identifies leagues and player odds.
    Returns a dictionary where keys are league names and values are lists of player bets.
    """
    try:
        # If input_source is a string (fallback content), wrap it in StringIO
        # Otherwise, assume it's a file-like object (uploaded file)
        if isinstance(input_source, str):
            data_stream = io.StringIO(input_source)
        else:
            # For Streamlit UploadedFile, it's already a file-like object.
            # If it has been read, its pointer might be at the end.
            # For safety, especially if the object could be reused, reset pointer.
            # However, Streamlit usually provides a fresh object or one that can be reread.
            if hasattr(input_source, 'seek'):
                input_source.seek(0)
            data_stream = input_source

        # Read the CSV, using generic column names as header is not standard
        df = pd.read_csv(data_stream, sep=';', header=None, skip_blank_lines=True)
        df = df.astype(str) # Treat all data as string initially
    except pd.errors.EmptyDataError:
        st.error("The CSV data is empty or could not be parsed.")
        return {}
    except Exception as e:
        st.error(f"An error occurred while reading the CSV: {e}")
        return {}

    leagues_data = {}
    current_league = "Unknown League" 

    # Column indices based on CSV structure
    COL_DATE = 0
    COL_TIME = 1
    COL_PLAYER_NAME = 3 
    COL_GR = 8          
    COL_UNDER_ODD = 9   
    COL_OVER_ODD = 10   

    for index, row in df.iterrows():
        try:
            # Check for LEAGUE_NAME
            if row.iloc[0] and isinstance(row.iloc[0], str) and row.iloc[0].strip().startswith("LEAGUE_NAME:"):
                current_league = row.iloc[0].replace("LEAGUE_NAME:", "").strip()
                if current_league not in leagues_data:
                    leagues_data[current_league] = []
                continue

            # Check for MATCH_NAME
            if row.iloc[0] and isinstance(row.iloc[0], str) and row.iloc[0].strip().startswith("MATCH_NAME:"):
                continue

            # Identify and process player data rows
            player_name = str(row.iloc[COL_PLAYER_NAME]).strip()
            # Replace comma with period for decimal conversion
            gr_val_str = str(row.iloc[COL_GR]).strip().replace(',', '.')
            under_odd_str = str(row.iloc[COL_UNDER_ODD]).strip().replace(',', '.')
            over_odd_str = str(row.iloc[COL_OVER_ODD]).strip().replace(',', '.')
            
            # Validate essential fields
            if player_name and player_name.lower() != 'nan' and \
               gr_val_str and gr_val_str.lower() != 'nan' and \
               under_odd_str and under_odd_str.lower() != 'nan' and \
               over_odd_str and over_odd_str.lower() != 'nan':

                try:
                    gr_val = float(gr_val_str)
                    under_odd = float(under_odd_str)
                    over_odd = float(over_odd_str)

                    if current_league not in leagues_data: # Initialize if somehow missed
                         leagues_data[current_league] = []
                    
                    leagues_data[current_league].append({
                        "date": str(row.iloc[COL_DATE]).strip(),
                        "time": str(row.iloc[COL_TIME]).strip(),
                        "player": player_name,
                        "gr": gr_val,
                        "under_odd": under_odd,
                        "over_odd": over_odd,
                        "team": current_league # Add team information
                    })
                except ValueError:
                    # Skip rows with non-convertible number formats silently
                    pass
        except IndexError:
            # Skip rows with fewer columns than expected
            pass
        except Exception:
            # Skip other unexpected errors for a specific row
            pass

    return leagues_data

def create_user(username, password):
    """Hashes the password and stores the username, hashed password, and initial balance in MongoDB."""
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    user_data = {"username": username, "password": hashed_password, "balance": 500}
    try:
        collection = db["users"]
        collection.insert_one(user_data)
        return True
    except Exception as e:
        st.error(f"Error creating user: {e}")
        return False

def register_user():
    """Displays a registration form and creates a new user."""
    username = st.text_input("Username", key="register_username")
    password = st.text_input("Password", type="password", key="register_password")
    password_confirm = st.text_input("Confirm Password", type="password", key="register_password_confirm")
    if st.button("Register"):
        if password != password_confirm:
            st.error("Passwords do not match.")
        elif create_user(username, password):
            st.success("User registered successfully!")
        else:
            st.error("Registration failed.")

def login_user():
    """Displays a login form and authenticates the user."""
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login"):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        try:
            collection = db["users"]
            user = collection.find_one({"username": username, "password": hashed_password})
            if user:
                st.success("Logged in successfully!")
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Login failed.")
        except Exception as e:
            st.error(f"Error logging in: {e}")

def get_user_balance(username):
    """Retrieves the user's balance from MongoDB."""
    try:
        collection = db["users"]
        user = collection.find_one({"username": username})
        if user:
            return user["balance"]
        else:
            return 0
    except Exception as e:
        st.error(f"Error getting user balance: {e}")
        return 0

# MongoDB setup
MONGODB_URI = "mongodb+srv://damirmikic20:takidaki19841989@varnybet.akthnb4.mongodb.net/?retryWrites=true&w=majority&appName=VarnyBet"  # Replace with your MongoDB connection string
client = MongoClient(MONGODB_URI)
db = client.varnybet  # Use the provided database name

def clear_bet_slip():
    st.session_state.bet_slip = []
    st.rerun()

def remove_bet(index):
    st.session_state.bet_slip.pop(index)
    st.rerun()

def get_user_bets(username):
    """Retrieves the user's placed bets from MongoDB."""
    try:
        collection = db["bets"]
        user_bets = list(collection.find({"username": username}))
        return user_bets
    except Exception as e:
        st.error(f"Error getting user bets: {e}")
        return []

# Initialize bet_slip in session state
if 'bet_slip' not in st.session_state:
    st.session_state.bet_slip = []

# --- Streamlit App Layout ---
st.markdown("<h1>VarnyBet</h1>", unsafe_allow_html=True)

if 'username' not in st.session_state:
    # Add registration and login forms
    col1, col2 = st.columns(2)
    with col1:
        register_user()
    with col2:
        login_user()
else:
    st.write(f"<p style='color: white;'>Zdravo, {st.session_state.username}!</p>", unsafe_allow_html=True)
    balance = get_user_balance(st.session_state.username)
    st.markdown(f"<p style='color: white;'>Stanje: {balance} merkuraca</p>", unsafe_allow_html=True)
    if st.button("Logout"):
        del st.session_state.username
        st.rerun()

    # Make the sidebar collapsible by default
    data_source_for_parsing = CSV_CONTENT  # Fallback to string content
    parsed_odds_data = parse_csv_data(data_source_for_parsing)
    with st.sidebar:
        st.header("Bet Slip")

        # Add a button to toggle the visibility of the bet slip
        if 'show_bet_slip' not in st.session_state:
            st.session_state.show_bet_slip = True

        if st.button(f"Hide Bet Slip" if st.session_state.show_bet_slip else "Show Bet Slip"):
            st.session_state.show_bet_slip = not st.session_state.show_bet_slip

        if st.session_state.show_bet_slip:
            st.markdown("<div class='bet-slip'>", unsafe_allow_html=True)

            # Calculate total odds and handle bet removal
            total_odds = 1.0
            bets_to_remove = []
            for i, bet in enumerate(st.session_state.bet_slip):
                st.markdown(f"""<div class='bet-slip-item'>
                                        <span style="color: #6b8a73;">{bet['player']} - {bet['odd_type']} ({bet['odd_value']:.2f})</span>
                                        </div>""", unsafe_allow_html=True)
                if st.button(f"Remove {i}", key=f"remove_{i}"):
                    bets_to_remove.append(i)

            # Remove bets after calculating total odds to avoid incorrect total
            for i in sorted(bets_to_remove, reverse=True):
                remove_bet(i)

            total_odds = 1.0
            for bet in st.session_state.bet_slip:
                total_odds *= bet['odd_value']
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown(f"**Total Odds: {total_odds:.2f}**", unsafe_allow_html=True)
        else:
            st.info("Your bet slip is empty.")

        if st.button("Clear Bet Slip"):
            clear_bet_slip()

        bet_amount = st.number_input("Enter bet amount", min_value=1, max_value=balance, value=1)

        if st.button("Place Bet"):
            if not st.session_state.bet_slip:
                st.error("Please add bets to the bet slip.")
            elif bet_amount > balance:
                st.error("Insufficient balance.")
            else:
                # Deduct bet amount from user balance
                new_balance = balance - bet_amount
                try:
                    collection = db["users"]
                    collection.update_one({"username": st.session_state.username}, {"$set": {"balance": new_balance}})

                    # Store bet details in "bets" collection
                    bets_collection = db["bets"]
                    bet_details = {
                        "username": st.session_state.username,
                        "bet_amount": bet_amount,
                        "bets": st.session_state.bet_slip,
                        "timestamp": pd.Timestamp.now()
                    }
                    bets_collection.insert_one(bet_details)

                    st.success(f"Bet placed successfully! New balance: {new_balance} coins")
                    clear_bet_slip()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error placing bet: {e}")

        if st.button("Show Placed Bets"):
            user_bets = get_user_bets(st.session_state.username)
            if user_bets:
                st.write("Your Placed Bets:")
                for bet in user_bets:
                    st.write(f"Bet Amount: {bet['bet_amount']}")
                    st.write("Bets:")
                    for b in bet['bets']:
                        st.write(f"- {b['player']} - {b['odd_type']} ({b['odd_value']})")
                    st.write(f"Timestamp: {bet['timestamp']}")
                    st.write("---")
            else:
                st.info("No bets placed yet.")

    if not parsed_odds_data:
        st.warning("No valid player odds data found. Please check the CSV format or upload a valid file.")
    else:
        # Initialize bet_slip in session state

        def add_bet(player, odd_type, odd_value):
            bet = {"player": player, "odd_type": odd_type, "odd_value": odd_value}
            # Check if there's already a bet for this player
            for i, existing_bet in enumerate(st.session_state.bet_slip):
                if existing_bet['player'] == player:
                    # Replace the existing bet with the new one
                    st.session_state.bet_slip[i] = bet
                    st.rerun()
                    return
            # If no existing bet, add the new bet
            st.session_state.bet_slip.append(bet)
            st.rerun()

        team_icons = {
            "Kvoteri": "👕",  # Shirt emoji for Kvoteri
            "Gaucosi": "👚",  # Different shirt emoji for Gaucosi
        }

        for league, players in parsed_odds_data.items():
            if not players:
                continue

            st.markdown(f"<div class='league-header'>{league}</div>", unsafe_allow_html=True)

            num_columns = 3  # Using 3 columns for a more compact view
            cols = st.columns(num_columns)
            col_idx = 0

            for player_bet in players:
                # Cycle through columns
                current_col = cols[col_idx % num_columns]
                with current_col:
                    team_icon = team_icons.get(player_bet['team'], "")  # Get team icon or empty string
                    st.markdown(f"""
                        <div class='bet-card'>
                            <div class='match-info'>{player_bet['date']} - {player_bet['time']}</div>
                            <div class='player-name'><span class='team-icon'>{team_icon}</span>{player_bet['player']}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    if st.button(f"MANJE {player_bet['gr']:.1f} - {player_bet['under_odd']:.2f}", key=f"under_{player_bet['player']}_{col_idx}"):
                        add_bet(player_bet['player'], "Under", player_bet['under_odd'])
                    if st.button(f"VIŠE {player_bet['gr']:.1f} - {player_bet['over_odd']:.2f}", key=f"over_{player_bet['player']}_{col_idx}"):
                        add_bet(player_bet['player'], "Over", player_bet['over_odd'])
                    col_idx += 1

    # --- Footer ---
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #718096; font-size: 0.8em;'>Odds data displayed for informational purposes.</div>", unsafe_allow_html=True)
