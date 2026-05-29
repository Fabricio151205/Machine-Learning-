import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib

# Leer dataset
data = pd.read_csv('dataset/ventas.csv')

# Variables
X = data[['mes']]
y = data['ventas']

# Crear modelo
modelo = LinearRegression()

# Entrenar modelo
modelo.fit(X, y)

# Guardar modelo
joblib.dump(modelo, 'modelos/modelo_ventas.pkl')

print("Modelo entrenado correctamente")