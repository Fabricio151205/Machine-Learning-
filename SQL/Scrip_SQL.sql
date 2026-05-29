CREATE DATABASE papeleria_ml;
GO

USE papeleria_ml;
GO

-- =========================
-- TABLA USUARIOS
-- =========================
CREATE TABLE usuarios (
    id INT PRIMARY KEY IDENTITY(1,1),
    nombre VARCHAR(100) NOT NULL,
    usuario VARCHAR(50) UNIQUE NOT NULL,
    contrasena VARCHAR(255) NOT NULL,
    rol VARCHAR(50),
    fecha_creacion DATETIME DEFAULT GETDATE()
);

-- =========================
-- TABLA CATEGORIAS
-- =========================
CREATE TABLE categorias (
    id INT PRIMARY KEY IDENTITY(1,1),
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(255)
);

-- =========================
-- TABLA PROVEEDORES
-- =========================
CREATE TABLE proveedores (
    id INT PRIMARY KEY IDENTITY(1,1),
    nombre VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    correo VARCHAR(100),
    direccion VARCHAR(255)
);

-- =========================
-- TABLA PRODUCTOS
-- =========================
CREATE TABLE productos (
    id INT PRIMARY KEY IDENTITY(1,1),
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(255),
    precio DECIMAL(10,2) NOT NULL,
    stock INT NOT NULL,
    categoria_id INT,
    proveedor_id INT,
    
    FOREIGN KEY (categoria_id) REFERENCES categorias(id),
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
);

-- =========================
-- TABLA INVENTARIO
-- =========================
CREATE TABLE inventario (
    id INT PRIMARY KEY IDENTITY(1,1),
    producto_id INT NOT NULL,
    stock_actual INT NOT NULL,
    stock_minimo INT NOT NULL,
    ultima_actualizacion DATETIME DEFAULT GETDATE(),

    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

-- =========================
-- TABLA VENTAS
-- =========================
CREATE TABLE ventas (
    id INT PRIMARY KEY IDENTITY(1,1),
    fecha DATETIME DEFAULT GETDATE(),
    total DECIMAL(10,2) NOT NULL,
    usuario_id INT,

    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- =========================
-- TABLA DETALLE_VENTAS
-- =========================
CREATE TABLE detalle_ventas (
    id INT PRIMARY KEY IDENTITY(1,1),
    venta_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,

    FOREIGN KEY (venta_id) REFERENCES ventas(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

-- =========================
-- TABLA MOVIMIENTOS INVENTARIO
-- =========================
CREATE TABLE movimientos_inventario (
    id INT PRIMARY KEY IDENTITY(1,1),
    producto_id INT NOT NULL,
    tipo_movimiento VARCHAR(20),
    cantidad INT NOT NULL,
    fecha DATETIME DEFAULT GETDATE(),

    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

-- =========================
-- TABLA PREDICCIONES
-- =========================
CREATE TABLE predicciones (
    id INT PRIMARY KEY IDENTITY(1,1),
    producto_id INT NOT NULL,
    demanda_predicha INT NOT NULL,
    fecha_prediccion DATETIME DEFAULT GETDATE(),

    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

-- =========================
-- TABLA ALERTAS STOCK
-- =========================
CREATE TABLE alertas_stock (
    id INT PRIMARY KEY IDENTITY(1,1),
    producto_id INT NOT NULL,
    mensaje VARCHAR(255),
    fecha_alerta DATETIME DEFAULT GETDATE(),

    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

-- =========================
-- TABLA HISTORIAL PREDICCIONES
-- =========================
CREATE TABLE historial_predicciones (
    id INT PRIMARY KEY IDENTITY(1,1),
    producto_id INT NOT NULL,
    prediccion_anterior INT,
    prediccion_nueva INT,
    fecha DATETIME DEFAULT GETDATE(),

    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

-- =========================
-- INSERTAMOS INFORMACION (EJMEPLOS)
-- =========================
INSERT INTO categorias(nombre)
VALUES ('Útiles escolares');

INSERT INTO proveedores(nombre)
VALUES ('Proveedor General');

INSERT INTO productos(nombre, descripcion, precio, stock, categoria_id, proveedor_id)
VALUES ('Lapicero', 'Lapicero azul', 2.50, 100, 1, 1);

ALTER TABLE productos
ALTER COLUMN descripcion VARCHAR(255) NULL;

ALTER TABLE productos
ALTER COLUMN categoria_id INT NULL;

ALTER TABLE productos
ALTER COLUMN proveedor_id INT NULL;