# ⛰️ Pukamani - Sistema de Control de Costos Mineros

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.11+-yellow)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red)
![Status](https://img.shields.io/badge/Status-Production-green)

> **Sistema integral para la gestión, estandarización y control de costos operativos en minería subterránea convencional.**

---

## 📋 Descripción del Proyecto

**Pukamani** (del quechua "Tierra Roja") es una solución tecnológica diseñada para modernizar el seguimiento financiero de las operaciones mineras. El sistema permite digitalizar el flujo de información de costos diarios, eliminando la dependencia de hojas de cálculo dispersas y centralizando la data en una base de datos segura en la nube.

El objetivo principal es proporcionar a la Gerencia y Superintendencia visibilidad en tiempo real sobre el **OPEX**, permitiendo la toma de decisiones basada en datos.

## 🚀 Funcionalidades Principales

* **🔐 Seguridad Robusta**: Sistema de autenticación encriptado (Bcrypt) con roles de usuario (Admin, Digitador, Lector).
* **📊 Dashboard Ejecutivo**: Visualización de KPIs en tiempo real, distribución de costos por partida y análisis de tendencias.
* **📝 Registro Diario**: Interfaz optimizada para la carga de datos operativos (Mano de obra, suministros, servicios).
* **☁️ Base de Datos Cloud**: Persistencia de datos en PostgreSQL (vía Supabase) con backups automáticos.
* **📥 Reportería**: Exportación automatizada de reportes en formato Excel compatible con ERPs.

## 🛠️ Tecnologías Utilizadas

Este proyecto ha sido construido utilizando un stack moderno y eficiente:

* **Frontend/Backend**: [Streamlit](https://streamlit.io/) (Framework de Python para Data Apps).
* **Base de Datos**: [Supabase](https://supabase.com/) (PostgreSQL).
* **Análisis de Datos**: Pandas & NumPy.
* **Visualización**: Altair & Plotly.
* **Seguridad**: Hasheo de contraseñas con Bcrypt.

---

## ⚙️ Instalación y Despliegue Local

Si deseas correr este proyecto en tu entorno local, sigue estos pasos:

### 1. Clonar el repositorio
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