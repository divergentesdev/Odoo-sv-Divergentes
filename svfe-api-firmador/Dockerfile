# Multi-stage build para el firmador electrónico
FROM maven:3.6.3-openjdk-8-slim AS build

# Directorio de trabajo
WORKDIR /app

# Copiar archivos del proyecto
COPY svfe-api-firmador/pom.xml .
COPY svfe-api-firmador/src ./src

# Compilar la aplicación
RUN mvn clean package -DskipTests

# Descomprimir el JAR para optimizar el tamaño de la imagen
RUN mkdir -p target/dependency && (cd target/dependency; jar -xf ../*.jar)

# Imagen final
FROM openjdk:8-jre-alpine

# Instalar certificados CA
RUN apk --no-cache add ca-certificates

# Crear directorio de trabajo
WORKDIR /app

# Crear directorios para certificados
RUN mkdir -p /app/temp /app/uploads

# Copiar las dependencias y clases desde la imagen de build
ARG DEPENDENCY=/app/target/dependency
COPY --from=build ${DEPENDENCY}/BOOT-INF/lib /app/lib
COPY --from=build ${DEPENDENCY}/META-INF /app/META-INF  
COPY --from=build ${DEPENDENCY}/BOOT-INF/classes /app

# Exponer puerto
EXPOSE 8113

# Comando de inicio
ENTRYPOINT ["java","-cp","/app:/app/lib/*","sv.mh.fe.Application"]