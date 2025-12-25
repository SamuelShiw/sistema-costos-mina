# 💎 CORE - Sistema de Control de Operaciones y Recursos

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.11+-yellow)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red)
![Status](https://img.shields.io/badge/Status-Production-green)

> **Sistema integral para la gestión, trazabilidad y control de costos operativos (OPEX) en minería subterránea.**

---

## 📋 Descripción del Proyecto

**CORE** (Control de Operaciones y Recursos) es una solución tecnológica desarrollada para optimizar el seguimiento financiero de las operaciones en la unidad minera **Pukamani**. 

El sistema digitaliza el flujo de información diario, reemplazando las hojas de cálculo descentralizadas por una arquitectura en la nube. Su objetivo es eliminar la "ceguera operativa", proporcionando a la Gerencia y Superintendencia visibilidad en tiempo real sobre el gasto por labor y centro de costos.

## 🚀 Funcionalidades Principales

* **🔐 Seguridad Robusta**: Roles diferenciados (Admin, Digitador, Lector) con encriptación de claves.
* **📊 Dashboard Ejecutivo**: KPIs en tiempo real, pareto de costos y curvas de avance vs. gasto.
* **📝 Registro Validado**: Interfaz que impide errores de tipeo en labores e insumos.
* **📥 Reportes Corporativos**: Generación automática de Excel con Tablas Dinámicas y gráficos listos para Finanzas.
* **☁️ Base de Datos Cloud**: Arquitectura SQL (Supabase) inmutable y segura.

## 🛠️ Tecnologías Utilizadas

Proyecto construido bajo estándares modernos de Ingeniería de Software:

* **Frontend**: [Streamlit](https://streamlit.io/) (UI reactiva).
* **Backend/DB**: [Supabase](https://supabase.com/) (PostgreSQL).
* **Data Processing**: Pandas & NumPy.
* **Reportes**: OpenPyXL (Motor de generación de Excel).
* **Visualización**: Altair Charts.

---

## ⚙️ Instalación Local (Para Desarrolladores)

1. **Clonar el repositorio**
   ```bash
   git clone [https://github.com/SamuelShiw/sistema-costos-mina.git](https://github.com/SamuelShiw/sistema-costos-mina.git)
   cd sistema-costos-mina

2. Crear entorno virtual
python -m venv venv
# En Windows:
.\venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

3. Instalar dependencias
pip install -r requirements.txt

Configurar variables de entorno
Crea una carpeta de llamada.streamlit y dentro de un archivo secrets.tomlcon tus credenciales de base de datos:
[postgres]
host = "tu-host-supabase"
port = 5432
dbname = "postgres"
user = "postgres"
password = "tu-password-seguro"

Ejecutar la aplicación
streamlit run app.py

📂 Estructura del Proyecto

sistema-costos-mina/
├── modules/            # Módulos de la lógica de negocio
│   ├── auth.py         # Autenticación y gestión de usuarios
│   ├── dashboard.py    # Visualización y KPIs
│   ├── registro.py     # Formularios de ingreso de data
│   └── maestros.py     # Configuración de tablas maestras
├── .streamlit/         # Configuración y Secretos (Ignorado en Git)
├── app.py              # Punto de entrada principal
├── database.py         # Conector a PostgreSQL
├── requirements.txt    # Dependencias del proyecto
└── README.md           # Documentación

👨‍💻 Autor
Desarrollado por J. Samuel - Ingeniero de Software & Especialista en Minería .

© 2025 Sistemas Pukamani. Todos los derechos reservados.