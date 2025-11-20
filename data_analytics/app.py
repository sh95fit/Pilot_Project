from data.database import DatabaseConnection

query = "SELECT * FROM order_service.orders"

df = DatabaseConnection.execute_query(query)

print(df)