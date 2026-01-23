📦 Warehouse Management System
A full-stack Warehouse Management System (WMS) built using Python, MySQL, and Streamlit, designed to manage inventory, orders, customers, and payments efficiently with a clean database-driven architecture.
___

🚀 Features
🔐 User Authentication & Authorization
🏢 Organization & User Hierarchy Management
📦 Product Inventory Management
🛒 Order Processing System
💳 Payment Tracking
📊 CSV-based bulk data loading
🗄️ MySQL Database Integration
🖥️ Streamlit Web Interface
⚙️ Modular CRUD Operations
___

🛠️ Tech Stack
Backend: Python
Frontend: Streamlit
Database: MySQL
ORM / DB Connector: SQLAlchemy / mysql-connector
Data Handling: Pandas
Environment: Virtualenv
___

📂 Project Structure
```bash
warehouse_management_system/
│
├── app.py                 # Main Streamlit application
├── auth.py                # Authentication logic
├── db.py                  # Database connection layer
├── create_tables.py       # DB schema creation
├── crud_functions.py      # CRUD operations
├── requirements.txt       # Dependencies
├── .gitignore
│
└── data/
    ├── Customers.csv
    ├── Orders.csv
    ├── OrderItems.csv
    ├── Payments.csv
    └── Products.csv
```
___

⚙️ Setup Instructions
1️⃣ Clone the Repository
```bash
git clone https://github.com/gauravxsarkar/Warehouse-Management-System.git
cd Warehouse-Management-System
```
2️⃣ Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```
3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```
4️⃣ Configure Database
```bash
Edit db.py and update:
HOST = "localhost"
USER = "root"
PASSWORD = "your_password"
DATABASE = "warehouse_db"
```
Create database:
```bash
CREATE DATABASE warehouse_db;
```
5️⃣ Create Tables
```bash
python create_tables.py
```
6️⃣ Run the Application
```bash
streamlit run app.py
```
___

🗃️ Database Schema
Entities:
Users
Organizations
Directory Levels
Customers
Products
Orders
Order Items
Payments
Supports:
Hierarchical organization structure
Relational integrity using foreign keys
___

📊 Sample Data
CSV datasets provided:
Customers.csv
Products.csv
Orders.csv
OrderItems.csv
Payments.csv
Used for:
Bulk ingestion
Testing workflows
Analytics & reporting
___

🔐 Security Features
Environment-based DB credentials
Password hashing (optional upgrade)
Role-based permissions (admin / staff)
___

👨‍💻 Author
Gaurav Sarkar
GitHub: https://github.com/gauravxsarkar