import streamlit as st
import json
from forex_python.converter import CurrencyRates, RatesNotAvailableError

# Common Forex pairs and instruments
COMMON_PAIRS = [
    "EURUSD", "USDJPY", "GBPUSD", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD",
    "EURGBP", "EURJPY", "GBPJPY", "AUDJPY", "CHFJPY", "CADJPY",
    "GOLD", "SILVER", "US30", "NAS100", "SPX500", "BTCUSD", "ETHUSD"
]

# Common Indian stocks and indices
INDIAN_INSTRUMENTS = [
    "NIFTY 50", "BANKNIFTY", "SENSEX", "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"
]

c = CurrencyRates()

def load_firm_rules(firm_name):
    with open('data/firms.json', 'r') as f:
        firms = json.load(f)
    return firms.get(firm_name, {})

def fetch_live_price(pair):
    try:
        base = pair[:3]
        quote = pair[3:]
        return c.get_rate(base, quote)
    except (RatesNotAvailableError, ValueError):
        return None

def calculate_pip_value(pair, lot_size, account_currency, price=None):
    if "JPY" in pair:
        pip_decimal = 0.01
    else:
        pip_decimal = 0.0001

    assumed_price = price if price else 1.0

    if pair.endswith("USD"):
        pip_value = pip_decimal * lot_size * 100000
    elif pair.startswith("USD"):
        pip_value = (pip_decimal / assumed_price) * lot_size * 100000
    else:
        pip_value = (pip_decimal / assumed_price) * lot_size * 100000

    return pip_value

def calculate_lot_size(risk_amount, stop_loss_pips, pip_value_per_lot):
    return risk_amount / (stop_loss_pips * pip_value_per_lot)

def calculate_profit(pips, lot_size, pip_value):
    return pips * lot_size * pip_value

def calculate_risk_reward(entry_price, stop_loss, take_profit, risk_amount):
    risk_pips = abs(entry_price - stop_loss) / 0.0001
    reward_pips = abs(take_profit - entry_price) / 0.0001
    rr_ratio = reward_pips / risk_pips if risk_pips != 0 else 0
    pip_value = risk_amount / risk_pips if risk_pips != 0 else 0
    return risk_pips, reward_pips, rr_ratio, pip_value

def calculate_new_target(total_target, current_best_day, max_daily_percent):
    max_daily_allowed = total_target * (max_daily_percent / 100)
    if current_best_day > max_daily_allowed:
        remaining = total_target - current_best_day
        remaining_days = 10 - 1
        new_daily_limit = remaining / remaining_days if remaining_days else 0
        return remaining, remaining_days, new_daily_limit
    return None, None, None

def validate_daily_drawdown(current_drawdown, max_daily_drawdown):
    return current_drawdown <= max_daily_drawdown

st.set_page_config(page_title="Forex Prop Firm Rules", layout="wide")
st.title("\U0001F4C8 Prop Firm Tools")

tab_main1, tab_main2 = st.tabs(["🌍 Forex Calculators", "🇮🇳 Indian Market Tools"])

with tab_main1:
    firm = st.selectbox("Select a Prop Firm", [
        "FTMO", "MyForexFunds", "The Funded Trader", "True Forex Funds", 
        "Fidelcrest", "FunderPro", "Funding Pips", "FundedNext"
    ])

    rules = load_firm_rules(firm)

    if rules:
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
            "\U0001F4C8 Evaluation Phases", "\U0001F4BC Funded Account", "\U0001F4CA All Phases Overview", 
            "⚙️ Trading Rules", "\U0001F4C9 Daily Drawdown Validator", "👠 Pip Value Calculator", 
            "📏 Lot Size Calculator", "\U0001F4B0 Profit Calculator", "\U0001F4C6 Consistency Checker",
            "🫩 Risk-Reward Optimizer"
        ])

        with tab5:
            st.subheader("\U0001F4C9 Daily Drawdown Validator")
            max_dd = rules.get("max_daily_drawdown", 5)
            current_dd = st.number_input("Today's Drawdown (%)", value=0.0)
            if validate_daily_drawdown(current_dd, max_dd):
                st.success(f"✅ Within limit ({current_dd}% <= {max_dd}%)")
            else:
                st.error(f"❌ Exceeded daily drawdown limit of {max_dd}%")

        with tab6:
            st.subheader("💠 Pip Value Calculator")
            pair = st.selectbox("Select Pair", COMMON_PAIRS, index=0)
            lot_size = st.number_input("Lot Size", value=1.0)
            account_currency = st.text_input("Account Currency", value="USD")
            price = fetch_live_price(pair)

            pip_value = calculate_pip_value(pair, lot_size, account_currency, price)
            st.markdown(f"**Pip Value:** ${pip_value:.2f}")

        with tab7:
            st.subheader("📏 Lot Size Calculator")
            risk_amount = st.number_input("Risk Amount ($)", value=100.0)
            stop_loss_pips = st.number_input("Stop Loss (pips)", value=20.0)
            pair = st.selectbox("Select Pair for Lot Size", COMMON_PAIRS, index=0, key='lotpair')
            price = fetch_live_price(pair)
            pip_value = calculate_pip_value(pair, 1, "USD", price)

            lot_size = calculate_lot_size(risk_amount, stop_loss_pips, pip_value)
            st.markdown(f"**Recommended Lot Size:** {lot_size:.2f} lots")

        with tab8:
            st.subheader("💰 Profit Calculator")
            profit_pips = st.number_input("Profit (in pips)", value=50.0)
            lot_size_profit = st.number_input("Lot Size Used", value=1.0)
            pair_profit = st.selectbox("Select Pair for Profit", COMMON_PAIRS, index=0, key='profitpair')
            price = fetch_live_price(pair_profit)
            pip_value = calculate_pip_value(pair_profit, 1, "USD", price)

            profit = calculate_profit(profit_pips, lot_size_profit, pip_value)
            st.markdown(f"**Profit:** {profit_pips:.1f} pips = ${profit:.2f}")

        with tab9:
            st.subheader("\U0001F4C6 Consistency Checker")
            total_target = st.number_input("Total Profit Target ($)", value=1000.0)
            max_daily_percent = rules.get("consistency_limit", 15)
            best_day_profit = st.number_input("Best Day Profit ($)", value=400.0)

            remaining, remaining_days, new_limit = calculate_new_target(
                total_target, best_day_profit, max_daily_percent
            )

            if remaining is not None:
                st.error("❌ Consistency Rule Broken!")
                st.markdown(f"**Remaining Target:** ${remaining:.2f}")
                st.markdown(f"**Remaining Days:** {remaining_days}")
                st.markdown(f"**New Daily Limit:** ${new_limit:.2f}/day")
                stop_loss = st.number_input("Stop Loss for New Lot Size (pips)", value=20.0)
                pip_value = 10
                new_lot = calculate_lot_size(new_limit, stop_loss, pip_value)
                st.markdown(f"**Adjusted Lot Size:** {new_lot:.2f} lots")
            else:
                st.success("✅ Within consistency rules")

        with tab10:
            st.subheader("\U0001F9AE Risk-Reward Optimizer")
            entry = st.number_input("Entry Price", value=1.1000)
            stop_loss = st.number_input("Stop Loss Price", value=1.0950)
            take_profit = st.number_input("Take Profit Price", value=1.1100)
            risk_amount = st.number_input("Risk Amount ($)", value=100.0, key='riskrr')

            risk_pips, reward_pips, rr_ratio, pip_value = calculate_risk_reward(
                entry, stop_loss, take_profit, risk_amount
            )

            st.markdown(f"**Risk (pips):** {risk_pips:.1f}")
            st.markdown(f"**Reward (pips):** {reward_pips:.1f}")
            st.markdown(f"**Risk-Reward Ratio:** {rr_ratio:.2f}")
            st.markdown(f"**Pip Value per Lot:** ${pip_value:.2f}")

with tab_main2:
    st.subheader("🇮🇳 Indian Stock Market Lot & Risk Calculator")
    instrument = st.selectbox("Select Instrument", INDIAN_INSTRUMENTS)
    capital = st.number_input("Total Capital (₹)", value=100000.0)
    risk_percent = st.number_input("Risk % per trade", value=1.0)
    stop_loss_points = st.number_input("Stop Loss (points)", value=20.0)
    price_per_lot = st.number_input("Instrument Price per Lot", value=200.0)
    lot_size = st.number_input("Lot Size (shares/contract)", value=50)

    risk_amount = (risk_percent / 100) * capital
    point_value = lot_size
    lot_count = risk_amount / (stop_loss_points * point_value)
    st.markdown(f"**Max Risk Amount:** ₹{risk_amount:.2f}")
    st.markdown(f"**Recommended Lot Count:** {lot_count:.2f} lots")
# Your full app.py content (already shown in canvas, so will skip re-inserting here)
