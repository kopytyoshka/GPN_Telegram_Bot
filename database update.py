import pandas as pd
from sqlalchemy import create_engine
import psycopg2 as psql

engine = create_engine('postgresql+psycopg2://postgres:postgres@localhost:5432/postgres')

try:
    connection = psql.connect(
        user="postgres",
        password="postgres",
        host="localhost",
        port="5432",
        database="postgres"
    )
    connection.autocommit = True

    with connection.cursor() as cursor:
        cursor.execute("truncate main_db")

except Exception as _ex:
    print("[INFO] Error with db connection")
finally:
    if connection:
        connection.close()
        print("[INFO] Connection with db closed")


with pd.ExcelFile('db/БД.xlsx') as xls:
    df = pd.read_excel(xls)
    df.to_sql(name='main_db', con=engine, if_exists='append', index=False)

