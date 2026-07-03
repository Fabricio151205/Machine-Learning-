from flask import Flask, render_template, request, redirect, flash, session
import pyodbc
import joblib
import numpy as np
import pandas as pd
from io import BytesIO
from flask import send_file
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'papeleria_ml_2026'

conexion = pyodbc.connect(
    'DRIVER={SQL Server};'
    'SERVER=FABRI\SQLEXPRESS;'
    'DATABASE=papeleria_ml;'
    'Trusted_Connection=yes;'
)

modelo_ia = joblib.load('modelos/modelo_demanda.pkl')

encoder_productos = joblib.load(
    'modelos/encoder_productos.pkl'
)

cursor = conexion.cursor()

modelo = joblib.load('modelos/modelo_ventas.pkl')
def generar_alertas_ia():

    alertas = []

    cursor.execute("""
        SELECT
            id,
            nombre,
            stock
        FROM productos
    """)

    productos = cursor.fetchall()

    from datetime import datetime

    hoy = datetime.now()

    año = hoy.year
    mes = hoy.month + 1

    if mes > 12:
        mes = 1
        año += 1

    for producto in productos:

        producto_id = producto[0]
        nombre = producto[1]
        stock = producto[2]

        try:

            prediccion = modelo_ia.predict(
                [[producto_id, año, mes]]
            )[0]

            prediccion = round(prediccion)

            if prediccion > stock:

                alertas.append({

                    'nombre': nombre,

                    'stock': stock,

                    'prediccion': prediccion,

                    'reponer': prediccion - stock

                })

        except:

            pass
    
    alertas.sort(
        key=lambda x: x['reponer'],
        reverse=True
    )

    alertas = alertas[:5]

    return alertas
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
    # Total productos
    cursor.execute("""
        SELECT COUNT(*)
        FROM productos
    """)
    total_productos = cursor.fetchone()[0]

    # Total categorías
    cursor.execute("""
        SELECT COUNT(*)
        FROM categorias
    """)
    total_categorias = cursor.fetchone()[0]

    # Total proveedores
    cursor.execute("""
        SELECT COUNT(*)
        FROM proveedores
    """)
    total_proveedores = cursor.fetchone()[0]

    # Productos con stock bajo
    cursor.execute("""
        SELECT COUNT(*)
        FROM productos
        WHERE stock <= 5
    """)
    stock_bajo = cursor.fetchone()[0]
    alertas_ia = generar_alertas_ia()

    return render_template(
        'productos/index.html',
        productos=productos,
        categorias=categorias,
        categoria_seleccionada=int(categoria_id) if categoria_id else None,
        total_productos=total_productos,
        total_categorias=total_categorias,
        total_proveedores=total_proveedores,
        stock_bajo=stock_bajo,
        alertas_ia=alertas_ia
    )

@app.route('/categorias')
def categorias():

    cursor.execute("""
        SELECT * FROM categorias
    """)

    categorias = cursor.fetchall()

    return render_template(
        'categorias/categorias.html',
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

    return render_template('categorias/agregar_categoria.html')

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
        'categorias/editar_categoria.html',
        categoria=categoria
    )

@app.route('/proveedores')
def proveedores():

    cursor.execute("""
        SELECT * FROM proveedores
    """)

    proveedores = cursor.fetchall()

    return render_template(
        'proveedores/proveedores.html',
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

    return render_template('proveedores/agregar_proveedor.html')

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
        'proveedores/editar_proveedor.html',
        proveedor=proveedor
    )


@app.route('/ventas', methods=['GET', 'POST'])
def ventas():

    if 'carrito' not in session:
        session['carrito'] = []

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

    print(session['carrito'])

    total_carrito = sum(
        item['subtotal']
        for item in session['carrito']
    )

    return render_template(
        'ventas/ventas.html',
        productos=productos,
        carrito=session['carrito'],
        total_carrito=total_carrito
    )

@app.route('/agregar_carrito', methods=['POST'])
def agregar_carrito():

    producto_id = int(request.form['producto_id'])
    cantidad = int(request.form['cantidad'])

    cursor.execute("""
        SELECT nombre, precio, stock
        FROM productos
        WHERE id = ?
    """, (producto_id,))

    producto = cursor.fetchone()

    nombre = producto[0]
    precio = float(producto[1])
    stock = int(producto[2])

    if cantidad > stock:

        flash(
            f'Stock insuficiente. Disponible: {stock}'
        )

        return redirect('/ventas')

    carrito = session.get('carrito', [])

    producto_encontrado = False

    for item in carrito:

        if item['producto_id'] == producto_id:

            item['cantidad'] += cantidad
            item['subtotal'] = (
                item['cantidad'] * item['precio']
            )

            producto_encontrado = True
            break

    if not producto_encontrado:

        carrito.append({
            'producto_id': producto_id,
            'nombre': nombre,
            'cantidad': cantidad,
            'precio': precio,
            'subtotal': precio * cantidad
        })

    session['carrito'] = carrito

    flash('Producto agregado al carrito')

    return redirect('/ventas')

@app.route('/eliminar_carrito/<int:indice>')
def eliminar_carrito(indice):

    carrito = session.get('carrito', [])

    if 0 <= indice < len(carrito):
        carrito.pop(indice)

    session['carrito'] = carrito

    flash('Producto eliminado del carrito')

    return redirect('/ventas')

@app.route('/vaciar_carrito')
def vaciar_carrito():

    session['carrito'] = []

    flash('Carrito vaciado correctamente')

    return redirect('/ventas')
@app.route('/confirmar_venta', methods=['POST'])
def confirmar_venta():

    carrito = session.get('carrito', [])

    if not carrito:

        flash('El carrito está vacío')

        return redirect('/ventas')
    
    for item in carrito:

        cursor.execute("""
            SELECT stock
            FROM productos
            WHERE id = ?
        """, (item['producto_id'],))

        stock_actual = int(cursor.fetchone()[0])

        if item['cantidad'] > stock_actual:

            flash(
                f"Stock insuficiente para {item['nombre']}. Disponible: {stock_actual}"
            )

            return redirect('/ventas')
        
    total = sum(
        item['subtotal']
        for item in carrito
    )

    cursor.execute("""
        INSERT INTO ventas
        (total, usuario_id)
        VALUES (?, NULL)
    """, (total,))

    conexion.commit()

    cursor.execute(
        "SELECT MAX(id) FROM ventas"
    )

    venta_id = cursor.fetchone()[0]

    for item in carrito:

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
            item['producto_id'],
            item['cantidad'],
            item['precio'],
            item['subtotal']
        ))

        cursor.execute("""
            UPDATE productos
            SET stock = stock - ?
            WHERE id = ?
        """,
        (
            item['cantidad'],
            item['producto_id']
        ))

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
            item['producto_id'],
            'SALIDA',
            item['cantidad']
        ))

    conexion.commit()

    session['carrito'] = []

    flash(
        f'Venta registrada correctamente. Total: S/. {total:.2f}'
    )

    return redirect('/ventas')

@app.route('/historial_ventas')
def historial_ventas():

    cursor.execute("""
        SELECT *
        FROM ventas
        ORDER BY fecha DESC
    """)

    ventas = cursor.fetchall()

    return render_template(
        'ventas/historial_ventas.html',
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
        'ventas/detalle_venta.html',
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
        'inventario/movimientos_inventario.html',
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
        'inventario/alertas_stock.html',
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
        'inventario/entrada_inventario.html',
        productos=productos,
        entrada_inventario=session.get(
            'entrada_inventario',
            []
        )
    )

@app.route('/agregar_entrada', methods=['POST'])
def agregar_entrada():

    producto_id = int(request.form['producto_id'])
    cantidad = int(request.form['cantidad'])

    cursor.execute("""
        SELECT nombre
        FROM productos
        WHERE id = ?
    """, (producto_id,))

    producto = cursor.fetchone()

    nombre = producto[0]

    entrada = session.get(
        'entrada_inventario',
        []
    )

    encontrado = False

    for item in entrada:

        if item['producto_id'] == producto_id:

            item['cantidad'] += cantidad
            encontrado = True
            break

    if not encontrado:

        entrada.append({
            'producto_id': producto_id,
            'nombre': nombre,
            'cantidad': cantidad
        })

    session['entrada_inventario'] = entrada

    flash('Producto agregado')

    return redirect('/entrada_inventario')

@app.route('/eliminar_entrada/<int:indice>')
def eliminar_entrada(indice):

    entrada = session.get(
        'entrada_inventario',
        []
    )

    if 0 <= indice < len(entrada):

        entrada.pop(indice)

    session['entrada_inventario'] = entrada

    flash('Producto eliminado')

    return redirect('/entrada_inventario')

@app.route('/confirmar_entrada', methods=['POST'])
def confirmar_entrada():

    entrada = session.get(
        'entrada_inventario',
        []
    )

    if not entrada:

        flash('No hay productos para registrar')

        return redirect('/entrada_inventario')

    for item in entrada:

        cursor.execute("""
            UPDATE productos
            SET stock = stock + ?
            WHERE id = ?
        """,
        (
            item['cantidad'],
            item['producto_id']
        ))

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
            item['producto_id'],
            'ENTRADA',
            item['cantidad']
        ))

    conexion.commit()

    session['entrada_inventario'] = []

    flash(
        'Entrada de inventario registrada correctamente'
    )

    return redirect('/entrada_inventario')
@app.route('/vaciar_entrada')
def vaciar_entrada():

    session['entrada_inventario'] = []

    flash('Lista vaciada')

    return redirect('/entrada_inventario')

@app.route('/prediccion', methods=['GET', 'POST'])
def prediccion():

    resultado = None

    if request.method == 'POST':

        producto_id = int(
            request.form['producto_id']
        )

        anio = int(
            request.form['anio']
        )

        mes = int(
            request.form['mes']
        )

        resultado = modelo_ia.predict(
            [[producto_id, anio, mes]]
        )[0]

    cursor.execute("""
        SELECT id, nombre
        FROM productos
        ORDER BY nombre
    """)

    productos = cursor.fetchall()

    return render_template(
        'ia/prediccion.html',
        productos=productos,
        resultado=resultado
    )

@app.route('/predicciones_ia')
def predicciones_ia():

    buscar = request.args.get('buscar', '')

    cursor.execute("""
        SELECT
            id,
            nombre,
            stock
        FROM productos
        ORDER BY nombre
    """)

    productos = cursor.fetchall()

    predicciones = []

    from datetime import datetime

    hoy = datetime.now()

    año = hoy.year
    mes = hoy.month + 1

    if mes > 12:
        mes = 1
        año += 1

    predicciones_6_meses = []

    resultado_busqueda = None

    for producto in productos:

        producto_id = producto[0]
        nombre = producto[1]
        stock = producto[2]
    
        

        prediccion = round(
            modelo_ia.predict(
                [[producto_id, año, mes]]
            )[0]
        )
        if buscar:

            if buscar.lower() in nombre.lower():

                resultado_busqueda = {

                    'nombre': nombre,
                    'stock': stock,
                    'prediccion': prediccion,
                    'reponer': max(0, prediccion - stock)

                }

                predicciones_6_meses = []

                for i in range(1, 7):

                    mes_futuro = mes + i
                    anio_futuro = año

                    if mes_futuro > 12:
                        mes_futuro -= 12
                        anio_futuro += 1

                    pred_futura = round(
                        modelo_ia.predict(
                            [[producto_id, anio_futuro, mes_futuro]]
                        )[0]
                    )

                    predicciones_6_meses.append({

                        'anio': anio_futuro,
                        'mes': mes_futuro,
                        'prediccion': pred_futura

                    })

                

        predicciones.append({

            'nombre': nombre,
            'stock': stock,
            'prediccion': prediccion,
            'reponer': max(0, prediccion - stock)

        })

    alertas = [
        p for p in predicciones
        if p['reponer'] > 0
    ]
    labels_grafico = []
    datos_grafico = []

    for pred in predicciones_6_meses:

        labels_grafico.append(
            f"{pred['mes']}/{pred['anio']}"
        )

        datos_grafico.append(
            pred['prediccion']
        )

    return render_template(
        'ia/predicciones_ia.html',
        predicciones=predicciones,
        alertas=alertas,
        buscar=buscar,
        resultado_busqueda=resultado_busqueda,
        predicciones_6_meses=predicciones_6_meses,
        labels_grafico=labels_grafico,
        datos_grafico=datos_grafico
    )

@app.route('/exportar_excel_ia')
def exportar_excel_ia():

    cursor.execute("""
        SELECT
            id,
            nombre,
            stock
        FROM productos
        ORDER BY nombre
    """)

    productos = cursor.fetchall()

    hoy = datetime.now()

    año = hoy.year
    mes = hoy.month + 1

    if mes > 12:
        mes = 1
        año += 1

    predicciones = []

    for producto in productos:

        producto_id = producto[0]
        nombre = producto[1]
        stock = producto[2]

        prediccion = round(
            modelo_ia.predict(
                [[producto_id, año, mes]]
            )[0]
        )

        predicciones.append({

            'Producto': nombre,
            'Stock': stock,
            'Prediccion': prediccion,
            'Reponer': max(0, prediccion - stock)

        })

    alertas = [
        p for p in predicciones
        if p['Reponer'] > 0
    ]

    output = BytesIO()

    resumen = pd.DataFrame({

        'Indicador': [

            'Fecha Reporte',
            'Productos Analizados',
            'Alertas Generadas',
            'Mayor Demanda',
            'Menor Demanda'

        ],

        'Valor': [

            datetime.now().strftime('%d/%m/%Y'),
            len(predicciones),
            len(alertas),
            max(predicciones, key=lambda x: x['Prediccion'])['Producto'],
            min(predicciones, key=lambda x: x['Prediccion'])['Producto']

        ]

    })

    with pd.ExcelWriter(
        output,
        engine='openpyxl'
    ) as writer:
        
        resumen.to_excel(
            writer,
            sheet_name='Resumen IA',
            index=False
        )

        pd.DataFrame(alertas).to_excel(
            writer,
            sheet_name='Alertas IA',
            index=False
        )

        pd.DataFrame(predicciones).to_excel(
            writer,
            sheet_name='Predicciones',
            index=False
        )

    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name=f'Reporte_IA_{datetime.now().strftime("%Y-%m-%d")}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


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
        'productos/agregar_producto.html',
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
        categoria_id = request.form['categoria_id']
        proveedor_id = request.form['proveedor_id']
        precio = request.form['precio']
        stock = request.form['stock']

        cursor.execute("""
            UPDATE productos
            SET
                nombre = ?,
                categoria_id = ?,
                proveedor_id = ?,
                precio = ?,
                stock = ?
            WHERE id = ?
        """,
        (
            nombre,
            categoria_id,
            proveedor_id,
            precio,
            stock,
            id
        ))

        conexion.commit()

        return redirect('/')

    cursor.execute(
        "SELECT * FROM productos WHERE id = ?",
        (id,)
    )

    producto = cursor.fetchone()

    cursor.execute("""
        SELECT id, nombre
        FROM categorias
        ORDER BY nombre
    """)
    categorias = cursor.fetchall()

    cursor.execute("""
        SELECT id, nombre
        FROM proveedores
        ORDER BY nombre
    """)
    proveedores = cursor.fetchall()

    return render_template(
        'productos/editar_producto.html',
        producto=producto,
        categorias=categorias,
        proveedores=proveedores
    )

if __name__ == '__main__':
    app.run(debug=True)