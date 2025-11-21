# 📊 Structured Notes Tracking System

A professional web-based application for tracking and managing structured financial notes with real-time price updates, automated status calculations, and comprehensive reporting.

## ✨ Features

### Core Functionality
- 📝 **Complete Note Management**: Add, edit, view, and delete structured notes
- 📈 **Multi-Underlying Support**: Track up to 4 underlying assets per note
- 💰 **Automated Calculations**: 
  - Expected and accumulated coupon calculations
  - Automatic KO/KI status monitoring
  - Payment date tracking
- 💹 **Real-Time Pricing**: Integration with Yahoo Finance for live price updates
- 📊 **Visual Dashboards**: Interactive charts and metrics
- 📥 **Data Export**: Export to CSV and Excel formats
- 🔐 **Security**: Optional password protection
- 📱 **Mobile Responsive**: Works seamlessly on all devices

### Product Types Supported
- FCN (Fixed Coupon Notes)
- WOFCN (Worst Of Fixed Coupon Notes)
- ACCU (Accumulator)
- DECU (Decumulator)
- Phoenix Notes
- DCN (Digital Coupon Notes)
- WOBEN (Worst Of Bonus Enhanced Notes)
- TWINWIN

### Technical Features
- 🗄️ **Dual Database Support**: SQLite (local) and PostgreSQL (cloud)
- ☁️ **Cloud-Ready**: Deploy to Streamlit Cloud, Railway, or Render
- 🔄 **Auto Status Updates**: Daily/Period-End KO and Daily/EKI monitoring
- 📊 **Professional UI**: Modern, clean interface with custom styling
- 🚀 **Production Ready**: Environment config, authentication, error handling

## 🚀 Quick Start

### Local Development

1. **Clone/Download the project**
   ```bash
   cd "Client portfolio"
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app_new.py
   ```

4. **Open in browser**
   - Automatically opens at `http://localhost:8501`

### Cloud Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions to:
- ✅ Streamlit Cloud (Recommended - Free tier available)
- ✅ Railway (Includes database)
- ✅ Render (Free tier available)
- ✅ Custom VPS with Docker

## 📁 Project Structure

```
Client portfolio/
├── app_new.py                    # Main Streamlit application
├── database.py                   # Database operations (SQLite + PostgreSQL)
├── auth.py                       # Authentication module
├── export_utils.py               # Data export functionality
├── fetch_prices_new.py          # Yahoo Finance integration
├── status_calculator.py          # KO/KI status calculations
├── coupon_calculator.py          # Coupon calculations
├── payment_date_generator.py    # Payment date utilities
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
├── .gitignore                    # Git ignore rules
├── .streamlit/
│   └── config.toml              # Streamlit configuration
├── database_schema.sql          # Database schema documentation
├── KO_KI_RULES.md              # Business logic documentation
├── DEPLOYMENT.md                # Deployment guide
└── README.md                    # This file
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
# Database (leave empty for SQLite)
DATABASE_URL=postgresql://user:password@host:port/database

# Optional password protection
APP_PASSWORD=your_secure_password

# Optional customization
APP_TITLE=Structured Notes Tracker
PRICE_UPDATE_DELAY=0.2
```

### Database Setup

**Local (SQLite):**
- Automatic - no setup needed
- Database file: `structured_notes_new.db`

**Cloud (PostgreSQL):**
- Set `DATABASE_URL` environment variable
- Tables auto-created on first run
- See [DEPLOYMENT.md](DEPLOYMENT.md) for setup

## 📖 User Guide

### Adding a New Note

1. Navigate to **"Add New Note"**
2. Fill in:
   - **Client Information**: Customer name, custodian bank
   - **Product Details**: Type, notional amount, ISIN
   - **Dates**: Trade, issue, observation start, final valuation
   - **Coupon Info**: Rate, payment dates, coupon barrier (Phoenix only)
   - **Barrier Rules**: KO/KI types and observation frequencies
   - **Underlyings**: Ticker, prices, barriers (up to 4)
3. Click **"Save Structured Note"**

### Viewing Notes

1. Navigate to **"View Notes"**
2. Filter by customer or product type
3. View summary table with key metrics
4. Click note for detailed view
5. Export data using CSV or Excel buttons

### Updating Prices

1. Navigate to **"Update Prices"**
2. Click **"Update All Prices"**
3. System fetches latest prices from Yahoo Finance
4. Status automatically recalculated

### Understanding KO/KI Rules

See [KO_KI_RULES.md](KO_KI_RULES.md) for detailed business logic:

**Knock-Out (KO):**
- Triggers when **ALL** underlyings exceed their KO prices
- Can be Daily or Period-End monitoring

**Knock-In (KI):**
- Triggers when **ANY ONE** underlying hits or falls below KI price
- Can be Daily or EKI (European - final date only)

## 🛠️ Technology Stack

- **Framework**: Streamlit 1.29+
- **Database**: SQLite / PostgreSQL
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly
- **Financial Data**: yfinance (Yahoo Finance)
- **Export**: openpyxl (Excel)
- **Authentication**: Custom + streamlit-authenticator

## 📊 Database Schema

### Tables

**structured_notes**
- Core note information
- Dates, coupon details, barrier rules
- Auto-calculated status fields

**note_underlyings**
- Underlying asset details
- Prices, barriers, last updates
- Foreign key to structured_notes

See [database_schema.sql](database_schema.sql) for complete schema.

## 🔒 Security

- Password protection via `APP_PASSWORD`
- PostgreSQL connection encryption
- Session-based authentication
- Private GitHub repository recommended
- `.env` excluded from version control

## 🐛 Known Limitations

- Yahoo Finance may rate-limit requests (adjust `PRICE_UPDATE_DELAY`)
- Free hosting tiers have resource limits
- SQLite not recommended for concurrent users
- Historical price data not stored (only latest)

## 🔄 Updating the Application

1. **Pull latest changes**
   ```bash
   git pull origin main
   ```

2. **Update dependencies**
   ```bash
   pip install -r requirements.txt --upgrade
   ```

3. **Restart application**
   - Cloud: Auto-deploys on push (Streamlit Cloud)
   - Local: Restart streamlit

## 📈 Roadmap / Future Enhancements

- [ ] Historical price tracking and charts
- [ ] Email notifications for KO/KI events
- [ ] Bulk note import (CSV/Excel)
- [ ] Advanced analytics and reporting
- [ ] Multi-currency support with FX rates
- [ ] API endpoints for integrations
- [ ] Mobile app (React Native)
- [ ] Role-based access control

## 🤝 Contributing

This is a private project for client use. For feature requests or bug reports, contact the administrator.

## 📄 License

Proprietary - All rights reserved

## 🆘 Support

For issues or questions:

1. Check [DEPLOYMENT.md](DEPLOYMENT.md) troubleshooting section
2. Review [KO_KI_RULES.md](KO_KI_RULES.md) for business logic
3. Contact your system administrator

## 🎯 Credits

Built with ❤️ using:
- [Streamlit](https://streamlit.io)
- [Supabase](https://supabase.com)
- [Yahoo Finance API](https://github.com/ranaroussi/yfinance)

---

**Version**: 2.0 (Production Ready)  
**Last Updated**: November 2025  
**Status**: ✅ Active Development


