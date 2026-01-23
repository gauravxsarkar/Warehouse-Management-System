from sqlalchemy import text
from db import engine

# er model
# https://dbdiagram.io/d/695ac7f539fa3db27b1180da

# Create all tables
with engine.begin() as conn:
    # Users table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(255) NOT NULL UNIQUE,
            role ENUM('admin', 'staff', 'manager') NOT NULL,
            email VARCHAR(255) NOT NULL,
            phone VARCHAR(20),
            date_joined DATE NOT NULL DEFAULT (CURRENT_DATE),
            password VARCHAR(255) NOT NULL
        )
    """))
    
    # Suppliers table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id INT PRIMARY KEY AUTO_INCREMENT,
            supplier_name VARCHAR(255) NOT NULL,
            supplier_phone VARCHAR(20),
            supplier_email VARCHAR(255),
            supplier_city VARCHAR(100)
        )
    """))
    
    # Products table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INT PRIMARY KEY AUTO_INCREMENT,
            product_name VARCHAR(255) NOT NULL,
            category VARCHAR(100),
            unit_price DECIMAL(10,2) NOT NULL,
            is_available BOOLEAN DEFAULT TRUE,
            reorder_level INT
        )
    """))
    
    # Warehouse table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS warehouse (
            warehouse_id INT PRIMARY KEY AUTO_INCREMENT,
            warehouse_city VARCHAR(100) NOT NULL,
            warehouse_total_capacity INT NOT NULL
        )
    """))
    
    # Orders table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INT PRIMARY KEY AUTO_INCREMENT,
            supplier_id INT,
            order_date DATE NOT NULL DEFAULT (CURRENT_DATE),
            order_status ENUM('pending', 'recieved', 'cancelled') NOT NULL DEFAULT 'pending',
            created_by INT,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) 
                ON UPDATE CASCADE ON DELETE SET NULL,
            FOREIGN KEY (created_by) REFERENCES users(user_id) 
                ON UPDATE CASCADE ON DELETE SET NULL
        )
    """))
    
    # Order Items table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS order_items (
            order_item_id INT PRIMARY KEY AUTO_INCREMENT,
            order_id INT NOT NULL,
            product_id INT NOT NULL,
            quantity_ordered INT NOT NULL,
            unit_price DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id) 
                ON UPDATE CASCADE ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(product_id) 
                ON UPDATE CASCADE ON DELETE CASCADE
        )
    """))
    
    # Payments table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INT PRIMARY KEY AUTO_INCREMENT,
            order_id INT NOT NULL,
            amount_paid DECIMAL(10,2) NOT NULL,
            payment_status ENUM('completed', 'pending', 'partial') NOT NULL,
            payment_date DATE NOT NULL DEFAULT (CURRENT_DATE),
            recorded_by INT,
            FOREIGN KEY (order_id) REFERENCES orders(order_id) 
                ON UPDATE CASCADE ON DELETE CASCADE,
            FOREIGN KEY (recorded_by) REFERENCES users(user_id) 
                ON UPDATE CASCADE ON DELETE SET NULL
        )
    """))
    
    # Inventory table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS inventory (
            inventory_id INT PRIMARY KEY AUTO_INCREMENT,
            product_id INT NOT NULL,
            warehouse_id INT NOT NULL,
            stock_left INT NOT NULL DEFAULT 0,
            last_restocked DATETIME DEFAULT CURRENT_TIMESTAMP
                      ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY product_warehouse_unique (product_id, warehouse_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id) 
                ON UPDATE CASCADE ON DELETE CASCADE,
            FOREIGN KEY (warehouse_id) REFERENCES warehouse(warehouse_id) 
                ON UPDATE CASCADE ON DELETE CASCADE
        )
    """))
    
    # Stock Movement table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS stock_movement (
            movement_id INT PRIMARY KEY AUTO_INCREMENT,
            product_id INT NOT NULL,
            warehouse_id INT NOT NULL,
            movement_type ENUM('in', 'out') NOT NULL,
            quantity INT NOT NULL,
            movement_date DATE NOT NULL DEFAULT (CURRENT_DATE),
            performed_by INT,
            FOREIGN KEY (product_id) REFERENCES products(product_id) 
                ON UPDATE CASCADE ON DELETE CASCADE,
            FOREIGN KEY (warehouse_id) REFERENCES warehouse(warehouse_id) 
                ON UPDATE CASCADE ON DELETE CASCADE,
            FOREIGN KEY (performed_by) REFERENCES users(user_id) 
                ON UPDATE CASCADE ON DELETE SET NULL
        )
    """))



