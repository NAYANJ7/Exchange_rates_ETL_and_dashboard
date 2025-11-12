# 💱 USD Exchange Rate Pipeline

<div align="center">

![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-017CEE?style=for-the-badge&logo=Apache%20Airflow&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

**A complete data pipeline for fetching, processing, and visualizing USD exchange rates**

[Quick Start](#-quick-start) • [Features](#-dashboard-features) • [Screenshots](#-screenshots) • [Documentation](#-how-to-use)

<div align="center">

---

</div>

## 📸 Screenshots

<div align="center">

### 💹 Currency Converter Dashboard
![Currency Converter](Screenshots/currency-converter.png)

*Real-time currency conversion with favorites support*

### 📊 Exchange Rate Comparison
![Rate Comparison](Screenshots/rate-comparison.png)

*Visual comparison of multiple currencies side-by-side*

### 📋 DAG Run Logs
![DAG Logs](Screenshots/dag-logs.png)

*Monitor all pipeline executions and track success/failure*

### 🔄 Airflow Pipeline
![Airflow DAG](Screenshots/airflow-dag.png)

*Orchestrate ETL workflow with Apache Airflow*

</div>

---

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

---

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

---

## 📊 Dashboard Features

### 1. 💹 Currency Converter
- **Real-time Conversion:** Convert USD to any supported currency
- **Favorite Currencies:** Star your preferred currencies for quick access
- **Country Flags:** Visual representation with flags (🇺🇸🇪🇺🇬🇧🇯🇵)
- **Native Symbols:** Display rates with currency symbols (€, £, ¥, ₹)
- **Search Functionality:** Quickly find any currency

### 2. 📈 Exchange Rate Comparison
- **Multi-Currency View:** Compare multiple currencies simultaneously
- **Historical Trends:** Analyze rate changes over time
- **Interactive Charts:** Hover for detailed rate information
- **Visual Analytics:** Bar charts for easy comparison

### 3. 📋 DAG Run Logs
- **Execution History:** View all DAG runs with timestamps
- **Status Tracking:** Monitor success, failure, and running states
- **Filtering Options:** Filter by DAG ID, status, or run type
- **Performance Metrics:** Duration and execution details
- **Statistics Dashboard:** Quick overview of total/successful/failed runs

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  External API   │────▶│  Apache Airflow  │────▶│   PostgreSQL    │
│ (Exchange Data) │     │   (ETL Pipeline) │     │   (Data Store)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                           │
                                                           ▼
                                                  ┌─────────────────┐
                                                  │    Streamlit    │
                                                  │   (Dashboard)   │
                                                  └─────────────────┘
```

### Pipeline Components

1. **Fetch Task** - Retrieves latest exchange rates from API
2. **Transform Task** - Cleans and processes raw data
3. **Load Task** - Stores processed data in PostgreSQL
4. **Dashboard** - Visualizes data with interactive Streamlit UI

---

## 🗂️ Project Structure

```
.
├── docker-compose.yaml       # Service orchestration
├── dags/                     # Airflow DAG definitions
│   └── exchange_rates_dag.py
├── etl/                      # ETL scripts
│   ├── fetch.py
│   ├── transform.py
│   └── load.py
├── sql/                      # Database schema
│   └── init.sql
├── streamlit_app/
│   ├── app.py               # Main dashboard application
│   ├── pages/               # Multi-page app structure
│   └── requirements.txt     # Python dependencies
├── scripts/
│   └── display_links.sh     # Access information display
└── Screenshots/             # Application screenshots
```

---

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

**Supported Currencies:**
- 🇪🇺 EUR (Euro)
- 🇬🇧 GBP (British Pound)
- 🇯🇵 JPY (Japanese Yen)
- 🇦🇺 AUD (Australian Dollar)
- 🇨🇦 CAD (Canadian Dollar)
- 🇨🇭 CHF (Swiss Franc)
- 🇨🇳 CNY (Chinese Yuan)
- 🇮🇳 INR (Indian Rupee)
- 🇲🇽 MXN (Mexican Peso)
- 🇧🇷 BRL (Brazilian Real)
- And many more!

To add more currencies, edit the `CURRENCY_INFO` dictionary in `streamlit_app/app.py`.

---

## 🛠️ Useful Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f airflow-scheduler
docker-compose logs -f streamlit
docker-compose logs -f exchange-postgres
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart streamlit
docker-compose restart airflow-webserver
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

### Execute SQL Queries
```bash
# Access database shell
docker exec -it exchange-postgres psql -U exchanger -d exchange_db

# Run SQL file
docker exec -i exchange-postgres psql -U exchanger -d exchange_db < sql/query.sql
```

---

## 🗄️ Database Access

**PostgreSQL Connection Details:**
```
Host:     localhost
Port:     5433
Database: exchange_db
Username: exchanger
Password: exchanger
```

Connect with psql:
```bash
psql -h localhost -p 5433 -U exchanger -d exchange_db
```

Connect with Python:
```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5433,
    database="exchange_db",
    user="exchanger",
    password="exchanger"
)
```

---

## 🐛 Troubleshooting

### Services Keep Restarting
```bash
# Clean restart
docker-compose down -v
docker-compose up -d

# Check logs for errors
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
  - "5434:5432"  # Change 5433 to 5434 for PostgreSQL
```

### Cannot Connect to Database
Make sure PostgreSQL container is healthy:
```bash
docker-compose ps
docker-compose logs exchange-postgres

# Test connection
docker exec exchange-postgres pg_isready -U exchanger
```

### Airflow DAG Not Appearing
```bash
# Check DAG file for syntax errors
docker exec airflow-webserver airflow dags list

# Restart scheduler
docker-compose restart airflow-scheduler
```

---

## 📈 Performance Tips

1. **Limit Historical Data:** The dashboard limits queries to 1000 rows for performance
2. **Filter Currencies:** Select only the currencies you need to compare
3. **Regular Cleanup:** Periodically clean old DAG runs from Airflow UI
4. **Database Indexing:** Ensure proper indexes on frequently queried columns
5. **Cache Results:** Use Streamlit's `@st.cache_data` for expensive operations

---

## 🔐 Security Notes

⚠️ **Important:** The default credentials are for development only!

**For Production Deployment:**
1. ✅ Change all default passwords
2. ✅ Use environment variables or secrets management
3. ✅ Enable HTTPS with SSL certificates
4. ✅ Restrict network access with firewall rules
5. ✅ Use strong `SECRET_KEY` values
6. ✅ Implement rate limiting
7. ✅ Enable authentication and authorization
8. ✅ Regular security updates

---

## 🚦 Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum (8GB recommended)
- 10GB free disk space

---

## 📚 Tech Stack

| Technology | Purpose |
|------------|---------|
| **Apache Airflow** | Workflow orchestration and scheduling |
| **Streamlit** | Interactive dashboard and visualization |
| **PostgreSQL** | Relational database for storing rates |
| **Docker** | Containerization and deployment |
| **Python** | ETL scripts and application logic |

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. 🍴 Fork the repository
2. 🔧 Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. 💾 Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. 📤 Push to the branch (`git push origin feature/AmazingFeature`)
5. 🔃 Open a Pull Request

### Development Setup
```bash
# Clone repository
git clone https://github.com/yourusername/usd-exchange-pipeline.git
cd usd-exchange-pipeline

# Start development environment
docker-compose up -d

# View logs
docker-compose logs -f
```

---

## 📝 License

This project is provided as-is for educational and development purposes.

---

## 🙏 Acknowledgments

- Exchange rate data provided by [Your API Provider]
- Built with love using open-source technologies
- Inspired by real-world data engineering challenges

---

<div align="center">

**Happy Exchange Rate Tracking! 💱📊**

Made with ❤️ using Docker, Airflow, and Streamlit

[![GitHub Stars](https://img.shields.io/github/stars/yourusername/usd-exchange-pipeline?style=social)](https://github.com/yourusername/usd-exchange-pipeline)
[![GitHub Forks](https://img.shields.io/github/forks/yourusername/usd-exchange-pipeline?style=social)](https://github.com/yourusername/usd-exchange-pipeline)

</div>
