"""
Structured Notes Tracking System - Web Application
Built with Streamlit for mobile-responsive interface
Production-ready with cloud database support and authentication
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import plotly.express as px
import os
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

from database import StructuredNotesDB
from fetch_prices_new import update_all_prices
from status_calculator import calculate_note_status, update_all_statuses
from coupon_calculator import calculate_expected_coupon, calculate_accumulated_coupon
from payment_date_generator import generate_payment_dates, format_dates_for_storage, format_dates_for_display, parse_manual_dates
from auth import check_password, show_logout_button
from export_utils import prepare_notes_for_export, export_to_csv, export_to_excel, get_export_filename, export_notes_with_underlyings
from import_utils import validate_excel_columns, parse_excel_to_notes, get_excel_template_dataframe
from excel_templates import get_fcn_template, get_phoenix_template, get_ben_template
from barrier_checker import check_all_barriers
from ai_extractor import extract_text_from_pdf, extract_note_data_with_claude, extract_note_data_with_openai
import time

# Page configuration
st.set_page_config(
    page_title=os.getenv('APP_TITLE', "Structured Notes Tracker"),
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Authentication check
if not check_password():
    st.stop()

# Enhanced CSS for professional appearance
st.markdown("""
<style>
    /* Professional color scheme and layout */
    .main .block-container {
        padding: 2rem 1rem;
        max-width: 1400px;
    }
    
    /* Header styling */
    h1 {
        color: #1e3a8a;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    h2, h3 {
        color: #334155;
        font-weight: 600;
    }
    
    /* Card-style containers */
    .stMetric {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Form styling */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {
        border-radius: 6px;
    }
    
    /* Data table styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Status badges */
    .status-alive {
        background: #10b981;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.875rem;
    }
    
    .status-ko {
        background: #ef4444;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.875rem;
    }
    
    .status-ki {
        background: #f59e0b;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.875rem;
    }
    
    /* Mobile responsive */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem 0.5rem;
        }
        .stButton > button {
            min-height: 44px;
            font-size: 16px;
        }
        h1 {
            font-size: 1.75rem;
        }
    }
    
    /* Info boxes */
    .stAlert {
        border-radius: 8px;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: #f8fafc;
    }
    
    /* Custom divider */
    hr {
        margin: 1.5rem 0;
        border: none;
        border-top: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
@st.cache_resource
def init_database():
    db = StructuredNotesDB()
    db.connect()
    db.create_tables()
    return db

db = init_database()

# Sidebar navigation
st.sidebar.title("📊 Navigation")
page = st.sidebar.radio("Menu", ["Dashboard", "Client Portfolio", "Add New Note", "AI Extract from PDF", "Import from Excel", "View Notes", "Edit Note", "Settings"], label_visibility="collapsed")

# Show logout button if authenticated
show_logout_button()

# ============================================================================
# PAGE 1: DASHBOARD
# ============================================================================
if page == "Dashboard":
    st.title("📊 Structured Notes Dashboard")
    
    # Get all notes
    all_notes = db.get_all_notes()
    
    if all_notes:
        df_notes = pd.DataFrame(all_notes)
        
        # Key metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Notes", len(df_notes))
        with col2:
            total_notional = df_notes['notional_amount'].sum()
            st.metric("Total Notional", f"${total_notional:,.0f}" if total_notional else "N/A")
        with col3:
            alive_notes = len(df_notes[df_notes['current_status'] == 'Alive'])
            st.metric("Alive", alive_notes)
        with col4:
            ko_notes = len(df_notes[df_notes['current_status'] == 'Knocked Out'])
            st.metric("Knocked Out", ko_notes)
        with col5:
            unique_customers = df_notes['customer_name'].nunique()
            st.metric("Total Clients", unique_customers)
        
        # Status distribution
        st.subheader("📊 Status Distribution")
        status_counts = df_notes['current_status'].value_counts()
        
        col1, col2 = st.columns([1, 2])
        with col1:
            for status, count in status_counts.items():
                st.metric(status, count)
        
        with col2:
            fig = px.pie(values=status_counts.values, names=status_counts.index,
                        title="Notes by Status")
            st.plotly_chart(fig, use_container_width=True)
        
        # Charts
        st.subheader("Portfolio Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # By product type
            product_dist = df_notes['type_of_structured_product'].value_counts()
            fig = px.pie(values=product_dist.values, names=product_dist.index, 
                        title="Distribution by Product Type")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # By customer
            customer_notional = df_notes.groupby('customer_name')['notional_amount'].sum().nlargest(10)
            fig = px.bar(x=customer_notional.values, y=customer_notional.index, 
                        orientation='h', title="Top 10 Clients by Notional")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No notes in database. Add your first note using 'Add New Note' page.")

# ============================================================================
# PAGE 2: CLIENT PORTFOLIO ANALYTICS
# ============================================================================
elif page == "Client Portfolio":
    st.title("👤 Client Portfolio Analytics")
    
    # Get all notes
    all_notes = db.get_all_notes()
    
    if all_notes:
        df_all = pd.DataFrame(all_notes)
        
        # Client selection
        clients = sorted(df_all['customer_name'].unique().tolist())
        selected_client = st.selectbox("📋 Select Client", clients, key="client_portfolio_select")
        
        if selected_client:
            # Filter notes for selected client
            client_notes = [note for note in all_notes if note['customer_name'] == selected_client]
            df_client = pd.DataFrame(client_notes)
            
            # === SECTION 1: PORTFOLIO SUMMARY ===
            st.markdown("---")
            st.subheader("💼 Portfolio Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_notes = len(client_notes)
                st.metric("Total Notes", total_notes)
            
            with col2:
                total_notional = df_client['notional_amount'].sum()
                st.metric("Total Notional", f"${total_notional:,.0f}")
            
            with col3:
                alive_count = len(df_client[df_client['current_status'] == 'Alive'])
                st.metric("Active Notes", alive_count)
            
            with col4:
                ki_count = len(df_client[df_client['current_status'] == 'Knocked In'])
                st.metric("KI Notes", ki_count, delta=None if ki_count == 0 else "⚠️")
            
            # === SECTION 2: UNDERLYING EXPOSURE ANALYSIS ===
            st.markdown("---")
            st.subheader("📈 Underlying Exposure Analysis")
            st.caption("Shows percentage of client's notes containing each underlying")
            
            # Get all underlyings for this client
            underlying_exposure = {}
            
            for note in client_notes:
                note_id = int(note['id'])
                note_details = db.get_note_with_underlyings(note_id)
                notional = note['notional_amount']
                isin = note.get('isin', 'No ISIN')
                
                for u in note_details['underlyings']:
                    ticker = u['underlying_ticker']
                    
                    if ticker not in underlying_exposure:
                        underlying_exposure[ticker] = {
                            'isins': set(),
                            'total_notional': 0
                        }
                    
                    # Only count each ISIN once per underlying
                    if isin not in underlying_exposure[ticker]['isins']:
                        underlying_exposure[ticker]['isins'].add(isin)
                        underlying_exposure[ticker]['total_notional'] += notional
            
            # Create exposure dataframe
            exposure_data = []
            for ticker, data in underlying_exposure.items():
                note_count = len(data['isins'])
                pct_of_notes = (note_count / total_notes) * 100
                
                exposure_data.append({
                    'Underlying': ticker,
                    'Notes': note_count,
                    '% of Portfolio': pct_of_notes,
                    'Total Notional': data['total_notional']
                })
            
            df_exposure = pd.DataFrame(exposure_data).sort_values('% of Portfolio', ascending=False)
            
            # Display exposure table and chart
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.write("**Underlying Exposure Table**")
                display_exposure = df_exposure.copy()
                display_exposure['Total Notional'] = display_exposure['Total Notional'].apply(lambda x: f"${x:,.0f}")
                display_exposure['% of Portfolio'] = display_exposure['% of Portfolio'].apply(lambda x: f"{x:.1f}%")
                st.dataframe(display_exposure[['Underlying', 'Notes', '% of Portfolio', 'Total Notional']], 
                           use_container_width=True, hide_index=True)
                
                st.caption(f"📊 {len(df_exposure)} unique underlyings in {total_notes} notes")
            
            with col2:
                st.write("**Portfolio Composition**")
                # Bar chart showing percentage of notes
                fig = px.bar(df_exposure.head(10), 
                           x='% of Portfolio', 
                           y='Underlying',
                           orientation='h',
                           text='% of Portfolio',
                           title="Top 10 Underlyings (% of Notes)",
                           color='% of Portfolio',
                           color_continuous_scale='Blues')
                fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                fig.update_layout(yaxis={'categoryorder':'total ascending'}, 
                                xaxis_title="% of Client's Notes (max 100%)",
                                showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            
            # === SECTION 3: MATURITY TIMELINE ===
            st.markdown("---")
            st.subheader("📅 Maturity Timeline")
            
            # Get earliest and latest maturity dates
            df_client_sorted = df_client.sort_values('final_valuation_date')
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**🔜 Earliest Maturity**")
                earliest_note = df_client_sorted.iloc[0]
                earliest_id = int(earliest_note['id'])
                earliest_details = db.get_note_with_underlyings(earliest_id)
                
                st.write(f"**Date:** {earliest_note['final_valuation_date']}")
                st.write(f"**ISIN:** {earliest_note['isin'] or 'No ISIN'}")
                st.write(f"**Product:** {earliest_note['type_of_structured_product']}")
                st.write(f"**Notional:** ${earliest_note['notional_amount']:,.0f}")
                st.write(f"**Status:** {earliest_note['current_status']}")
                st.write("**Underlyings:**")
                for u in earliest_details['underlyings']:
                    st.caption(f"  • {u['underlying_ticker']}")
            
            with col2:
                st.write("**🔚 Furthest Maturity**")
                latest_note = df_client_sorted.iloc[-1]
                latest_id = int(latest_note['id'])
                latest_details = db.get_note_with_underlyings(latest_id)
                
                st.write(f"**Date:** {latest_note['final_valuation_date']}")
                st.write(f"**ISIN:** {latest_note['isin'] or 'No ISIN'}")
                st.write(f"**Product:** {latest_note['type_of_structured_product']}")
                st.write(f"**Notional:** ${latest_note['notional_amount']:,.0f}")
                st.write(f"**Status:** {latest_note['current_status']}")
                st.write("**Underlyings:**")
                for u in latest_details['underlyings']:
                    st.caption(f"  • {u['underlying_ticker']}")
            
            # === SECTION 4: KI RISK ALERT ===
            st.markdown("---")
            st.subheader("⚠️ KI Risk Alert")
            st.caption("Monitoring notes from Observation Start Date to Final Valuation Date")
            
            # Calculate KI risk
            from datetime import datetime, timedelta
            today = date.today()
            
            ki_notes_in_observation = []  # KI notes in observation period
            ki_near_breach = []  # Active notes near KI with < 30 days
            
            for note in client_notes:
                try:
                    obs_start = datetime.strptime(note['observation_start_date'], '%Y-%m-%d').date()
                    final_val = datetime.strptime(note['final_valuation_date'], '%Y-%m-%d').date()
                    days_to_maturity = (final_val - today).days
                except:
                    continue
                
                # Check if currently in observation period
                in_observation = obs_start <= today <= final_val
                
                note_id = int(note['id'])
                note_details = db.get_note_with_underlyings(note_id)
                
                # Determine KI determination type
                ki_type = note.get('ki_type', 'Daily')
                if ki_type == 'EKI':
                    ki_determination = f"EKI - Final date only ({note['final_valuation_date']})"
                else:
                    ki_determination = "Daily KI monitoring"
                
                # SECTION 1: Notes that have Knocked In during observation period
                if note['current_status'] == 'Knocked In' and in_observation:
                    for u in note_details['underlyings']:
                        if u.get('last_close_price') and u.get('ki_price'):
                            ki_notes_in_observation.append({
                                'ISIN': note.get('isin', 'No ISIN'),
                                'Product': note['type_of_structured_product'],
                                'Underlying': u['underlying_ticker'],
                                'Current': u['last_close_price'],
                                'KI Barrier': u['ki_price'],
                                '% vs KI': ((u['last_close_price'] - u['ki_price']) / u['ki_price']) * 100,
                                'Days to Maturity': days_to_maturity,
                                'KI Event Date': note.get('ki_event_date', 'Not recorded'),
                                'KI Type': ki_determination
                            })
                    continue
                
                # Skip if not in observation or already terminal status
                if not in_observation or note['current_status'] in ['Knocked Out', 'Ended', 'Converted']:
                    continue
                
                try:
                    final_val = datetime.strptime(note['final_valuation_date'], '%Y-%m-%d').date()
                    days_to_maturity = (final_val - today).days
                except:
                    continue
                
                note_id = int(note['id'])
                note_details = db.get_note_with_underlyings(note_id)
                
                # Determine KI determination date based on product type
                ki_type = note.get('ki_type', 'Daily')
                product_type = note['type_of_structured_product']
                
                if ki_type == 'EKI':
                    ki_determination = f"Final date only ({note['final_valuation_date']})"
                    ki_status_text = "EKI - Final date only"
                else:
                    ki_determination = "Daily monitoring"
                    ki_status_text = "Daily KI"
                
                # Check each underlying
                for u in note_details['underlyings']:
                    if not u['ki_price'] or not u['last_close_price']:
                        continue
                    
                    # Calculate distance from KI
                    pct_above_ki = ((u['last_close_price'] - u['ki_price']) / u['ki_price']) * 100
                    
                    risk_data = {
                        'ISIN': note.get('isin', 'No ISIN'),
                        'Product': product_type,
                        'Underlying': u['underlying_ticker'],
                        'Current': u['last_close_price'],
                        'KI Barrier': u['ki_price'],
                        '% vs KI': pct_above_ki,
                        'Days to Maturity': days_to_maturity,
                        'KI Date': ki_determination,
                        'Final Val': note['final_valuation_date']
                    }
                    
                    # Categorize risk - only near-breach for active notes
                    if 0 < pct_above_ki <= 5 and days_to_maturity <= 30:
                        # Close to breach and near maturity
                        risk_data['Risk Level'] = '🟠 HIGH RISK'
                        ki_near_breach.append(risk_data)
            
            # === Display Results ===
            
            # Section 1: Knocked In Notes (Primary Focus)
            if ki_notes_in_observation:
                affected_isins = set([item['ISIN'] for item in ki_notes_in_observation])
                
                st.error(f"🔴 KNOCKED IN: {len(affected_isins)} note(s) have been Knocked In during observation period!")
                st.caption("These notes are being tracked from Observation Start → Final Valuation Date")
                
                df_ki_notes = pd.DataFrame(ki_notes_in_observation)
                df_ki_notes = df_ki_notes.sort_values('Days to Maturity')
                
                # Format for display
                df_ki_notes['Current'] = df_ki_notes['Current'].apply(lambda x: f"${x:.2f}")
                df_ki_notes['KI Barrier'] = df_ki_notes['KI Barrier'].apply(lambda x: f"${x:.2f}")
                df_ki_notes['% vs KI'] = df_ki_notes['% vs KI'].apply(lambda x: f"{x:.2f}%")
                
                st.dataframe(df_ki_notes[['ISIN', 'Product', 'Underlying', 'Current', 'KI Barrier', 
                                         '% vs KI', 'Days to Maturity', 'KI Event Date', 'KI Type']], 
                           use_container_width=True, hide_index=True)
                
                st.caption("⚠️ These notes will convert to shares if Worst Performing Share is below Strike at maturity")
                st.caption("💡 Monitor these closely until Final Valuation Date")
            
            # Section 2: Near-Breach Risks (Secondary Focus)
            if ki_near_breach:
                # Count unique ISINs
                affected_isins = set([item['ISIN'] for item in ki_near_breach])
                
                st.warning(f"🟠 WARNING: {len(ki_near_breach)} underlying position(s) within 5% of KI barrier!")
                st.warning(f"📋 Affects {len(affected_isins)} note(s) with < 30 days to maturity")
                
                df_near = pd.DataFrame(ki_near_breach)
                df_near = df_near.sort_values('% vs KI')
                
                # Format for display
                df_near['Current'] = df_near['Current'].apply(lambda x: f"${x:.2f}")
                df_near['KI Barrier'] = df_near['KI Barrier'].apply(lambda x: f"${x:.2f}")
                df_near['% vs KI'] = df_near['% vs KI'].apply(lambda x: f"{x:.2f}%")
                
                st.dataframe(df_near[['ISIN', 'Product', 'Underlying', 'Current', 'KI Barrier', 
                                     '% vs KI', 'Days to Maturity', 'KI Date']], 
                           use_container_width=True, hide_index=True)
                
                st.caption("⚠️ **Remember:** If ANY ONE of these underlyings hits KI, the entire note becomes Knocked In!")
                st.caption("💡 Monitor daily and update prices frequently for these high-risk positions")
            
            # All clear message
            if not ki_notes_in_observation and not ki_near_breach:
                st.success("✅ No KI risks detected")
                st.caption("All notes have all underlyings well above KI barriers or have sufficient time to maturity")
            
            # === SECTION 5: RETURN ESTIMATE ===
            st.markdown("---")
            st.subheader("💰 Expected Return Analysis")
            
            # Calculate expected returns for each note
            return_data = []
            total_expected_coupon = 0
            
            for note in client_notes:
                # Calculate expected coupon for this note
                expected_coupon = calculate_expected_coupon(
                    note['notional_amount'],
                    note['coupon_per_annum'],
                    note['coupon_payment_dates']
                )
                
                total_expected_coupon += expected_coupon
                
                # Calculate return % for this note
                if note['notional_amount'] > 0:
                    note_return_pct = (expected_coupon / note['notional_amount']) * 100
                else:
                    note_return_pct = 0
                
                # Calculate number of payments
                payment_dates = note.get('coupon_payment_dates', '')
                num_payments = len(payment_dates.split(',')) if payment_dates else 0
                
                return_data.append({
                    'ISIN': note.get('isin', 'No ISIN'),
                    'Product': note['type_of_structured_product'],
                    'Notional': note['notional_amount'],
                    'Coupon p.a.': note['coupon_per_annum'] * 100,
                    'Payments': num_payments,
                    'Expected Coupon': expected_coupon,
                    'Return %': note_return_pct,
                    'Status': note['current_status']
                })
            
            # Calculate portfolio-level return
            if total_notional > 0:
                portfolio_return_pct = (total_expected_coupon / total_notional) * 100
            else:
                portfolio_return_pct = 0
            
            # Display return metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Expected Coupon", f"${total_expected_coupon:,.2f}")
            
            with col2:
                st.metric("Portfolio Return %", f"{portfolio_return_pct:.2f}%")
            
            with col3:
                avg_coupon_rate = df_client['coupon_per_annum'].mean() * 100
                st.metric("Avg Coupon Rate", f"{avg_coupon_rate:.2f}%")
            
            with col4:
                # Calculate weighted average tenor
                total_payments = sum([r['Payments'] for r in return_data])
                avg_payments = total_payments / len(return_data) if return_data else 0
                st.metric("Avg Payment Count", f"{avg_payments:.1f}")
            
            # Return breakdown table
            st.write("**Return Breakdown by ISIN**")
            df_returns = pd.DataFrame(return_data).sort_values('Expected Coupon', ascending=False)
            
            # Format for display
            display_returns = df_returns.copy()
            display_returns['Notional'] = display_returns['Notional'].apply(lambda x: f"${x:,.0f}")
            display_returns['Coupon p.a.'] = display_returns['Coupon p.a.'].apply(lambda x: f"{x:.2f}%")
            display_returns['Expected Coupon'] = display_returns['Expected Coupon'].apply(lambda x: f"${x:,.2f}")
            display_returns['Return %'] = display_returns['Return %'].apply(lambda x: f"{x:.2f}%")
            
            st.dataframe(display_returns, use_container_width=True, hide_index=True)
            
            st.caption("💡 **Expected Coupon:** Total coupons to be received if note stays alive until maturity")
            st.caption("📊 **Portfolio Return %:** Total expected coupons across all notes / Total notional invested")
            st.caption("⚠️ **Note:** This assumes all notes stay alive (no KO/KI) and all coupons are paid")
            
            # === SECTION 6: STATUS BREAKDOWN ===
            st.markdown("---")
            st.subheader("📊 Portfolio by Status")
            
            status_breakdown = df_client['current_status'].value_counts()
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                for status, count in status_breakdown.items():
                    notional = df_client[df_client['current_status'] == status]['notional_amount'].sum()
                    st.metric(status, f"{count} notes", f"${notional:,.0f}")
            
            with col2:
                fig = px.pie(values=status_breakdown.values, 
                           names=status_breakdown.index,
                           title=f"{selected_client} - Notes by Status")
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No notes in database yet.")

# ============================================================================
# PAGE 3: AI EXTRACT FROM PDF
# ============================================================================
elif page == "AI Extract from PDF":
    st.title("🤖 AI-Powered Termsheet Extraction")
    
    st.info("💡 Upload a termsheet PDF and AI will automatically extract all the data!")
    
    # API Key input
    st.subheader("🔑 Step 1: API Key")
    
    # Check if API key is in secrets
    claude_api_key = os.getenv('CLAUDE_API_KEY', '')
    openai_api_key = os.getenv('OPENAI_API_KEY', '')
    
    col1, col2 = st.columns(2)
    
    with col1:
        use_claude = st.checkbox("Use Claude API", value=bool(claude_api_key))
        if use_claude:
            if not claude_api_key:
                claude_api_key = st.text_input("Claude API Key", type="password",
                                              help="Get from: https://console.anthropic.com/")
    
    with col2:
        use_openai = st.checkbox("Use OpenAI API", value=bool(openai_api_key))
        if use_openai:
            if not openai_api_key:
                openai_api_key = st.text_input("OpenAI API Key", type="password",
                                              help="Get from: https://platform.openai.com/api-keys")
    
    if not use_claude and not use_openai:
        st.warning("⚠️ Please select and configure at least one AI provider")
        st.markdown("**How to get API keys:**")
        st.markdown("- **Claude:** https://console.anthropic.com/ (Recommended)")
        st.markdown("- **OpenAI:** https://platform.openai.com/api-keys")
        st.stop()
    
    # PDF Upload
    st.markdown("---")
    st.subheader("📄 Step 2: Upload Termsheet PDF")
    
    uploaded_pdf = st.file_uploader(
        "Choose a termsheet PDF",
        type=['pdf'],
        help="Upload the termsheet PDF for AI extraction"
    )
    
    if uploaded_pdf is not None:
        st.success(f"✅ PDF uploaded: {uploaded_pdf.name}")
        
        if st.button("🤖 Extract Data with AI", type="primary", use_container_width=True):
            with st.spinner("🔍 Extracting text from PDF..."):
                pdf_text = extract_text_from_pdf(uploaded_pdf)
            
            if "Error" in pdf_text:
                st.error(pdf_text)
            else:
                st.success(f"✅ Extracted {len(pdf_text)} characters from PDF")
                
                with st.expander("📄 View Extracted Text (First 1000 chars)"):
                    st.text(pdf_text[:1000])
                
                # Call AI API
                extracted_data = None
                
                if use_claude and claude_api_key:
                    with st.spinner("🤖 Claude is analyzing termsheet..."):
                        extracted_data = extract_note_data_with_claude(pdf_text, claude_api_key)
                
                elif use_openai and openai_api_key:
                    with st.spinner("🤖 GPT-4 is analyzing termsheet..."):
                        extracted_data = extract_note_data_with_openai(pdf_text, openai_api_key)
                
                if extracted_data:
                    st.success("✅ AI extraction successful!")
                    
                    # Display extracted data
                    st.subheader("📊 Extracted Data")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.json({k: v for k, v in extracted_data.items() if k != 'underlyings'})
                    
                    with col2:
                        if 'underlyings' in extracted_data:
                            st.write("**Underlyings:**")
                            for idx, u in enumerate(extracted_data['underlyings']):
                                st.json({f"Underlying {idx+1}": u})
                    
                    # Option to use this data
                    st.markdown("---")
                    st.info("💡 You can now copy this data and paste it into 'Add New Note' form, or use the JSON for Excel import")
                    
                    # Download as JSON
                    json_data = json.dumps(extracted_data, indent=2)
                    st.download_button(
                        label="💾 Download as JSON",
                        data=json_data,
                        file_name=f"extracted_{uploaded_pdf.name.replace('.pdf', '.json')}",
                        mime="application/json"
                    )
                else:
                    st.error("❌ AI extraction failed. Please check your API key and try again.")
    else:
        st.info("👆 Please upload a termsheet PDF to begin extraction")
        
        # Show benefits
        with st.expander("🌟 Benefits of AI Extraction"):
            st.markdown("""
            **Why use AI extraction?**
            - ⚡ **Save 10+ minutes** per note (no manual data entry)
            - ✅ **Reduce errors** (no typos or wrong numbers)
            - 📊 **Extract complex data** (all underlyings, barriers, dates)
            - 🤖 **Understands structure** (FCN vs Phoenix vs BEN)
            - 🔄 **Bulk processing** (extract multiple termsheets)
            
            **How it works:**
            1. Upload termsheet PDF
            2. AI reads and understands the document
            3. Extracts all relevant fields
            4. Returns structured JSON data
            5. Copy to Add Note form or import
            
            **Cost:**
            - Claude: ~$0.01 per termsheet
            - OpenAI GPT-4: ~$0.02 per termsheet
            """)

# ============================================================================
# PAGE 4: ADD NEW NOTE
# ============================================================================
elif page == "Add New Note":
    st.title("➕ Add New Structured Note")
    
    with st.form("add_note_form", clear_on_submit=True):
        # CLIENT INFORMATION
        st.subheader("👤 Client Information")
        col1, col2 = st.columns(2)
        
        with col1:
            customer_name = st.text_input("Customer Name *", placeholder="e.g., PT, SU LEI")
        with col2:
            custodian_bank = st.text_input("Custodian Bank", placeholder="e.g., RBC, UBS")
        
        st.markdown("---")
        
        # PRODUCT DETAILS
        st.subheader("📄 Product Details")
        col1, col2 = st.columns(2)
        
        with col1:
            product_type = st.selectbox(
                "Type of Structured Product *",
                ["FCN", "WOFCN", "Phoenix", "BEN", "ACCU", "DECU", "DCN", "WOBEN", "TWINWIN"]
            )
        with col2:
            isin = st.text_input("ISIN", placeholder="e.g., XS3039666410")
        
        col1, col2 = st.columns(2)
        with col1:
            notional_amount = st.number_input("Notional Amount *", min_value=0.0, step=1000.0, format="%.2f")
        with col2:
            currency = st.selectbox("Currency", ["USD", "EUR", "SGD", "HKD", "CHF", "GBP"])
        
        st.markdown("---")
        
        # DATES
        st.subheader("📅 Important Dates")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            trade_date = st.date_input("Trade Date *")
        with col2:
            issue_date = st.date_input("Issue Date *")
        with col3:
            obs_start = st.date_input("Observation Start Date *")
        with col4:
            final_val_date = st.date_input("Final Valuation Date *")
        
        st.markdown("---")
        
        # COUPON INFORMATION
        st.subheader("💰 Coupon Information")
        col1, col2 = st.columns(2)
        
        with col1:
            coupon_per_annum = st.number_input("Coupon per Annum (%) *", min_value=0.0, max_value=100.0, 
                                               step=0.01, format="%.2f")
        with col2:
            # Coupon Barrier (only for Phoenix)
            if product_type == "Phoenix":
                coupon_barrier = st.number_input("Coupon Barrier *", min_value=0.0, step=0.01, format="%.2f")
            else:
                coupon_barrier = None
                st.info("Coupon Barrier only for Phoenix notes")
        
        # Payment dates - Manual input with DD/MM/YYYY support
        st.write("**Coupon Payment Dates**")
        st.info("💡 Enter dates in DD/MM/YYYY format, separated by commas")
        
        coupon_payment_dates_manual = st.text_input(
            "Payment Dates (comma-separated) *",
            placeholder="e.g., 15/12/2025, 15/01/2026, 15/02/2026",
            help="Format: DD/MM/YYYY, separated by commas. Dates can be any interval."
        )
        
        if coupon_payment_dates_manual:
            # Parse and validate
            parsed_dates = parse_manual_dates(coupon_payment_dates_manual)
            if parsed_dates:
                st.success(f"✅ Parsed {len(parsed_dates)} payment dates:")
                st.caption(format_dates_for_display(parsed_dates, '%d/%m/%Y'))
                coupon_payment_dates_input = format_dates_for_storage(parsed_dates)
            else:
                st.error("❌ Could not parse dates. Please check format (DD/MM/YYYY)")
                coupon_payment_dates_input = None
        else:
            coupon_payment_dates_input = None
        
        st.markdown("---")
        
        # BARRIER MONITORING RULES
        st.subheader("🎯 Barrier Monitoring Rules")
        st.info("📌 KO/KI status will be auto-calculated based on these rules and price observations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Knock-Out (KO) Rules**")
            ko_type = st.selectbox(
                "KO Type",
                ["Daily", "Period-End"],
                help="Daily: Monitor every day | Period-End: Monitor at specific intervals"
            )
            
            if ko_type == "Period-End":
                ko_obs_freq = st.selectbox(
                    "KO Observation Frequency",
                    ["Daily", "Weekly", "Monthly", "Quarterly", "Semi-Annually"],
                    help="How often to check KO condition (from observation start date)"
                )
            else:
                ko_obs_freq = "Daily"
            
            st.caption("KO occurs if ALL underlyings exceed their KO prices")
        
        with col2:
            st.write("**Knock-In (KI) Rules**")
            ki_type = st.selectbox(
                "KI Type",
                ["Daily", "EKI"],
                help="Daily: Monitor every day | EKI: Only check on final valuation date"
            )
            
            st.caption("KI occurs if ANY ONE underlying is at or below its KI price")
        
        st.markdown("---")
        
        # UNDERLYING ASSETS
        st.subheader("📈 Underlying Assets")
        st.info("💡 Fill in at least 1 underlying. Leave others blank if not needed.")
        
        underlyings = []
        
        # Always show all 4 underlying boxes (user fills in what they need)
        for i in range(4):
            with st.expander(f"Underlying {i+1}", expanded=(i==0)):
                col1, col2 = st.columns(2)
                
                with col1:
                    u_ticker = st.text_input(f"Ticker {i+1}" + (" *" if i == 0 else ""), 
                                            placeholder="e.g., TSLA",
                                            help="For Yahoo Finance price lookup",
                                            key=f"u_ticker_{i}")
                    u_spot = st.number_input(f"Spot Price {i+1}" + (" *" if i == 0 else ""), 
                                            min_value=0.0, step=0.01, 
                                            format="%.4f", key=f"u_spot_{i}")
                    u_strike = st.number_input(f"Strike Price {i+1}" + (" *" if i == 0 else ""), 
                                              min_value=0.0, step=0.01, 
                                              format="%.4f", key=f"u_strike_{i}")
                
                with col2:
                    u_ko = st.number_input(f"KO Price {i+1}", min_value=0.0, step=0.01, 
                                          format="%.4f", key=f"u_ko_{i}", value=0.0)
                    u_ki = st.number_input(f"KI Price {i+1}", min_value=0.0, step=0.01, 
                                          format="%.4f", key=f"u_ki_{i}", value=0.0)
                
                # Only add to list if ticker is filled
                if u_ticker and u_ticker.strip():
                    underlyings.append({
                        'sequence': i + 1,
                        'underlying_name': u_ticker.strip(),  # Use ticker as name
                        'underlying_ticker': u_ticker.strip(),
                        'spot_price': u_spot if u_spot > 0 else None,
                        'strike_price': u_strike if u_strike > 0 else None,
                        'ko_price': u_ko if u_ko > 0 else None,
                        'ki_price': u_ki if u_ki > 0 else None,
                        'last_close_price': None  # Will be fetched from Yahoo Finance
                    })
        
        # Submit button
        submitted = st.form_submit_button("💾 Save Structured Note", use_container_width=True, type="primary")
        
        if submitted:
            # Validation
            if not customer_name or not product_type:
                st.error("❌ Please fill in all required fields (*)")
            elif notional_amount <= 0:
                st.error("❌ Notional Amount must be greater than 0")
            elif not any(u['underlying_name'] and u['underlying_ticker'] for u in underlyings):
                st.error("❌ Please fill in at least one underlying with name and ticker")
            else:
                try:
                    # Prepare note data
                    note_data = {
                        'customer_name': customer_name.strip(),
                        'custodian_bank': custodian_bank.strip() if custodian_bank else None,
                        'type_of_structured_product': product_type,
                        'notional_amount': notional_amount,
                        'isin': isin.strip() if isin else None,
                        'trade_date': str(trade_date),
                        'issue_date': str(issue_date),
                        'observation_start_date': str(obs_start),
                        'final_valuation_date': str(final_val_date),
                        'coupon_payment_dates': coupon_payment_dates_input.strip() if coupon_payment_dates_input else None,
                        'coupon_per_annum': coupon_per_annum / 100.0,  # Convert to decimal
                        'coupon_barrier': coupon_barrier if product_type == "Phoenix" else None,
                        'ko_type': ko_type,
                        'ko_observation_frequency': ko_obs_freq if ko_type == "Period-End" else None,
                        'ki_type': ki_type
                    }
                    
                    # Filter out empty underlyings
                    valid_underlyings = [u for u in underlyings if u['underlying_name'] and u['underlying_ticker']]
                    
                    # Insert into database
                    note_id = db.insert_structured_note(note_data, valid_underlyings)
                    
                    st.success(f"✅ Structured note saved successfully! (ID: {note_id})")
                    st.balloons()
                    
                    # Show what was saved
                    with st.expander("📋 View Saved Data"):
                        st.json(note_data)
                        st.write("**Underlyings:**")
                        st.json(valid_underlyings)
                    
                except Exception as e:
                    st.error(f"❌ Error saving note: {str(e)}")
                    st.exception(e)

# ============================================================================
# PAGE 4: IMPORT FROM EXCEL
# ============================================================================
elif page == "Import from Excel":
    st.title("📥 Import Notes from Excel")
    
    st.info("💡 Upload an Excel file to bulk import multiple structured notes at once")
    
    # Download template section
    st.subheader("📄 Step 1: Download Template")
    st.write("Choose template based on product type:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # FCN Template
        fcn_template = get_fcn_template()
        fcn_excel = export_to_excel(fcn_template, sheet_name="FCN Template")
        
        st.download_button(
            label="📥 FCN Template",
            data=fcn_excel,
            file_name="fcn_import_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            help="For FCN, WOFCN, ACCU, DECU products"
        )
        st.caption("**FCN/WOFCN:**")
        st.caption("✅ Simple barriers")
        st.caption("✅ Regular coupons")
    
    with col2:
        # Phoenix Template
        phoenix_template = get_phoenix_template()
        phoenix_excel = export_to_excel(phoenix_template, sheet_name="Phoenix Template")
        
        st.download_button(
            label="📥 Phoenix Template",
            data=phoenix_excel,
            file_name="phoenix_import_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            help="For Phoenix/Autocall products with memory coupons"
        )
        st.caption("**Phoenix/Autocall:**")
        st.caption("✅ Step-down KO")
        st.caption("✅ Memory coupons")
    
    with col3:
        # BEN Template
        ben_template = get_ben_template()
        ben_excel = export_to_excel(ben_template, sheet_name="BEN Template")
        
        st.download_button(
            label="📥 BEN Template",
            data=ben_excel,
            file_name="ben_import_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            help="For BEN/Booster products with upside participation"
        )
        st.caption("**BEN/Booster:**")
        st.caption("✅ No coupons")
        st.caption("✅ Upside participation")
    
    st.markdown("---")
    
    # Upload section
    st.subheader("📤 Step 2: Upload Your Excel File")
    
    uploaded_file = st.file_uploader(
        "Choose an Excel file (.xlsx or .xls)",
        type=['xlsx', 'xls'],
        help="Upload your completed Excel file with structured notes data"
    )
    
    if uploaded_file is not None:
        try:
            # Read Excel file
            df = pd.read_excel(uploaded_file)
            
            st.success(f"✅ File uploaded successfully: {uploaded_file.name}")
            st.write(f"📊 Found {len(df)} rows")
            
            # Show preview
            with st.expander("👀 Preview Data (first 5 rows)"):
                st.dataframe(df.head(), use_container_width=True)
            
            # Validate columns
            is_valid, errors = validate_excel_columns(df)
            
            if not is_valid:
                st.error("❌ Excel file validation failed:")
                for error in errors:
                    st.error(f"  • {error}")
                st.info("💡 Please download the template and ensure all required columns are present.")
            else:
                st.success("✅ All required columns found")
                
                # Parse data
                with st.spinner("Parsing Excel data..."):
                    notes, underlyings_list, parse_errors = parse_excel_to_notes(df)
                
                if parse_errors:
                    st.warning(f"⚠️ Found {len(parse_errors)} errors while parsing:")
                    with st.expander("View Errors"):
                        for error in parse_errors:
                            st.error(f"  • {error}")
                
                if notes:
                    st.success(f"✅ Successfully parsed {len(notes)} notes")
                    
                    # Check for duplicates
                    existing_isins = {note.get('isin') for note in all_notes if note.get('isin')}
                    import_isins = [note.get('isin') for note in notes if note.get('isin')]
                    duplicates = [isin for isin in import_isins if isin in existing_isins]
                    
                    if duplicates:
                        st.warning(f"⚠️ Found {len(duplicates)} duplicate ISINs in database:")
                        with st.expander("View Duplicates"):
                            for dup in set(duplicates):
                                st.write(f"• {dup}")
                        
                        st.markdown("**Import Mode:**")
                        import_mode = st.radio(
                            "How to handle duplicates?",
                            ["Skip duplicates (import only new ISINs)", 
                             "Import all (allow duplicates)",
                             "Cancel import"],
                            key="import_mode"
                        )
                    else:
                        st.success("✅ No duplicates detected - all ISINs are new")
                        import_mode = "Import all (allow duplicates)"
                    
                    # Show summary
                    st.subheader("📋 Import Summary")
                    
                    summary_col1, summary_col2, summary_col3 = st.columns(3)
                    with summary_col1:
                        st.metric("Total Notes", len(notes))
                    with summary_col2:
                        total_notional = sum([n['notional_amount'] for n in notes])
                        st.metric("Total Notional", f"${total_notional:,.0f}")
                    with summary_col3:
                        unique_customers = len(set([n['customer_name'] for n in notes]))
                        st.metric("Unique Customers", unique_customers)
                    
                    # Show detailed preview
                    with st.expander("📄 View Notes to be Imported"):
                        for idx, note in enumerate(notes):
                            st.write(f"**{idx+1}. {note['customer_name']}** - {note['type_of_structured_product']}")
                            st.caption(f"Notional: ${note['notional_amount']:,.0f} | ISIN: {note.get('isin', 'N/A')} | {len(underlyings_list[idx])} underlying(s)")
                    
                    # Import button
                    st.markdown("---")
                    
                    col1, col2, col3 = st.columns([2, 1, 2])
                    
                    with col2:
                        if st.button("💾 Import All Notes", type="primary", use_container_width=True):
                            # Check import mode
                            if 'import_mode' in locals() and import_mode == "Cancel import":
                                st.error("❌ Import cancelled")
                            else:
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                imported_count = 0
                                skipped_count = 0
                                failed_count = 0
                                failed_rows = []
                                
                                for idx, (note, underlyings) in enumerate(zip(notes, underlyings_list)):
                                    # Check if should skip duplicates
                                    if 'import_mode' in locals() and import_mode == "Skip duplicates (import only new ISINs)":
                                        if note.get('isin') in existing_isins:
                                            skipped_count += 1
                                            status_text.text(f"Skipped duplicate: {note.get('isin', 'No ISIN')}")
                                            progress_bar.progress((idx + 1) / len(notes))
                                            continue
                                    
                                    try:
                                        # Reconnect to database for each import to avoid connection timeout
                                        try:
                                            db.conn.ping(reconnect=True)  # For MySQL
                                        except:
                                            # For PostgreSQL, check connection and reconnect if needed
                                            try:
                                                db.conn.cursor().execute('SELECT 1')
                                            except:
                                                # Reconnect if connection is closed
                                                db.connect()
                                        
                                        # Insert note
                                        note_id = db.insert_structured_note(note, underlyings)
                                        imported_count += 1
                                        status_text.text(f"Importing... {imported_count}/{len(notes)}")
                                    except Exception as e:
                                        failed_count += 1
                                        error_msg = f"Row {note.get('row_number', idx+2)}: {str(e)}"
                                        failed_rows.append(error_msg)
                                
                                # Update progress
                                progress_bar.progress((idx + 1) / len(notes))
                            
                                progress_bar.empty()
                                status_text.empty()
                                
                                # Show results
                                if imported_count > 0:
                                    st.success(f"🎉 Successfully imported {imported_count} notes!")
                                
                                if skipped_count > 0:
                                    st.info(f"ℹ️ Skipped {skipped_count} duplicate ISINs")
                                
                                if failed_count > 0:
                                    st.warning(f"⚠️ Failed to import {failed_count} notes:")
                                    with st.expander("View Failed Imports"):
                                        for error in failed_rows:
                                            st.error(f"❌ {error}")
                                
                                if imported_count > 0:
                                    st.balloons()
                                    st.info("✅ Import complete! Go to 'View Notes' to see your notes.")
                else:
                    st.warning("⚠️ No valid notes found in the Excel file")
        
        except Exception as e:
            st.error(f"❌ Error reading Excel file: {str(e)}")
            st.exception(e)
    else:
        st.info("👆 Please upload an Excel file to begin import")
        
        # Show column requirements
        with st.expander("📚 Required Columns Reference"):
            st.markdown("""
            ### Required Columns:
            - `customer_name` - Customer/client name
            - `type_of_structured_product` - FCN, WOFCN, ACCU, DECU, Phoenix, DCN, WOBEN, TWINWIN
            - `notional_amount` - Notional amount (number)
            - `trade_date` - Trade date (YYYY-MM-DD or DD/MM/YYYY)
            - `issue_date` - Issue date
            - `observation_start_date` - Observation start date
            - `final_valuation_date` - Final valuation date
            - `coupon_per_annum` - Annual coupon rate (as percentage, e.g., 12.5)
            - `coupon_payment_dates` - Comma-separated dates
            
            ### Optional Columns:
            - `custodian_bank` - Custodian bank name
            - `isin` - ISIN code
            - `coupon_barrier` - Coupon barrier (for Phoenix notes)
            - `ko_type` - Daily or Period-End
            - `ko_observation_frequency` - If Period-End KO
            - `ki_type` - Daily or EKI
            
            ### Underlying Columns (for each underlying 1-4):
            - `underlying_X_ticker` - Ticker symbol (required if underlying exists)
            - `underlying_X_spot_price` - Spot price at trade
            - `underlying_X_strike_price` - Strike price
            - `underlying_X_ko_price` - Knock-out price
            - `underlying_X_ki_price` - Knock-in price
            - `underlying_X_last_close_price` - Latest close price (optional, will be fetched from Yahoo Finance if empty)
            
            (Replace X with 1, 2, 3, or 4)
            
            **Note:** If `last_close_price` is left empty, the system will automatically fetch it from Yahoo Finance when you click "Update Prices".
            """)

# ============================================================================
# PAGE 5: VIEW NOTES
# ============================================================================
elif page == "View Notes":
    st.title("📋 View Structured Notes")
    
    # Get all notes
    all_notes = db.get_all_notes()
    
    if all_notes:
        df_all = pd.DataFrame(all_notes)
        
        # Global action buttons at top
        st.markdown("### 🔄 Global Actions")
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("🔄 Refresh All", use_container_width=True, type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Step 1: Check barriers (KO/KI/Conversion detection)
                    status_text.text("🎯 Step 1/2: Checking barriers...")
                    progress_bar.progress(0.25)
                    
                    ko_count, ki_count, conv_count, barrier_details = check_all_barriers(db.conn)
                    
                    # Step 2: Update all statuses (date-based transitions)
                    progress_bar.progress(0.50)
                    status_text.text("📅 Step 2/2: Updating statuses...")
                    
                    def update_progress(current, total, isin, status):
                        progress = 0.50 + (0.50 * current / total)
                        progress_bar.progress(progress)
                        status_text.text(f"Step 2/2: {current}/{total} - {isin}")
                    
                    updated, status_failed = update_all_statuses(db.conn, progress_callback=update_progress)
                    
                    # Clear progress
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Show results
                    st.success(f"✅ Refresh complete! Updated {updated} notes")
                    
                    # Show barrier events
                    if ko_count > 0 or ki_count > 0 or conv_count > 0:
                        st.info(f"🎯 Barrier Events: KO: {ko_count} | KI: {ki_count} | Converted: {conv_count}")
                        
                        if barrier_details:
                            with st.expander("📋 View Barrier Events"):
                                for detail in barrier_details:
                                    if "🔴 KO:" in detail:
                                        st.error(detail)
                                    elif "🟠 KI:" in detail:
                                        st.warning(detail)
                                    elif "✅" in detail:
                                        st.info(detail)
                                    else:
                                        st.write(detail)
                    
                    # Show status update failures
                    if status_failed:
                        st.warning(f"⚠️ Failed to update {len(status_failed)} notes:")
                        with st.expander("View Failed ISINs"):
                            for failure in status_failed:
                                st.error(f"❌ {failure}")
                    
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"❌ Error: {str(e)}")
                    
        with col2:
            if st.button("💹 Update Prices", use_container_width=True, type="secondary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_price_progress(current, total, ticker, status):
                    progress_bar.progress(current / total)
                    status_text.text(f"{current}/{total}: {ticker} {status}")
                
                try:
                    updated, errors, failed = update_all_prices(db.conn, delay=0.2, progress_callback=update_price_progress)
                    progress_bar.empty()
                    status_text.empty()
                    
                    st.success(f"✅ Updated {updated} underlying positions!")
                    
                    if errors > 0:
                        st.warning(f"⚠️ Failed to update {errors} tickers:")
                        with st.expander("View Failed Tickers & ISINs"):
                            for failure in failed:
                                st.error(f"❌ {failure}")
                    
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"❌ Error: {str(e)}")
        
        with col3:
            # Export to CSV
            csv_data = export_to_csv(prepare_notes_for_export(all_notes))
            st.download_button(
                label="📄 Export CSV",
                data=csv_data,
                file_name=get_export_filename("csv"),
                mime="text/csv",
                use_container_width=True
            )
        
        st.markdown("---")
        
        # Count notes by status
        status_counts = df_all['current_status'].value_counts().to_dict()
        
        # Create tabs for each status category
        tab_alive, tab_not_obs, tab_ko, tab_ki, tab_converted, tab_ended = st.tabs([
            f"🟢 Alive ({status_counts.get('Alive', 0)})",
            f"⏳ Not Observed Yet ({status_counts.get('Not Observed Yet', 0)})",
            f"🔴 Knocked Out ({status_counts.get('Knocked Out', 0)})",
            f"🟠 Knocked In ({status_counts.get('Knocked In', 0)})",
            f"🔄 Converted ({status_counts.get('Converted', 0)})",
            f"⚫ Ended ({status_counts.get('Ended', 0)})"
        ])
        
        # Function to render notes for a specific status
        def render_status_tab(status_filter, tab_container):
            with tab_container:
                # Filter notes by status
                filtered_notes = [note for note in all_notes if note['current_status'] == status_filter]
                
                if not filtered_notes:
                    st.info(f"No notes with status: {status_filter}")
                    return
                
                df_notes = pd.DataFrame(filtered_notes)
                
                # Additional filters within tab
                col1, col2 = st.columns(2)
                with col1:
                    customers = ["All Clients"] + sorted(df_notes['customer_name'].unique().tolist())
                    selected_customer = st.selectbox(f"Filter by Customer", customers, key=f"customer_{status_filter}")
                with col2:
                    products = ["All"] + sorted(df_notes['type_of_structured_product'].unique().tolist())
                    selected_product = st.selectbox(f"Filter by Product", products, key=f"product_{status_filter}")
                
                # Apply additional filters
                if selected_customer != "All Clients":
                    df_notes = df_notes[df_notes['customer_name'] == selected_customer]
                if selected_product != "All":
                    df_notes = df_notes[df_notes['type_of_structured_product'] == selected_product]
                
                st.write(f"**Showing {len(df_notes)} notes**")
                
                # Calculate coupon columns
                expected_coupons = []
                accumulated_coupons = []
                payments_progress = []
                
                for _, row in df_notes.iterrows():
                    expected = calculate_expected_coupon(
                        row['notional_amount'],
                        row['coupon_per_annum'],
                        row['coupon_payment_dates']
                    )
                    expected_coupons.append(expected)
                    
                    accumulated, paid, total = calculate_accumulated_coupon(
                        row['notional_amount'],
                        row['coupon_per_annum'],
                        row['coupon_payment_dates']
                    )
                    accumulated_coupons.append(accumulated)
                    payments_progress.append(f"{paid}/{total}" if total > 0 else "0/0")
                
                df_notes['expected_coupon'] = expected_coupons
                df_notes['accumulated_coupon'] = accumulated_coupons
                df_notes['payments_progress'] = payments_progress
                
                # Display table
                display_df = df_notes[[
                    'customer_name', 'custodian_bank', 'type_of_structured_product', 
                    'notional_amount', 'isin', 'coupon_per_annum',
                    'expected_coupon', 'accumulated_coupon', 'payments_progress',
                    'trade_date', 'final_valuation_date'
                ]].copy()
                
                # Format columns
                display_df['coupon_per_annum'] = display_df['coupon_per_annum'].apply(
                    lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A"
                )
                display_df['notional_amount'] = display_df['notional_amount'].apply(
                    lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A"
                )
                display_df['expected_coupon'] = display_df['expected_coupon'].apply(
                    lambda x: f"${x:,.2f}" if pd.notna(x) and x > 0 else "$0.00"
                )
                display_df['accumulated_coupon'] = display_df['accumulated_coupon'].apply(
                    lambda x: f"${x:,.2f}" if pd.notna(x) and x > 0 else "$0.00"
                )
                
                # Rename columns
                display_df.columns = [
                    'Customer', 'Custodian Bank', 'Product Type', 'Notional', 'ISIN',
                    'Coupon p.a.', 'Expected Coupon', 'Accumulated Coupon', 'Payments',
                    'Trade Date', 'Maturity'
                ]
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # ISIN Search and Details
                st.markdown("---")
                st.subheader("🔍 Search & View Details")
                
                search_isin = st.text_input(f"Search by ISIN", 
                                           placeholder="Enter ISIN",
                                           key=f"search_{status_filter}")
                
                if search_isin:
                    search_isin = search_isin.strip().upper()
                    matching = df_notes[df_notes['isin'].str.upper() == search_isin]
                    
                    if len(matching) > 0:
                        selected_note_id = int(matching.iloc[0]['id'])
                        st.success(f"✅ Found: {matching.iloc[0]['customer_name']}")
                        
                        note_details = db.get_note_with_underlyings(selected_note_id)
                        
                        with st.expander("📄 Note Details", expanded=True):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**Customer:** {note_details['customer_name']}")
                                st.write(f"**Custodian Bank:** {note_details['custodian_bank'] or 'N/A'}")
                                st.write(f"**Product Type:** {note_details['type_of_structured_product']}")
                                st.write(f"**Notional:** ${note_details['notional_amount']:,.0f}")
                                st.write(f"**Coupon:** {note_details['coupon_per_annum']*100:.2f}%")
                            
                            with col2:
                                st.write(f"**ISIN:** {note_details['isin'] or 'N/A'}")
                                st.write(f"**Trade Date:** {note_details['trade_date']}")
                                st.write(f"**Maturity:** {note_details['final_valuation_date']}")
                                
                                # Status with color
                                status = note_details['current_status']
                                if status == 'Alive':
                                    st.success(f"**Status:** {status}")
                                elif status == 'Not Observed Yet':
                                    st.info(f"**Status:** {status}")
                                elif status == 'Knocked Out':
                                    st.error(f"**Status:** {status}")
                                elif status == 'Knocked In':
                                    st.warning(f"**Status:** {status}")
                                elif status == 'Ended':
                                    st.info(f"**Status:** {status}")
                            
                            st.write("**Underlyings:**")
                            for u in note_details['underlyings']:
                                st.write(f"**{u['underlying_sequence']}. {u['underlying_name']}** ({u['underlying_ticker']})")
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.write(f"Spot: ${u['spot_price']:,.2f}" if u['spot_price'] else "Spot: N/A")
                                    st.write(f"Strike: ${u['strike_price']:,.2f}" if u['strike_price'] else "Strike: N/A")
                                with col2:
                                    st.write(f"KO: ${u['ko_price']:,.2f}" if u['ko_price'] else "KO: N/A")
                                    st.write(f"KI: ${u['ki_price']:,.2f}" if u['ki_price'] else "KI: N/A")
                                with col3:
                                    st.write(f"Last Close: ${u['last_close_price']:,.2f}" if u['last_close_price'] else "Last Close: N/A")
                                    # Convert timestamp to Singapore time
                                    if u['last_price_update']:
                                        try:
                                            if isinstance(u['last_price_update'], str):
                                                utc_time = datetime.strptime(u['last_price_update'], '%Y-%m-%d %H:%M:%S')
                                            else:
                                                utc_time = u['last_price_update']
                                            
                                            utc_tz = pytz.UTC
                                            sg_tz = pytz.timezone('Asia/Singapore')
                                            
                                            if utc_time.tzinfo is None:
                                                utc_time = utc_tz.localize(utc_time)
                                            
                                            sg_time = utc_time.astimezone(sg_tz)
                                            st.write(f"Updated: {sg_time.strftime('%Y-%m-%d %H:%M:%S')} SGT")
                                        except:
                                            st.write(f"Updated: {u['last_price_update']}")
                                    else:
                                        st.write("Updated: Never")
                                st.markdown("---")
                    else:
                        st.error(f"❌ ISIN '{search_isin}' not found in {status_filter} notes")
        
        # Render each tab
        render_status_tab('Alive', tab_alive)
        render_status_tab('Not Observed Yet', tab_not_obs)
        render_status_tab('Knocked Out', tab_ko)
        render_status_tab('Knocked In', tab_ki)
        render_status_tab('Converted', tab_converted)
        render_status_tab('Ended', tab_ended)
    else:
        st.info("No notes in database yet.")

# ============================================================================
# PAGE 6: EDIT NOTE
# ============================================================================
elif page == "Edit Note":
    st.title("✏️ Edit Structured Note")
    
    # Get all notes
    all_notes = db.get_all_notes()
    
    if all_notes:
        df_notes = pd.DataFrame(all_notes)
        
        # Select note to edit
        selected_note_id = st.selectbox(
            "Select note to edit",
            df_notes['id'].tolist(),
            format_func=lambda x: f"ID {x}: {df_notes[df_notes['id']==x]['customer_name'].values[0]} - {df_notes[df_notes['id']==x]['isin'].values[0] or 'No ISIN'} ({df_notes[df_notes['id']==x]['type_of_structured_product'].values[0]})"
        )
        
        if selected_note_id:
            # Get note details
            note = db.get_note_with_underlyings(selected_note_id)
            
            # Pre-populate form with existing data
            with st.form("edit_note_form"):
                st.info(f"Editing Note ID: {selected_note_id}")
                
                # CLIENT INFORMATION
                st.subheader("👤 Client Information")
                col1, col2 = st.columns(2)
                
                with col1:
                    customer_name = st.text_input("Customer Name *", value=note['customer_name'])
                with col2:
                    custodian_bank = st.text_input("Custodian Bank", value=note['custodian_bank'] or "")
                
                st.markdown("---")
                
                # PRODUCT DETAILS
                st.subheader("📄 Product Details")
                col1, col2 = st.columns(2)
                
                with col1:
                    product_types = ["FCN", "WOFCN", "Phoenix", "BEN", "ACCU", "DECU", "DCN", "WOBEN", "TWINWIN"]
                    current_product_idx = product_types.index(note['type_of_structured_product']) if note['type_of_structured_product'] in product_types else 0
                    product_type = st.selectbox("Type of Structured Product *", product_types, index=current_product_idx)
                with col2:
                    isin = st.text_input("ISIN", value=note['isin'] or "")
                
                col1, col2 = st.columns(2)
                with col1:
                    notional_amount = st.number_input("Notional Amount *", min_value=0.0, step=1000.0, 
                                                     value=float(note['notional_amount']) if note['notional_amount'] else 0.0)
                with col2:
                    currency = st.selectbox("Currency", ["USD", "EUR", "SGD", "HKD", "CHF", "GBP"])
                
                st.markdown("---")
                
                # DATES
                st.subheader("📅 Important Dates")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    # Handle date conversion - could be string or date object
                    if isinstance(note['trade_date'], str):
                        trade_val = datetime.strptime(note['trade_date'], '%Y-%m-%d').date()
                    else:
                        trade_val = note['trade_date'] if note['trade_date'] else date.today()
                    trade_date = st.date_input("Trade Date *", value=trade_val)
                    
                with col2:
                    if isinstance(note['issue_date'], str):
                        issue_val = datetime.strptime(note['issue_date'], '%Y-%m-%d').date()
                    else:
                        issue_val = note['issue_date'] if note['issue_date'] else date.today()
                    issue_date = st.date_input("Issue Date *", value=issue_val)
                    
                with col3:
                    if isinstance(note['observation_start_date'], str):
                        obs_val = datetime.strptime(note['observation_start_date'], '%Y-%m-%d').date()
                    else:
                        obs_val = note['observation_start_date'] if note['observation_start_date'] else date.today()
                    obs_start = st.date_input("Observation Start *", value=obs_val)
                    
                with col4:
                    if isinstance(note['final_valuation_date'], str):
                        final_val = datetime.strptime(note['final_valuation_date'], '%Y-%m-%d').date()
                    else:
                        final_val = note['final_valuation_date'] if note['final_valuation_date'] else date.today()
                    final_val_date = st.date_input("Final Valuation Date *", value=final_val)
                
                st.markdown("---")
                
                # COUPON INFORMATION
                st.subheader("💰 Coupon Information")
                col1, col2 = st.columns(2)
                
                with col1:
                    coupon_per_annum = st.number_input("Coupon per Annum (%) *", min_value=0.0, max_value=100.0, 
                                                       step=0.01, value=float(note['coupon_per_annum']*100) if note['coupon_per_annum'] else 0.0)
                with col2:
                    if product_type == "Phoenix":
                        coupon_barrier = st.number_input("Coupon Barrier", min_value=0.0, step=0.01, 
                                                         value=float(note['coupon_barrier']) if note['coupon_barrier'] else 0.0)
                    else:
                        coupon_barrier = None
                
                coupon_payment_dates_input = st.text_input("Coupon Payment Dates (comma-separated)", 
                                                          value=note['coupon_payment_dates'] or "")
                
                st.markdown("---")
                
                # BARRIER RULES
                st.subheader("🎯 Barrier Monitoring Rules")
                col1, col2 = st.columns(2)
                
                with col1:
                    ko_types = ["Daily", "Period-End"]
                    ko_type_idx = ko_types.index(note['ko_type']) if note['ko_type'] in ko_types else 0
                    ko_type = st.selectbox("KO Type", ko_types, index=ko_type_idx)
                    
                    if ko_type == "Period-End":
                        ko_obs_freq = st.selectbox("KO Observation Frequency", 
                                                   ["Daily", "Weekly", "Monthly", "Quarterly", "Semi-Annually"])
                    else:
                        ko_obs_freq = "Daily"
                
                with col2:
                    ki_types = ["Daily", "EKI"]
                    ki_type_idx = ki_types.index(note['ki_type']) if note['ki_type'] in ki_types else 0
                    ki_type = st.selectbox("KI Type", ki_types, index=ki_type_idx)
                
                st.markdown("---")
                
                # UNDERLYING ASSETS
                st.subheader("📈 Underlying Assets")
                st.info("💡 Update underlyings as needed. Leave blank to remove.")
                
                # Get existing underlyings
                existing_underlyings = {u['underlying_sequence']: u for u in note['underlyings']}
                
                underlyings = []
                
                for i in range(4):
                    existing_u = existing_underlyings.get(i+1, {})
                    
                    with st.expander(f"Underlying {i+1}", expanded=(i==0)):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            u_ticker = st.text_input(f"Ticker {i+1}" + (" *" if i == 0 else ""), 
                                                    value=existing_u.get('underlying_ticker', ''),
                                                    placeholder="e.g., TSLA",
                                                    key=f"edit_u_ticker_{i}")
                            u_spot = st.number_input(f"Spot Price {i+1}" + (" *" if i == 0 else ""), 
                                                    min_value=0.0, step=0.01, format="%.4f",
                                                    value=float(existing_u.get('spot_price', 0.0)) if existing_u.get('spot_price') else 0.0,
                                                    key=f"edit_u_spot_{i}")
                            u_strike = st.number_input(f"Strike Price {i+1}" + (" *" if i == 0 else ""), 
                                                      min_value=0.0, step=0.01, format="%.4f",
                                                      value=float(existing_u.get('strike_price', 0.0)) if existing_u.get('strike_price') else 0.0,
                                                      key=f"edit_u_strike_{i}")
                        
                        with col2:
                            u_ko = st.number_input(f"KO Price {i+1}", min_value=0.0, step=0.01, format="%.4f",
                                                  value=float(existing_u.get('ko_price', 0.0)) if existing_u.get('ko_price') else 0.0,
                                                  key=f"edit_u_ko_{i}")
                            u_ki = st.number_input(f"KI Price {i+1}", min_value=0.0, step=0.01, format="%.4f",
                                                  value=float(existing_u.get('ki_price', 0.0)) if existing_u.get('ki_price') else 0.0,
                                                  key=f"edit_u_ki_{i}")
                        
                        # Only add if ticker is filled
                        if u_ticker and u_ticker.strip():
                            underlyings.append({
                                'sequence': i + 1,
                                'underlying_name': u_ticker.strip(),
                                'underlying_ticker': u_ticker.strip(),
                                'spot_price': u_spot if u_spot > 0 else None,
                                'strike_price': u_strike if u_strike > 0 else None,
                                'ko_price': u_ko if u_ko > 0 else None,
                                'ki_price': u_ki if u_ki > 0 else None,
                                'last_close_price': existing_u.get('last_close_price')  # Preserve existing price
                            })
                
                # Submit button
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("💾 Update Note", use_container_width=True, type="primary")
                with col2:
                    cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
                
                if cancel:
                    st.info("Edit cancelled")
                    st.rerun()
                
                if submitted:
                    # Validation
                    if not customer_name or not product_type:
                        st.error("❌ Please fill in all required fields (*)")
                    elif notional_amount <= 0:
                        st.error("❌ Notional Amount must be greater than 0")
                    elif len(underlyings) == 0:
                        st.error("❌ Please fill in at least one underlying")
                    else:
                        try:
                            # Prepare note data
                            updated_note_data = {
                                'customer_name': customer_name.strip(),
                                'custodian_bank': custodian_bank.strip() if custodian_bank else None,
                                'type_of_structured_product': product_type,
                                'notional_amount': notional_amount,
                                'isin': isin.strip() if isin else None,
                                'trade_date': str(trade_date),
                                'issue_date': str(issue_date),
                                'observation_start_date': str(obs_start),
                                'final_valuation_date': str(final_val_date),
                                'coupon_payment_dates': coupon_payment_dates_input.strip() if coupon_payment_dates_input else None,
                                'coupon_per_annum': coupon_per_annum / 100.0,
                                'coupon_barrier': coupon_barrier if product_type == "Phoenix" else None,
                                'ko_type': ko_type,
                                'ko_observation_frequency': ko_obs_freq if ko_type == "Period-End" else None,
                                'ki_type': ki_type
                            }
                            
                            # Update in database
                            if db.update_structured_note(selected_note_id, updated_note_data, underlyings):
                                st.success(f"✅ Note ID {selected_note_id} updated successfully!")
                                st.balloons()
                            else:
                                st.error("❌ Failed to update note")
                        except Exception as e:
                            st.error(f"❌ Error updating note: {str(e)}")
                            st.exception(e)
    else:
        st.info("No notes in database to edit.")

# ============================================================================
# PAGE 7: SETTINGS
# ============================================================================
elif page == "Settings":
    st.title("⚙️ Settings")
    
    # System Information
    st.subheader("📊 System Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Database Type:** {db.db_type.upper()}")
        if db.db_type == 'sqlite':
            st.write(f"**Location:** `{db.db_path}`")
        else:
            st.write(f"**Location:** Cloud PostgreSQL")
    
    with col2:
        all_notes = db.get_all_notes()
        st.metric("Total Records", len(all_notes))
        
        if all_notes:
            df = pd.DataFrame(all_notes)
            total_notional = df['notional_amount'].sum()
            st.metric("Total Notional", f"${total_notional:,.0f}")
    
    st.markdown("---")
    
    # Export Options
    st.subheader("📥 Data Export")
    st.write("Export all data with detailed underlying information")
    
    if all_notes:
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            # Detailed export with underlyings
            detailed_df = export_notes_with_underlyings(db, all_notes)
            detailed_csv = export_to_csv(detailed_df)
            st.download_button(
                label="📄 Detailed CSV",
                data=detailed_csv,
                file_name=get_export_filename("csv"),
                mime="text/csv",
                use_container_width=True,
                help="Export with all underlying details"
            )
        
        with col2:
            detailed_excel = export_to_excel(detailed_df, sheet_name="Notes with Underlyings")
            st.download_button(
                label="📊 Detailed Excel",
                data=detailed_excel,
                file_name=get_export_filename("xlsx"),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                help="Export with all underlying details"
            )
    else:
        st.info("No data to export")
    
    st.markdown("---")
    
    # Application Information
    st.subheader("ℹ️ About")
    st.write("""
    **Structured Notes Tracking System**
    
    Version: 2.0 (Production Ready)
    
    Features:
    - ✅ Cloud database support (PostgreSQL + SQLite)
    - ✅ Real-time price updates from Yahoo Finance
    - ✅ Automated KO/KI status tracking
    - ✅ Coupon calculations
    - ✅ Data export (CSV/Excel)
    - ✅ Password protection
    - ✅ Mobile-responsive design
    
    For support or feature requests, contact your administrator.
    """)

# Footer
st.markdown("---")
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    st.markdown("📱 **Structured Notes Tracking System** | Built with Streamlit")
with col2:
    st.markdown("**Created by:** Benjamin Yong | **Version:** 1.0 | **November 2025**")

