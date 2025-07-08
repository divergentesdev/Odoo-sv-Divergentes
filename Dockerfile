FROM odoo:18.0

USER root

# Instalar dependencias del sistema para El Salvador
RUN apt-get update && apt-get install -y \
    # Dependencias para firma digital
    python3-cryptography \
    python3-openssl \
    python3-lxml \
    libxml2-dev \
    libxmlsec1-dev \
    libxmlsec1-openssl \
    pkg-config \
    gcc \
    python3-dev \
    build-essential \
    # Utilidades adicionales
    curl \
    wget \
    vim \
    git \
    # Dependencias para validación JSON
    python3-jsonschema \
    # Limpiar cache
    && rm -rf /var/lib/apt/lists/*

# Instalar paquetes Python adicionales
RUN pip3 install --break-system-packages \
    xmlsec \
    jsonschema \
    requests \
    cryptography \
    pyOpenSSL \
    lxml

# Crear directorios necesarios
RUN mkdir -p /var/log/odoo /mnt/extra-addons /etc/odoo

# Copiar archivo de configuración
COPY config/odoo.conf /etc/odoo/odoo.conf

# Establecer permisos
RUN chown -R odoo:odoo /var/log/odoo /mnt/extra-addons /etc/odoo

USER odoo

# Exponer puertos
EXPOSE 8069 8072

# Comando por defecto
CMD ["odoo"]