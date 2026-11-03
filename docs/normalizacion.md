# Normalización de las muestras de Laura

Cada CSV de `normalizacion_datos/` contiene los **datos reales de la etapa**, una fila de encabezados y una fila por tupla. Prefijos `1fn_`, `2fn_` y `3fn_` identifican la etapa. Los archivos 3FN contienen el catálogo completo cargado desde `db/02_seed.sql`; también incluyen el plan y el artista adicionales, señalados en el README. La muestra original no incluye esos dos casos adicionales. En CSV, un campo vacío en `photo` representa NULL en la muestra.

## Supuestos y criterios

- Un título no es clave. Se conservan los identificadores originales de canciones, artistas, álbumes y playlists. Email identifica al suscriptor de la muestra; el modelo final introduce `subscriber_id` interno.
- Una canción no se repite dentro de la misma playlist o álbum; cada posición es única dentro de la playlist y cada número de pista dentro del álbum. Es un supuesto explícito, pendiente de confirmación.
- Código de país determina nombre de país. Una suscripción determina precio y publicidad actuales; la muestra no contiene historial. Nombre del género identifica su categoría. Duración en segundos conserva exactamente los valores originales.
- Los conjuntos opcionales se representan con relaciones separadas, no con una fila inventada con clave NULL. Así las playlists vacías y bibliotecas vacías conservan su fila de cabecera.
- Las dependencias funcionales listadas reflejan los supuestos del ejercicio y las claves naturales; no son hechos demostrables solo por coincidencia en un conjunto pequeño de datos.

## A. Playlists

### 1FN

Se reemplaza la lista de canciones por `A_playlists(playlist_id PK, name, created_at, email, subscription, monthly_price_mxn, has_ads)` y `A_canciones(playlist_id PK/FK, position PK, song_id, title, duration_seconds, added_at)`. La primera conserva la playlist 13 aunque no tenga canciones. Datos: `1fn_A_playlists.csv` y `1fn_A_canciones.csv`.

En la relación de canciones, `playlist_id, position → song_id, added_at`; por el supuesto de no repetición, `(playlist_id, song_id)` es otra clave candidata. `song_id → title, duration_seconds`. En la cabecera, `playlist_id → name, created_at, email`, `email → subscription` y `subscription → monthly_price_mxn, has_ads`.

### 2FN

Antes de descomponer, en el grano candidato `(playlist_id, song_id)`, `song_id → title, duration_seconds` es dependencia parcial. Separar `A_songs(song_id PK, title, duration_seconds)` y `A_playlist_song(playlist_id PK/FK, song_id PK/FK, position UQ por playlist, added_at)`. Las cabeceras y suscriptores con PK simple se presentan también separados para facilitar el modelo. Datos: cuatro CSV `2fn_A_*`.

### 3FN

Dependencias transitivas: `playlist_id → email → subscription → monthly_price_mxn, has_ads`. Se separan `playlists`, `subscribers` y `subscriptions`; los atributos de canción se consolidan con la muestra B en `songs` y `genres`. `playlist_song` conserva posición y fecha. Las PK/FK y datos finales están en los CSV 3FN correspondientes.

## B. Créditos de canciones

### 1FN

La lista de artistas se expande a `B_creditos(song_id PK, artist_id PK, title, duration_seconds, genre, artist, country_code, country, role)`. Hay una fila por crédito y los roles pertenecen a la relación. Datos: `1fn_B_creditos.csv`.

### 2FN

Antes de descomponer: `song_id → title, duration_seconds, genre` y `artist_id → artist, country_code, country` son dependencias parciales respecto a `(song_id, artist_id)`. Se separan `B_songs(song_id PK, ...)`, `B_artists(artist_id PK, ...)` y `B_artist_song(song_id PK/FK, artist_id PK/FK, role)`. Datos: tres CSV `2fn_B_*`.

### 3FN

`artist_id → country_code → country` es transitiva y se separa en `countries`. `genre_id → name` identifica el género en `genres`; `songs.genre_id` es FK. Resultado: `songs`, `genres`, `artists`, `countries` y `artist_song`; CSV `3fn_*` correspondientes. A11 se agregó únicamente para el caso de artista sin publicaciones.

## C. Álbumes

### 1FN

La lista de pistas se expande a `C_canciones_album(album_id PK, song_id PK, album, release_year, cover, artist_id, artist, track_number, song)`. `(album_id, track_number)` es una clave candidata. Datos: `1fn_C_canciones_album.csv`.

### 2FN

Antes de descomponer: `album_id → album, release_year, cover, artist_id, artist` y `song_id → song` son parciales respecto a `(album_id, song_id)`. Se obtienen `C_albums(album_id PK, ...)`, `C_songs(song_id PK, song)` y `C_album_song(album_id PK/FK, song_id PK/FK, track_number)`. Datos: tres CSV `2fn_C_*`.

### 3FN

`album_id → artist_id → artist` es transitiva; los datos del artista se consolidan en `artists`, con el país en `countries`. Los títulos de canciones se consolidan en `songs`; `album_song` conserva la posición y evita duplicarla por álbum. CSV finales `3fn_albums`, `3fn_artists`, `3fn_songs` y `3fn_album_song`.

## D. Suscriptores y biblioteca

### 1FN

`D_suscriptores(email PK, registered_at, subscription, display_name, photo, country_code, country)` tiene datos atómicos. Las listas se separan en `D_canciones(email PK/FK, song_id PK/FK)` y `D_albumes(email PK/FK, album_id PK/FK)`. Esto conserva a Marta, que tiene ambas listas vacías, sin introducir un valor falso. Datos: tres CSV `1fn_D_*`.

### 2FN

Las claves compuestas de las tablas de guardados no tienen atributos no clave; no hay dependencias parciales que extraer. La cabecera usa la clave simple `email`, por lo que está en 2FN. Sus datos sin cambios están en los tres CSV `2fn_D_*`.

### 3FN y extensión del modelo

`email → country_code → country` es transitiva y se extrae `countries`. Del conjunto A también conocemos `email → subscription → price, has_ads`; se extrae `subscriptions`. Siguiendo la entrevista, los datos se distribuyen entre `subscribers`, `profiles` y `libraries`, con `library_song` y `library_album`. La clave técnica `subscriber_id` sustituye al email como PK, manteniendo el email único. Los CSV 3FN incluyen las filas, PK y relaciones de las cinco tablas y sus catálogos; las FK se detallan en `diagrama_er.png` y en `db/01_schema.sql`.

## Correspondencia y comprobación

Todos los valores A–D están en `db/02_seed.sql`. `docs/generar_datos_normalizacion.py` reconstruye los CSV consultando la base ya cargada: requiere `psql` y las variables de conexión PostgreSQL. Los archivos exportados contienen la reproducción del desarrollo, no son necesarios para iniciar la base.
