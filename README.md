# Base de datos transaccional de Spotify

Modelo y datos de las tareas 2 y 3 de Ingeniería de Datos. Incluye las muestras A–D de Laura, el esquema PostgreSQL, las consultas y las pruebas de restricciones y transacciones.

## Contenido

- `db/01_schema.sql`: tablas, restricciones y comprobaciones diferidas.
- `db/02_seed.sql`: datos originales y casos límite adicionales.
- `tests.sql`: consultas, pruebas de restricciones y transacciones exitosas y fallidas.
- `docs/diagrama_conceptual.png` y `docs/diagrama_er.png`: diagramas actualizados.
- `docs/normalizacion.md` y `docs/normalizacion_datos/`: desarrollo y datos de 1FN, 2FN y 3FN.
- `docker-compose.yml`: servicio PostgreSQL 18; `.env.example`: plantilla de variables.

## Preparación y arranque

En Ubuntu/WSL, desde esta carpeta, con Docker y Compose instalados:

```bash
cp .env.example .env
docker compose up -d
docker compose logs postgres
docker compose exec postgres psql -U admin -d spotify -f /tests.sql
```

`.env` contiene `POSTGRES_USER`, `POSTGRES_PASSWORD` y `POSTGRES_DB`. El ejemplo usa `admin`, una contraseña de práctica y `spotify`. Es local, no lo subas a Git. La contraseña de `.env.example` es un marcador de ejemplo, no una credencial real. Si cambias el usuario o el nombre de la base, ajusta `-U` y `-d` en el comando.

La primera inicialización puede tardar unos segundos. Revisa que los logs digan que PostgreSQL está listo y que no haya errores del esquema o seed. Los scripts en `db/` se ejecutan automáticamente solo cuando el volumen está vacío. Después de cambiar el SQL de inicialización, para reconstruir desde cero:

```bash
docker compose down -v
docker compose up -d
```

`down -v` elimina todos los datos del volumen de **este proyecto**. `docker compose down` sin `-v` conserva los datos. Comprueba primero que estás en la carpeta correcta.

Antes de entregar, sube todos los archivos, clona el repositorio en otra carpeta, crea allí el `.env`, inicia con un volumen nuevo y ejecuta las pruebas. Comprueba también que `.env` no esté en el repositorio ni en el historial.

## Cómo leer las pruebas

Se muestran las respuestas a Laura y se verifican los resultados de la muestra. Los bloques de restricciones atrapan las violaciones esperadas y fallan si una operación inválida se acepta. Para mostrar un error real a mitad de cada transacción, `tests.sql` deja continuar psql en dos líneas: **es normal ver dos mensajes `ERROR`**, uno por perfil sin nombre y otro por división entre cero. Después se hace `ROLLBACK` y se comprueba el estado. Cualquier otro error, o que falten las verificaciones finales, requiere revisión.

No hay datos de reproducciones: la pregunta de la canción más escuchada queda documentada como no respondible. Pertenecer a una playlist o biblioteca no demuestra una escucha.

## Decisiones y supuestos

- El diseño parte del diagrama conceptual previo y lo amplía con `countries` y `genres` para evitar repetir dependencias transitivas. `profiles` y `libraries` usan la PK del suscriptor como PK y FK: cada cuenta tiene una de cada una.
- La unicidad y FK aseguran como máximo un perfil y una biblioteca. Triggers diferidos garantizan el mínimo al final de la transacción, permitiendo crear o eliminar explícitamente los tres registros juntos. Los mínimos de un artista por canción y una canción por álbum también se verifican al terminar la transacción; son supuestos del modelo conceptual anterior.
- Cada suscriptor tiene un único plan actual. Los precios son MXN mensuales, sin historial de cambios.
- El plan adicional `Estudiante` y el artista `A11` son ficticios para probar relaciones vacías. Los ID A1–A10, 101–108, 201–206 y 10–14 se conservan; los ID internos de suscriptor, género y plan se asignaron para este proyecto.
- El orden de la playlist y de cada álbum se conserva con `position` y `track_number`. Se asume que una canción no se repite dentro de la misma playlist o álbum y que sus posiciones no se repiten. Las fechas de inclusión se registran tal como las suministró Laura.
- El perfil puede no tener foto. Un álbum puede no tener artista publicador; los créditos de las canciones son independientes. Cada playlist tiene un único propietario, y las bibliotecas pueden estar vacías.
- No se almacena historial de suscripciones ni reproducción; tampoco se modelan las playlists colaborativas o las disqueras. La eliminación del suscriptor borra explícitamente sus dependencias y no elimina artistas, canciones o álbumes.

## Alcance de la validación

El esquema, el seed, las consultas, las restricciones y los casos de transacción se ejecutaron en PostgreSQL 17 local y en PostgreSQL 18.6 mediante Docker Compose. Para la prueba final de Docker se utilizó un clon limpio de GitHub y un volumen nuevo: la inicialización no presentó errores, las verificaciones terminaron correctamente y los dos errores señalados en las pruebas fueron intencionales.
