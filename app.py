import streamlit as st
import pandas as pd
from sqlalchemy import text
from werkzeug.security import generate_password_hash

from auth import authenticate
from db import engine
from crud_functions import (run_query, view, insert, update, delete, get_primarykey, get_col)

# session initialisation
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# login page
def login_page():
    st.title("Warehouse Management System")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = authenticate(username, password)

        if user:
            st.session_state.logged_in = True
            st.session_state.user = user
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid username or password")

# gatekeeper
if not st.session_state.logged_in:
    login_page()
    st.stop()

# sidebar and radio
user = st.session_state.user
role = user["role"]

st.sidebar.write(f"User: {user['username']}")
st.sidebar.write(f"Role: {role}")

pages = ["Inventory","Products","Warehouse","Suppliers"]

if role in ("admin","manager"):
    pages.append("Orders and Payments")
    # pages.append("Stock IN/Out")
if role == "admin":
    pages.append("Users")
    pages.append("Order Items")

page = st.sidebar.radio("Go To",pages)

st.sidebar.divider()

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

##################################################################

# INVENTORY PAGE
def inventory_page(role):
    st.header("Manage Inventory")

    product_name = st.text_input("Product Name")

    # get warehouse cities
    query = "SELECT warehouse_city FROM warehouse"
    rows = run_query(engine, query, fetch=True)
    warehouse_cities = [i[0] for i in rows]
    warehouse_city = st.selectbox(" Warehouse City", warehouse_cities)

    stock_left = st.number_input("Stock Left", min_value=0)

    product_id = None
    warehouse_id = None
    inventory_id = None

    if product_name:
        product_id = get_primarykey(engine, "products", "product_id", ["product_name"], [product_name])
    if warehouse_city:
        warehouse_id = get_primarykey(engine, "warehouse", "warehouse_id", ["warehouse_city"], [warehouse_city])
    if product_id and warehouse_city:
        inventory_id = get_primarykey(engine, "inventory", "inventory_id", ["product_id","warehouse_id"], [product_id, warehouse_id])

    data = {
    "product_id": product_id,
    "warehouse_id": warehouse_id,
    "stock_left": stock_left
    }

    col1, col2, col3 = st.columns(3)

    # search
    if col1.button("Search"):
        if not inventory_id:
            st.warning("no product found")
            return
        
        inventory = view(engine, "inventory", "inventory_id", inventory_id)
        st.dataframe([inventory])

    # add
    if col2.button("Add") and role in ("admin", "manager"):
# /
        if not product_id or not warehouse_id:
            st.warning("first add product/warehouse in the table")
            return
        
        if stock_left < 0:
            st.error("Stock cannot be negative")
            return

        # checkl warehouse capacity
        warehouse = view(engine, "warehouse", "warehouse_id", warehouse_id)
        if not warehouse:
            st.error("warehouse not found")
            return
        
        current_stock_query = """
                            SELECT COALESCE(SUM(stock_left),0)
                            FROM inventory
                            WHERE warehouse_id = :wid
        """
        current_total = run_query(engine, current_stock_query, {"wid": warehouse_id},fetch=True)[0][0]

        if current_total + stock_left > warehouse["warehouse_total_capacity"]:
            st.error(f"Warehouse capacity exceeded! Current: {current_total}, Capacity: {warehouse["warehouse_total_capacity"]}")
            return
# /
        try:
            insert(engine, "inventory", data)
            st.success("Inventory added")
        except Exception as e:
            st.error(f"Failed to add inventory: {str(e)}")

    # update
    if col3.button("Update") and role in ("admin", "manager"):
        if not inventory_id:
            st.warning("inventory record not found")
            return
        try:
            update(engine, "inventory", "inventory_id", inventory_id, data)
            st.success("Inventory Updated")
        except Exception as e:
            st.error("failed to update inventory. all fields are required.")
            st.exception(e)

    st.divider()
    st.subheader("View All Inventory")

    # Show all inventory
    query = """
        SELECT * FROM inventory
    """
    inventory = run_query(engine, query, fetch=True)
    if inventory:
        df = pd.DataFrame(inventory)
        st.dataframe(df)
    else:
        st.info("No inventory found")


# PRODUCTS PAGE
def products_page(role):
    st.header("Manage Products")

    product_name = st.text_input("Product_name")
    category = st.text_input("Category")
    unit_price = st.number_input("Unit Price")
    reorder_level = st.number_input("Reorder Level")

    product_id = None
    if product_name:
        product_id = get_primarykey(engine, "products", "product_id", ["product_name"], [product_name])

    data = {
        "product_name": product_name,
        "category": category,
        "unit_price": unit_price,
        "reorder_level": reorder_level
    }

    col1, col2, col3, col4 = st.columns(4)

    # search
    if col1.button("Search"):
        
        product = view(engine, "products", "product_id", product_id)

        if not product:
            st.warning("Product not found")
        else:
            st.dataframe([product])

    # add
    if col2.button("Add") and role in ("admin", "manager"):
        if not product_name or not category:
            st.warning("fill all required fields")
            return
        
        insert(engine, "products", data)
        st.success("product added")

    # update
    if col3.button("Update") and role in ("admin", "manager"):
        try:
            update(engine, "products", "product_id", product_id, data)
            st.success("Product Updated")
        except Exception as e:
            st.error("All fields are required to update.")
            st.exception(e)

    # delete
    if col4.button("Delete") and role == "admin":
        if not product_id:
            st.warning("Product not found")
            return
        
        delete(engine, "products", "product_id", product_id)
        st.success("Product Deleted")

    st.divider()
    st.subheader("View All Products")

    # Show all products
    query = """
        SELECT * FROM products
    """
    products = run_query(engine, query, fetch=True)
    if products:
        df = pd.DataFrame(products)
        st.dataframe(df)
    else:
        st.info("No products found")


# WAREHOUSE PAGE
def warehouse_page(role):
    st.header("Manage Warehouse")

    warehouse_city = st.text_input("Warehouse City")

    warehouse_total_capacity = st.number_input("Total Capacity", min_value=1)

    warehouse_id = None
    if warehouse_city:
        warehouse_id = get_primarykey(engine, "warehouse", "warehouse_id", ["warehouse_city"], [warehouse_city])

    data = {
        "warehouse_city": warehouse_city,
        "warehouse_total_capacity": warehouse_total_capacity
    }

    col1, col2, col3, col4 = st.columns(4)

    # search
    if col1.button("Search"):       
        warehouse = view(engine, "warehouse", "warehouse_id", warehouse_id)
        st.dataframe([warehouse])

    # add
    if col2.button("Add") and role in ("admin", "manager"):
        insert(engine, "warehouse", data)
        st.success("warehouse added")

    # update
    if col3.button("Update") and role in ("admin", "manager"):
        update(engine, "warehouse", "warehouse_id", warehouse_id, data)
        st.success("warehouse Updated")

    # delete
    if col4.button("Delete") and role in ("admin"):
        delete(engine, "warehouse", "warehouse_id", warehouse_id)
        st.success("warehouse Deleted")

    st.divider()
    st.subheader("View All Warehouses")

    # Show all warehouses
    query = """
        SELECT * FROM warehouse
    """
    warehouses = run_query(engine, query, fetch=True)
    if warehouses:
        df = pd.DataFrame(warehouses)
        st.dataframe(df)
    else:
        st.info("No warehouse found")


# SUPPLIERS PAGE
def suppliers_page(role):
    st.header("Manage Suppliers")

    supplier_name = st.text_input("Supplier Name")
    supplier_phone = st.text_input("Supplier Phone")
    supplier_email = st.text_input("Supplier Email")
    supplier_city = st.text_input("Supplier City")

    data = {
        "supplier_name": supplier_name,
        "supplier_phone": supplier_phone,
        "supplier_email": supplier_email,
        "supplier_city": supplier_city
    }

    supplier_id = None
    if supplier_name:
       supplier_id = get_primarykey(engine, "suppliers", "supplier_id", ["supplier_name"], [supplier_name])

    col1, col2, col3, col4 = st.columns(4)

    # search
    if col1.button("Search"):
        if not supplier_id:
            st.warning("no records found")
            return
        
        supplier = view(engine, "suppliers", "supplier_id", supplier_id)
        st.dataframe([supplier])

    # add
    if col2.button("Add") and role in ("admin", "manager"):
        insert(engine, "suppliers", data)
        st.success("Supplier added")

    # update
    if col3.button("Update") and role in ("admin", "manager"):
        update(engine, "suppliers", "supplier_id", supplier_id, data)
        st.success("Supplier Updated")

    # delete
    if col4.button("Delete") and role in ("admin"):
        delete(engine, "suppliers", "supplier_id", supplier_id)
        st.success("Supplier Deleted")

    st.divider()
    st.subheader("View All Suppliers")

    # Show all suppliers
    query = """
        SELECT * FROM suppliers
    """
    suppliers = run_query(engine, query, fetch=True)
    if suppliers:
        df = pd.DataFrame(suppliers)
        st.dataframe(df)
    else:
        st.info("No warehouse found")

# ORDERS PAGE
def orders_page(role):
    st.header("Manage Orders")

    # inputs
    supplier_name = st.text_input("Supplier Name")
    order_status = st.selectbox("Order Status",["pending", "received", "cancelled"])

    supplier_id = None
    if supplier_name:
        supplier_id = get_primarykey(engine,"suppliers","supplier_id",["supplier_name"],[supplier_name])

    order_id = get_primarykey(engine, "orders", "order_id", ["supplier_id"],[supplier_id])

    col1, col2, col3, col4 = st.columns(4)

    # search
    if col1.button("Search"):
        query = """
                SELECT o.*, s.supplier_name
                FROM orders o
                JOIN suppliers s ON o.supplier_id = s.supplier_id
                WHERE s.supplier_name= :supplier_name
        """
        order = run_query(engine, query,{"supplier_name": supplier_name},fetch=True)
        st.dataframe(order)

    # add
    if col2.button("Add") and role in ("admin", "manager"):
        if not supplier_name:
            st.warning("Supplier name is required")
            return
        
        if not supplier_id:
            st.warning("Supplier doesnt exist. Add supplier in suppliers page first.")
            return
        
        data = {
            "supplier_id": supplier_id,
            "order_status": "pending",
            "created_by": st.session_state.user["user_id"]
        }

        insert(engine, "orders", data)
        st.success("Order created")

    # update
    if col3.button("Update Status") and role in ("admin", "manager"):
        if not order_id:
            st.warning("Order ID required")
            return
        try:
            update_data = {"order_status": order_status}
            update(engine, "orders", "order_id", order_id, update_data)
            st.success("Order status updated")
        except Exception as e:
            st.error(f"Failed to update: {str(e)}")

    # delete
    if col4.button("Delete") and role in ("admin"):
        delete(engine, "orders", "order_id", order_id)
        st.success("Order Deleted")
    
    st.divider()
    st.subheader("View All Orders")
    
    # Show all orders
    query = """
        SELECT o.order_id, s.supplier_name, o.order_date, o.order_status, u.username as created_by
        FROM orders o
        LEFT JOIN suppliers s ON o.supplier_id = s.supplier_id
        LEFT JOIN users u ON o.created_by = u.user_id
        ORDER BY o.order_date DESC
    """
    orders = run_query(engine, query, fetch=True)
    if orders:
        df = pd.DataFrame(orders, columns=['Order ID', 'Supplier', 'Order Date', 'Status', 'Created By'])
        st.dataframe(df)
    else:
        st.info("No orders found")


# ORDER ITEMS PAGE
def order_items_page(role):
    st.header("Manage Order Items")
    
    order_id = st.number_input("Order ID", min_value=1)
    
    # Get product names
    product_rows = run_query(engine, "SELECT product_name FROM products", fetch=True)
    product_names = [i[0] for i in product_rows]
    product_name = st.selectbox("Product", product_names)
    
    quantity_ordered = st.number_input("Quantity", min_value=1)
    unit_price = st.number_input("Unit Price", min_value=1)
    
    product_id = None
    if product_name:
        product_id = get_primarykey(engine, "products", "product_id", ["product_name"], [product_name])
    
    data = {
        "order_id": order_id,
        "product_id": product_id,
        "quantity_ordered": quantity_ordered,
        "unit_price": unit_price
    }
    
    col1, col2= st.columns(2)
    
    # Viewing all items for an order
    if col1.button("View Order Items"):
        query = """
            SELECT oi.order_item_id, p.product_name, oi.quantity_ordered, 
                   oi.unit_price, (oi.quantity_ordered * oi.unit_price) as total
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            WHERE oi.order_id = :oid
        """
        items = run_query(engine, query, {"oid": order_id}, fetch=True)
        if items:
            st.dataframe(items)
            
            # Show order total
            total = sum(item[4] for item in items)
            st.info(f"Order Total: ₹{total:.2f}")
        else:
            st.warning("No items found for this order")
    
    if col2.button("Add") and role in ("admin", "manager"):
        if not order_id or not product_id:
            st.warning("Order ID and Product are required")
            return
        try:
            insert(engine, "order_items", data)
            st.success("Item added to order")
        except Exception as e:
            st.error(f"Failed to add item: {str(e)}")
    
    st.divider()
    st.subheader("Delete Order Item")
    
    item_id = st.number_input("Order Item ID (from table above)", min_value=1)
    
    if st.button("Delete Item") and role in ("admin", "manager"):
        if not item_id:
            st.warning("Item ID required")
            return
        
        try:
            delete(engine, "order_items", "order_item_id", item_id)
            st.success("Item deleted")
        except Exception as e:
            st.error(f"Failed to delete: {str(e)}")

# PAYMENTS PAGE
def payments_page(role):
    if role not in ("admin","manager"):
        st.error("Not authorised to view payments")
        return
    
    st.header("Payments")

    order_id = st.text_input("Order ID")
    amount_paid = st.number_input("Amount Paid", min_value=0)
    payment_status = st.selectbox("Payment Status",["pending", "partial", "completed"])

    payment_id = get_primarykey(engine,"payments", "payment_id",["order_id"],[order_id])

    data = {
        "order_id": order_id,
        "amount_paid": amount_paid,
        "payment_status": payment_status,
        "recorded_by": st.session_state.user["user_id"]
    }

    col1, col2, col3 = st.columns(3)

    # search
    if col1.button("Search"):
        if not payment_id:
            st.warning("Payment not found")
            return
        payment = view(engine, "payments", "payment_id", payment_id)
        st.dataframe([payment])

    # add
    if col2.button("Add") and role in ("admin", "manager"):
# /
        # Calculate order total
        total_query = """
            SELECT COALESCE(SUM(quantity_ordered * unit_price), 0)
            FROM order_items
            WHERE order_id = :oid
        """
        order_total = run_query(engine, total_query, {"oid": order_id}, fetch=True)[0][0]
        
        if order_total == 0:
            st.error("Cannot add payment: Order has no items")
            return
        
        # Check existing payments
        paid_query = """
            SELECT COALESCE(SUM(amount_paid), 0)
            FROM payments
            WHERE order_id = :oid
        """
        already_paid = run_query(engine, paid_query, {"oid": order_id}, fetch=True)[0][0]
        
        if already_paid + amount_paid > order_total:
            st.error(f"Payment exceeds order total. Order: ${order_total:.2f}, Already paid: ${already_paid:.2f}")
            return
# /      
        data["recorded_by"] = st.session_state.user["user_id"]

        try:
            insert(engine, "payments", data)
            st.success("Payment added")
        except Exception as e:
            st.error(f"Failed to add payment: {str(e)}")

    # delete
    if col3.button("Delete"):
        if role != "admin":
            st.error("Only admins can delete payments")
            return
        
        delete(engine, "payments", "payment_id", payment_id)
        st.success("Payment Deleted")


# ORDERS AND PAYMENTS PAGE
def orders_and_payments_page(role):

    # View all orders
    st.subheader("All Purchase Orders")
    
    query = """
        SELECT o.order_id, s.supplier_name, o.order_date, o.order_status, 
               COALESCE(SUM(oi.quantity_ordered * oi.unit_price), 0) as order_total,
               COALESCE(SUM(p.amount_paid), 0) as paid
        FROM orders o
        LEFT JOIN suppliers s ON o.supplier_id = s.supplier_id
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        LEFT JOIN payments p ON o.order_id = p.order_id
        GROUP BY o.order_id, s.supplier_name, o.order_date, o.order_status
        ORDER BY o.order_date DESC
    """
    orders = run_query(engine, query, fetch=True)
    
    # st.dataframe(orders)

    if orders:
        # Calculate balance for each order
        orders_with_balance = []
        for order in orders:
            # order_list is recreated every loop. tabhi orders with bal is required.
            order_list = list(order)
            balance = order[4] - order[5]  # total - paid
            order_list.append(balance)
            orders_with_balance.append(order_list)
        
        df = pd.DataFrame(orders_with_balance, 
                         columns=['Order ID', 'Supplier', 'Date', 'Status', 'Total', 'Paid', 'Balance'])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No orders yet")
    
    st.divider()
    
    tab1, tab2 = st.tabs(["Add Order", "Record Payment"])
    
    # TAB 1: create new order
    with tab1:        
        supplier_name = st.text_input("Supplier Name")
        order_id = st.number_input("Order ID", min_value=1)
        order_status = st.selectbox("Order Status",["pending", "received", "cancelled"])
        
        supplier_id = None
        if supplier_name:
            supplier_id = get_primarykey(engine, "suppliers", "supplier_id", ["supplier_name"], [supplier_name])
        
        col1, col2, col3 = st.columns(3)

        if col1.button("Create Order"):
            if not supplier_name:
                st.warning("Supplier name is required")
                return
            elif not supplier_id:
                st.error("Supplier does not exist!")
                return
            
            data = {
                "supplier_id": supplier_id,
                "order_status": "pending",
                "created_by": st.session_state.user["user_id"]
            }

            insert(engine, "orders", data)
            st.success("Order created")
            st.rerun()

        # update status
        if col2.button("Update Status") and role in ("admin", "manager"):
            if not order_id:
                st.warning("Order ID required")
                return
            try:
                update_data = {"order_status": order_status}
                update(engine, "orders", "order_id", order_id, update_data)
                st.success("Order status updated")
            except Exception as e:
                st.error(f"Failed to update: {str(e)}")

        # delete
        if col3.button("Delete Order") and role in ("admin"):
            delete(engine, "orders", "order_id", order_id)
            st.success("Order Deleted")

     
        # Show existing items
        items_query = """
            SELECT oi.order_item_id, p.product_name, oi.quantity_ordered, 
                    oi.unit_price, (oi.quantity_ordered * oi.unit_price) as total
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            WHERE oi.order_id = :oid
        """
        items = run_query(engine, items_query, {"oid": order_id}, fetch=True)
        
        st.write("Items in order:")
        items_df = pd.DataFrame(items)
        st.dataframe(items_df)
                
        st.divider()

        # Add new items
        st.subheader("Add New Items to Order")
        product_name = st.text_input("Product")
        
        product_id = None
        unit_price = None
        if product_name:
            product_id = get_primarykey(engine, "products", "product_id", ["product_name"], [product_name])
        if product_id:
            unit_price = get_col(engine, "products", "unit_price", "product_id", product_id)
        
        quantity_ordered = st.number_input("Quantity", min_value=1)

        
        if st.button("Add item to order"):
            if not order_id or not product_id:
                st.warning("Order ID and Product required")
                return
            
            order = view(engine, "orders", "order_id", order_id)

            if not order:
                st.error("Order not found")
                return

            data = {
                "order_id": order_id,
                "product_id": product_id,
                "quantity_ordered": quantity_ordered,
                "unit_price": unit_price
            }
            try:
                insert(engine, "order_items", data)
                st.success("Item added!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {str(e)}")
    
    # TAB 2: PAYMENTS
    with tab2:        
        payment_order_id = st.number_input("Order ID", min_value=1, key= "payments_oid")
        amount_paid = st.number_input("Amount received", min_value=1)
        payment_status = st.selectbox("Payment Status",["pending", "partial", "completed"])

        order_total = 0
        already_paid = 0
        balance = 0

        payment_id = get_primarykey(engine,"payments", "payment_id",["order_id"],[order_id])

        data = {
            "order_id": order_id,
            "amount_paid": amount_paid,
            "payment_status": payment_status,
            "recorded_by": st.session_state.user["user_id"]
        }

        # payment summary
        if payment_order_id:
            # order total
            total_query = """
                SELECT COALESCE(SUM(quantity_ordered * unit_price),0)
                FROM order_items
                WHERE order_id = :oid
            """
            order_total = run_query(engine, total_query, {"oid": payment_order_id}, fetch=True)[0][0]
            
            # paid
            paid_query = """
                SELECT COALESCE(SUM(amount_paid),0)
                FROM payments
                WHERE order_id = :oid
            """
            already_paid = run_query(engine, paid_query, {"oid": payment_order_id}, fetch=True)[0][0]
            
            # balance
            balance = order_total - already_paid

            st.write(f"Order Total : {order_total}")
            st.write(f"Already Paid : {already_paid}")
            st.write(f"Balance : {balance}")
                
        col1, col2, col3 = st.columns(3)

        # Record new payment        
        if col1.button("Record Payment", key="record_payment_btn"):
            if not payment_order_id:
                st.warning("Order ID required")
                return
            
            if order_total == 0:
                st.error("Order has no items")
                return
            
            new_total_paid = already_paid + amount_paid

            if new_total_paid >= order_total:
                payment_status = "completed"
            elif new_total_paid > 0:
                payment_status = "partial"
            else:
                payment_status = "pending"
            
            data = {
                "order_id": payment_order_id,
                "amount_paid": amount_paid,
                "payment_status": payment_status,
                "recorded_by": st.session_state.user["user_id"]
            }
            
            insert(engine, "payments", data)
            st.success(f"Remaining: ₹{order_total - new_total_paid}")
            st.rerun()

    # add
    if col2.button("Add") and role in ("admin", "manager"):
# /
        # Calculate order total
        total_query = """
            SELECT COALESCE(SUM(quantity_ordered * unit_price), 0)
            FROM order_items
            WHERE order_id = :oid
        """
        order_total = run_query(engine, total_query, {"oid": order_id}, fetch=True)[0][0]
        
        if order_total == 0:
            st.error("Cannot add payment: Order has no items")
            return
        
        # Check existing payments
        paid_query = """
            SELECT COALESCE(SUM(amount_paid), 0)
            FROM payments
            WHERE order_id = :oid
        """
        already_paid = run_query(engine, paid_query, {"oid": order_id}, fetch=True)[0][0]
        
        if already_paid + amount_paid > order_total:
            st.error(f"Payment exceeds order total. Order: ${order_total:.2f}, Already paid: ${already_paid:.2f}")
            return
# /      
        data["recorded_by"] = st.session_state.user["user_id"]

        try:
            insert(engine, "payments", data)
            st.success("Payment added")
        except Exception as e:
            st.error(f"Failed to add payment: {str(e)}")

    # delete
    if col3.button("Delete"):
        if role != "admin":
            st.error("Only admins can delete payments")
            return
        
        delete(engine, "payments", "payment_id", payment_id)
        st.success("Payment Deleted")

        st.divider()
        # Show payment history
        st.write("Payment History")

        payments_query = """
            SELECT payment_id, amount_paid, payment_date, payment_status
            FROM payments
            WHERE order_id = :oid
            ORDER BY payment_date DESC
        """
        payments = run_query(engine, payments_query, {"oid": payment_order_id}, fetch=True)
        payments_df = pd.DataFrame(payments)
        st.dataframe(payments_df)


# STOCK MOVEMENT PAGE
# /
def stock_movement_page(role):
    st.header("Stock Movement History")

    if role not in ("admin", "manager"):
        st.error("Not authorised")
        return

    query = """
        SELECT sm.movement_id, p.product_name, w.warehouse_city,
               sm.movement_type, sm.quantity, sm.movement_date,
               u.username as performed_by
        FROM stock_movement sm
        JOIN products p ON sm.product_id = p.product_id
        JOIN warehouse w ON sm.warehouse_id = w.warehouse_id
        LEFT JOIN users u ON sm.performed_by = u.user_id
        ORDER BY sm.movement_date DESC
    """
    
    rows = run_query(engine, query, fetch=True)
    
    if rows:
        # Convert to proper dataframe format
        df = pd.DataFrame(rows, columns=['Movement ID', 'Product', 'Warehouse', 
                                          'Type', 'Quantity', 'Date', 'Performed By'])
        st.dataframe(df)
    else:
        st.info("No stock movements recorded")
# /

# USERS PAGE
def users_page(role):
    if role != "admin":
        st.error("Only admin can manage users")
        return
    
    st.header("Manage Users")

    user_id = st.text_input("User ID")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    email = st.text_input("Email")
    phone = st.text_input("Phone")
    user_role = st.selectbox("Role", ["admin", "manager", "staff"])
    
    col1, col2, col3, col4 = st.columns(4)

    # search
    if col1.button("Search"):
        user = view(engine, "users", "user_id", user_id)
        if not user:
            st.warning("User not found")
            return
        user.pop("password", None)
        st.dataframe([user])

    # password reset
    st.divider()
    st.subheader("Password Reset")

    reset_user_id = st.number_input("User ID for password reset", min_value=1)
    new_password = st.text_input("New Password", type="password")

    if st.button("Reset password"):
        if not new_password or not reset_user_id:
            st.error("user id and new password required")
            return
        update(engine, "users", "user_id", reset_user_id, {"password": generate_password_hash(new_password)})
        st.success("Password reset successfully")

    # add
    if col2.button("Add"):
        if not username or not password or not email:
            st.error("username, password and emal required")
            return
        
        data = {
            "username": username,
            "password": generate_password_hash(password),
            "email": email,
            "phone": phone,
            "role": user_role
        }

        insert(engine, "users", data)
        st.success("User added")

    # update
    if col3.button("Update"):
        if not user_id:
            st.warning("User ID required")
            return
        
        data = {
            "username": username,
            "email": email,
            "phone": phone,
            "role": user_role
        }

        update(engine, "users", "user_id", user_id, data)
        st.success("User Updated")

    # delete
    if col4.button("Delete"):
        if not user_id:
            st.warning("User ID required")
            return
        
        delete(engine, "users", "user_id", user_id)
        st.success("User Deleted")

    st.divider()
    st.subheader("View All Users")
    
    # Show all users
    query = """
        SELECT * FROM users
    """
    users = run_query(engine, query, fetch=True)
    if users:
        df = pd.DataFrame(users)
        st.dataframe(df)
    else:
        st.info("No users found")


##################################################################

# main content

if page == "Inventory":
    inventory_page(role)

elif page == "Products":
    products_page(role)

elif page == "Warehouse":
    warehouse_page(role)

elif page == "Suppliers":
    suppliers_page(role)

elif page == "Orders and Payments":
    orders_and_payments_page(role)

elif page == "Stock In/Out":
    stock_movement_page(role)

elif page == "Users":
    users_page(role)

# elif page == "Orders":
#     orders_page(role)

elif page == "Order Items":
    order_items_page(role)

# elif page == "Payments":
#     payments_page(role)

