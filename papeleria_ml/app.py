from flask import Flask, render_template, request, redirect, flash
import pyodbc
import joblib
import numpy as np

app = Flask(__name__)
app.secret_key = 'papeleria_ml_2026'

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

    categoria_id = request.args.get('categoria')

    cursor.execute("""
        SELECT *
        FROM categorias
        ORDER BY nombre
    """)
    categorias = cursor.fetchall()

    if categoria_id:

        cursor.execute("""
            SELECT
                p.id,
                p.nombre,
                c.nombre AS categoria,
                pr.nombre AS proveedor,
                p.precio,
                p.stock
            FROM productos p
            LEFT JOIN categorias c
                ON p.categoria_id = c.id
            LEFT JOIN proveedores pr
                ON p.proveedor_id = pr.id
            WHERE p.categoria_id = ?
            ORDER BY p.id
        """, (categoria_id,))

    else:

        cursor.execute("""
            SELECT
                p.id,
                p.nombre,
                c.nombre AS categoria,
                pr.nombre AS proveedor,
                p.precio,
                p.stock
            FROM productos p
            LEFT JOIN categorias c
                ON p.categoria_id = c.id
            LEFT JOIN proveedores pr
                ON p.proveedor_id = pr.id
            ORDER BY p.id
        """)

    productos = cursor.fetchall()

    return render_template(
        'index.html',
        productos=productos,
        categorias=categorias,
        categoria_seleccionada=int(categoria_id) if categoria_id else None
    )

    cursor.execute("""
        SELECT
            p.id,
            p.nombre,
            c.nombre AS categoria,
            pr.nombre AS proveedor,
            p.precio,
            p.stock
        FROM productos p
        LEFT JOIN categorias c
            ON p.categoria_id = c.id
        LEFT JOIN proveedores pr
            ON p.proveedor_id = pr.id
        ORDER BY p.id
    """)

    productos = cursor.fetchall()

    return render_template(
        'index.html',
        productos=productos
    )

@app.route('/categorias')
def categorias():

    cursor.execute("""
        SELECT * FROM categorias
    """)

    categorias = cursor.fetchall()

    return render_template(
        'categorias.html',
        categorias=categorias
    )

@app.route('/agregar_categoria', methods=['GET', 'POST'])
def agregar_categoria():

    if request.method == 'POST':

        nombre = request.form['nombre']
        descripcion = request.form['descripcion']

        cursor.execute("""
            INSERT INTO categorias
            (nombre, descripcion)
            VALUES (?, ?)
        """, (nombre, descripcion))

        conexion.commit()

        return redirect('/categorias')

    return render_template('agregar_categoria.html')

@app.route('/eliminar_categoria/<int:id>')
def eliminar_categoria(id):

    cursor.execute(
        "DELETE FROM categorias WHERE id = ?",
        (id,)
    )

    conexion.commit()

    return redirect('/categorias')

@app.route('/editar_categoria/<int:id>', methods=['GET', 'POST'])
def editar_categoria(id):

    if request.method == 'POST':

        nombre = request.form['nombre']
        descripcion = request.form['descripcion']

        cursor.execute("""
            UPDATE categorias
            SET nombre = ?, descripcion = ?
            WHERE id = ?
        """, (nombre, descripcion, id))

        conexion.commit()

        return redirect('/categorias')

    cursor.execute(
        "SELECT * FROM categorias WHERE id = ?",
        (id,)
    )

    categoria = cursor.fetchone()

    return render_template(
        'editar_categoria.html',
        categoria=categoria
    )

@app.route('/proveedores')
def proveedores():

    cursor.execute("""
        SELECT * FROM proveedores
    """)

    proveedores = cursor.fetchall()

    return render_template(
        'proveedores.html',
        proveedores=proveedores
    )

@app.route('/agregar_proveedor', methods=['GET', 'POST'])
def agregar_proveedor():

    if request.method == 'POST':

        nombre = request.form['nombre']
        telefono = request.form['telefono']
        correo = request.form['correo']
        direccion = request.form['direccion']

        cursor.execute("""
            INSERT INTO proveedores
            (nombre, telefono, correo, direccion)
            VALUES (?, ?, ?, ?)
        """, (nombre, telefono, correo, direccion))

        conexion.commit()

        return redirect('/proveedores')

    return render_template('agregar_proveedor.html')

@app.route('/eliminar_proveedor/<int:id>')
def eliminar_proveedor(id):

    cursor.execute(
        "DELETE FROM proveedores WHERE id = ?",
        (id,)
    )

    conexion.commit()

    return redirect('/proveedores')

@app.route('/editar_proveedor/<int:id>', methods=['GET', 'POST'])
def editar_proveedor(id):

    if request.method == 'POST':

        nombre = request.form['nombre']
        telefono = request.form['telefono']
        correo = request.form['correo']
        direccion = request.form['direccion']

        cursor.execute("""
            UPDATE proveedores
            SET nombre = ?,
                telefono = ?,
                correo = ?,
                direccion = ?
            WHERE id = ?
        """, (nombre, telefono, correo, direccion, id))

        conexion.commit()

        return redirect('/proveedores')

    cursor.execute(
        "SELECT * FROM proveedores WHERE id = ?",
        (id,)
    )

    proveedor = cursor.fetchone()

    return render_template(
        'editar_proveedor.html',
        proveedor=proveedor
    )

@app.route('/ventas', methods=['GET', 'POST'])
def ventas():

    if request.method == 'POST':

        producto_id = int(request.form['producto_id'])
        cantidad = int(request.form['cantidad'])

        cursor.execute("""
            SELECT precio, stock
            FROM productos
            WHERE id = ?
        """, (producto_id,))

        producto = cursor.fetchone()

        precio = float(producto[0])
        stock_actual = int(producto[1])

        total = precio * cantidad

        if cantidad > stock_actual:

            flash(
                f'Stock insuficiente. Disponible: {stock_actual}'
            )

            return redirect('/ventas')

        cursor.execute("""
            INSERT INTO ventas
            (total, usuario_id)
            VALUES (?, NULL)
        """, (total,))

        conexion.commit()

        # Obtener ID de la venta recién creada
        cursor.execute("SELECT MAX(id) FROM ventas")

        venta_id = cursor.fetchone()[0]

        # Guardar detalle de venta
        cursor.execute("""
            INSERT INTO detalle_ventas
            (
                venta_id,
                producto_id,
                cantidad,
                precio_unitario,
                subtotal
            )
            VALUES (?, ?, ?, ?, ?)
        """,
        (
            venta_id,
            producto_id,
            cantidad,
            precio,
            total
        ))

        conexion.commit()

        # Descontar stock
        cursor.execute("""
            UPDATE productos
            SET stock = stock - ?
            WHERE id = ?
        """, (cantidad, producto_id))

        conexion.commit()

        # Registrar movimiento de inventario
        cursor.execute("""
            INSERT INTO movimientos_inventario
            (
                producto_id,
                tipo_movimiento,
                cantidad
            )
            VALUES (?, ?, ?)
        """,
        (
            producto_id,
            'SALIDA',
            cantidad
        ))

        conexion.commit()

        flash(f'Venta registrada correctamente. Total: S/. {total:.2f}')

        return redirect('/ventas')
    
    cursor.execute("""
        SELECT * FROM productos
    """)

    productos = cursor.fetchall()

    return render_template(
        'ventas.html',
        productos=productos
    )

@app.route('/historial_ventas')
def historial_ventas():

    cursor.execute("""
        SELECT *
        FROM ventas
        ORDER BY fecha DESC
    """)

    ventas = cursor.fetchall()

    return render_template(
        'historial_ventas.html',
        ventas=ventas
    )

@app.route('/detalle_venta/<int:venta_id>')
def detalle_venta(venta_id):

    cursor.execute("""
        SELECT
            p.nombre,
            dv.cantidad,
            dv.precio_unitario,
            dv.subtotal
        FROM detalle_ventas dv
        INNER JOIN productos p
            ON dv.producto_id = p.id
        WHERE dv.venta_id = ?
    """, (venta_id,))

    detalles = cursor.fetchall()

    return render_template(
        'detalle_venta.html',
        detalles=detalles
    )

@app.route('/movimientos_inventario')
def movimientos_inventario():

    cursor.execute("""
        SELECT
            mi.id,
            p.nombre,
            mi.tipo_movimiento,
            mi.cantidad,
            mi.fecha
        FROM movimientos_inventario mi
        INNER JOIN productos p
            ON mi.producto_id = p.id
        ORDER BY mi.fecha DESC
    """)

    movimientos = cursor.fetchall()

    return render_template(
        'movimientos_inventario.html',
        movimientos=movimientos
    )


@app.route('/alertas_stock')
def alertas_stock():

    cursor.execute("""
        SELECT *
        FROM productos
        WHERE stock <= 5
        ORDER BY stock ASC
    """)

    productos = cursor.fetchall()

    return render_template(
        'alertas_stock.html',
        productos=productos
    )

@app.route('/entrada_inventario', methods=['GET', 'POST'])
def entrada_inventario():

    if request.method == 'POST':

        producto_id = int(request.form['producto_id'])
        cantidad = int(request.form['cantidad'])

        # Aumentar stock
        cursor.execute("""
            UPDATE productos
            SET stock = stock + ?
            WHERE id = ?
        """, (cantidad, producto_id))

        conexion.commit()

        # Registrar movimiento
        cursor.execute("""
            INSERT INTO movimientos_inventario
            (
                producto_id,
                tipo_movimiento,
                cantidad
            )
            VALUES (?, ?, ?)
        """,
        (
            producto_id,
            'ENTRADA',
            cantidad
        ))

        conexion.commit()

        flash(
            f'Se ingresaron {cantidad} unidades al inventario'
        )

        return redirect('/entrada_inventario')
    
    
    cursor.execute("""
        SELECT *
        FROM productos
    """)

    productos = cursor.fetchall()

    return render_template(
        'entrada_inventario.html',
        productos=productos
    )
@app.route('/prediccion')
def prediccion():

    mes = 13

    prediccion = modelo.predict(np.array([[mes]]))

    return f"Predicción de ventas para el mes {mes}: {prediccion[0]:.0f}"


@app.route('/agregar_producto', methods=['GET', 'POST'])
def agregar_producto():

    if request.method == 'POST':

        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        categoria_id = request.form['categoria_id']
        proveedor_id = request.form['proveedor_id']
        precio = request.form['precio']
        stock = request.form['stock']

        cursor.execute("""
            INSERT INTO productos
            (
                nombre,
                descripcion,
                categoria_id,
                proveedor_id,
                precio,
                stock
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            nombre,
            descripcion,
            categoria_id,
            proveedor_id,
            precio,
            stock
        ))

        conexion.commit()

        return redirect('/')

    cursor.execute("""
        SELECT *
        FROM categorias
    """)
    categorias = cursor.fetchall()

    cursor.execute("""
        SELECT *
        FROM proveedores
    """)
    proveedores = cursor.fetchall()

    return render_template(
        'agregar_producto.html',
        categorias=categorias,
        proveedores=proveedores
    )

@app.route('/eliminar_producto/<int:id>')
def eliminar_producto(id):

    cursor.execute(
        "DELETE FROM productos WHERE id = ?",
        (id,)
    )

    conexion.commit()

    return redirect('/')

@app.route('/editar_producto/<int:id>', methods=['GET', 'POST'])
def editar_producto(id):

    if request.method == 'POST':

        nombre = request.form['nombre']
        precio = request.form['precio']
        stock = request.form['stock']

        cursor.execute("""
            UPDATE productos
            SET nombre = ?, precio = ?, stock = ?
            WHERE id = ?
        """, (nombre, precio, stock, id))

        conexion.commit()

        return redirect('/')

    cursor.execute(
        "SELECT * FROM productos WHERE id = ?",
        (id,)
    )

    producto = cursor.fetchone()

    return render_template(
        'editar_producto.html',
        producto=producto
    )

if __name__ == '__main__':
    app.run(debug=True)