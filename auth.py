"""
Simple Authentication Module for Structured Notes Tracker
Supports password protection and optional multi-user auth
"""

import streamlit as st
import os
import hashlib
import hmac


def check_password() -> bool:
    """
    Simple password protection for the app.
    Returns True if password is correct or no password is set.
    """
    
    # Check if password is required
    app_password = os.getenv('APP_PASSWORD')
    
    # If no password is set, allow access
    if not app_password:
        return True
    
    # Check if already authenticated in this session
    if st.session_state.get('authenticated', False):
        return True
    
    # Show login form
    st.markdown("""
        <style>
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 40px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        st.title("🔐 Login")
        st.markdown("Please enter your password to access the Structured Notes Tracker")
        
        password_input = st.text_input("Password", type="password", key="password_input")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Login", type="primary", use_container_width=True):
                if verify_password(password_input, app_password):
                    st.session_state['authenticated'] = True
                    st.success("✅ Authentication successful!")
                    st.rerun()
                else:
                    st.error("❌ Incorrect password")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    return False


def verify_password(input_password: str, stored_password: str) -> bool:
    """
    Verify password using secure comparison.
    """
    return hmac.compare_digest(input_password, stored_password)


def logout():
    """
    Logout the current user
    """
    st.session_state['authenticated'] = False
    st.rerun()


def show_logout_button():
    """
    Display logout button in sidebar if authenticated
    """
    if os.getenv('APP_PASSWORD') and st.session_state.get('authenticated', False):
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            logout()


# Optional: Multi-user authentication using streamlit-authenticator
# Uncomment and configure if you need multiple users with different permissions

"""
import streamlit_authenticator as stauth

def setup_multi_user_auth():
    
    # Configuration for multiple users
    names = ['John Doe', 'Jane Smith']
    usernames = ['jdoe', 'jsmith']
    passwords = ['password123', 'password456']  # In production, use hashed passwords
    
    # Hash passwords
    hashed_passwords = stauth.Hasher(passwords).generate()
    
    # Create authenticator
    authenticator = stauth.Authenticate(
        names,
        usernames,
        hashed_passwords,
        'structured_notes_cookie',
        'random_signature_key',
        cookie_expiry_days=30
    )
    
    name, authentication_status, username = authenticator.login('Login', 'main')
    
    if authentication_status:
        authenticator.logout('Logout', 'sidebar')
        return True, username
    elif authentication_status == False:
        st.error('Username/password is incorrect')
        return False, None
    elif authentication_status == None:
        st.warning('Please enter your username and password')
        return False, None
"""




