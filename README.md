# 💱 USD Exchange Rate Pipeline

A complete data pipeline for fetching, processing, and visualizing USD exchange rates using Apache Airflow and Streamlit.

## 🚀 Quick Start

### Start the Pipeline

```bash
docker-compose up -d
```

That's it! The access information will be displayed automatically in your terminal.

### Access URLs

#### 🔧 Airflow Web UI
- **URL:** http://localhost:8080
- **Username:** `admin`
- **Password:** `admin123`

#### 💱 Streamlit Dashboard  
- **URL:** http://localhost:8501
- **Username:** `streamlit_user`
- **Password:** `streamlit123`

## 📋 How to Use

### Step 1: Run Your DAG
1. Open Airflow UI at http://localhost:8080
2. Login with credentials above
3. Find your exchange rate DAG
4. Click the "Play" button to unpause it
5. Click "Trigger DAG" to run it

### Step 2: View Exchange Rates
1. Wait for the DAG to complete (check status in Airflow)
2. Open Streamlit Dashboard at http://localhost:8501
3. Login with credentials above
4. Explore the exchange rate visualizations!

## 📊 Dashboard Features

### 1. Exchange Rates Page
- **Current Rates:** View latest USD exchange rates with country flags 🇺🇸🇪🇺🇬🇧
- **Historical Trend:** Analyze rate changes over time
- **Rate Comparison:** Compare multiple currencies side-by-side
- **Currency Symbols:** See rates with native currency symbols (€, £, ¥, etc.)

### 2. DAG Run Logs
- View all DAG execution history
- Filter by status, DAG ID, or run type
- See success/failure statistics
- Monitor task-level details

## 🗂️ Project Structure

```
.
├── docker-compose.yaml       # Service orchestration
├── dags/                     # Airflow DAG definitions
├── etl/                      # ETL scripts
├── sql/                      # SQL scripts
├── streamlit_app/
│   ├── app.py               # Streamlit dashboard
│   └── requirements.txt     # Python dependencies
└── scripts/
    └── display_links.sh     # Display access information
```

## 🔧 Customization

### Change Credentials

Edit `docker-compose.yaml`:

```yaml
# Airflow credentials (in airflow-init service)
ADMIN_USERNAME: your_username
ADMIN_PASSWORD: your_password

# Streamlit credentials (in streamlit service)
STREAMLIT_USERNAME: your_username
STREAMLIT_PASSWORD: your_password
```

### Add More Currencies

The dashboard automatically detects currencies in your database. The following currencies are pre-configured with flags and symbols:

EUR 🇪🇺, GBP 🇬🇧, JPY 🇯🇵, AUD 🇦🇺, CAD 🇨🇦, CHF 🇨🇭, CNY 🇨🇳, INR 🇮🇳, MXN 🇲🇽, BRL 🇧🇷, and more!

To add more, edit `CURRENCY_INFO` dictionary in `streamlit_app/app.py`.

## 🛠️ Useful Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f airflow-scheduler
docker-compose logs -f streamlit
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart streamlit
```

### Stop Everything
```bash
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### Check Service Status
```bash
docker-compose ps
```

## 🗄️ Database Access

**PostgreSQL Connection:**
- Host: `localhost`
- Port: `5433`
- Database: `exchange_db`
- Username: `exchanger`
- Password: `exchanger`

Connect with psql:
```bash
psql -h localhost -p 5433 -U exchanger -d exchange_db
```

## 🐛 Troubleshooting

### Services Keep Restarting
```bash
docker-compose down -v
docker-compose up -d
docker-compose logs -f
```

### Streamlit Waiting for DAG
The Streamlit service waits for at least one successful DAG run. Make sure to:
1. Trigger your DAG from Airflow UI
2. Wait for it to complete successfully
3. Streamlit will automatically start showing data

### Port Already in Use
Change the port mappings in `docker-compose.yaml`:
```yaml
ports:
  - "8081:8080"  # Change 8080 to 8081 for Airflow
  - "8502:8501"  # Change 8501 to 8502 for Streamlit
```

### Cannot Connect to Database
Make sure PostgreSQL container is healthy:
```bash
docker-compose ps
docker-compose logs exchange-postgres
```

## 📈 Performance Tips

1. **Limit Historical Data:** The dashboard limits queries to 1000 rows for performance
2. **Filter Currencies:** Select only the currencies you need to compare
3. **Regular Cleanup:** Periodically clean old DAG runs from Airflow UI

## 🔐 Security Notes

⚠️ **Important:** The default credentials are for development only!

For production:
1. Change all default passwords
2. Use environment variables or secrets management
3. Enable HTTPS
4. Restrict network access
5. Use strong SECRET_KEY values

## 📝 License

This project is provided as-is for educational and development purposes.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

---

**Happy Exchange Rate Tracking! 💱📊**