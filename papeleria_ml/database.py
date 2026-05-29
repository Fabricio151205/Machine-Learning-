import pyodbc

conexion = pyodbc.connect(
    'DRIVER={SQL Server};'
    'SERVER=FABRI\SQLEXPRESS;'
    'DATABASE=papeleria_ml;'
    'Trusted_Connection=yes;'
)

print("Conexión exitosa")