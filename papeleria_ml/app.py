from flask import Flask, render_template, request, redirect
import pyodbc
import joblib
import numpy as np

app = Flask(__name__)

conexion = pyodbc.connect(
    'DRIVER={SQL Server};'
    'SERVER=FABRI\SQLEXPRESS;'
    'DATABASE=papeleria_ml;'
    'Trusted_Connection=yes;'
)


cursor = conexion.cursor()

modelo = joblib.load('modelos/modelo_ventas.pkl')

@app.route('/')
def inicio():

    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()

    return render_template('index.html', productos=productos)


@app.route('/prediccion')
def prediccion():

    mes = 13

    prediccion = modelo.predict(np.array([[mes]]))

    return f"Predicción de ventas para el mes {mes}: {prediccion[0]:.0f}"


@app.route('/agregar_producto', methods=['GET', 'POST'])
def agregar_producto():

    if request.method == 'POST':

        nombre = request.form['nombre']
        precio = request.form['precio']
        stock = request.form['stock']

        cursor.execute("""
            INSERT INTO productos
            (nombre, precio, stock)
            VALUES (?, ?, ?)
        """, (nombre, precio, stock))

        conexion.commit()

        return redirect('/')

    return render_template('agregar_producto.html')


if __name__ == '__main__':
    app.run(debug=True)