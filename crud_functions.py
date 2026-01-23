from sqlalchemy import text

def run_query(engine, query, params= None, fetch= False):
    with engine.begin() as conn:
        result = conn.execute(text(query), params or {})
        if fetch:
            return result.fetchall()

def view(engine, table, column, value):
    query = f"SELECT * FROM {table} WHERE {column} = :val"
    rows = run_query(engine, query, {"val": value}, fetch= True)
    if rows:
        return dict(rows[0]._mapping)
    return None
    
def insert(engine, table, data):
    cols = ", ".join(data.keys())
    vals = ", ".join(f":{k}" for k in data)
    query = f"""INSERT INTO {table} ({cols})
                VALUES ({vals})"""
    run_query(engine, query, data)

def update(engine, table, where_column, where_value, data):
    set_part = ", ".join(f"{k} = :{k}" for k in data)
    query = f"""UPDATE {table}
                SET {set_part}
                WHERE {where_column} = :where_value
                """
    data["where_value"] = where_value

    run_query(engine, query, data)

def delete(engine, table, column, value):
    query = f"DELETE FROM {table} WHERE {column} = :val"
    run_query(engine, query, {"val": value})

def get_primarykey(engine, table, pk_column, search_columns, search_values):

    # search_columns and search_values are list items
    if len(search_columns) != len(search_values):
        raise ValueError("Columns and Values length not equal!")
    
    conditions = " AND ".join(f"{k} = :{k}" for k in search_columns)

    query = f"""SELECT {pk_column}
                FROM {table}
                WHERE {conditions}
    """

    # zip used to merge the two columns then convert into dict to pass in parameters
    params = dict(zip(search_columns, search_values))

    rows = run_query(engine, query, params, fetch=True)

    if rows:
        return rows[0][0]
    return None

def get_col(engine, table, column_to_get, search_column, search_value):

    query = f"""SELECT {column_to_get}
                FROM {table}
                WHERE {search_column} = :value
    """
    rows = run_query(engine,query, {"value": search_value}, fetch= True)

    if rows:
        return rows[0][0]
    return None