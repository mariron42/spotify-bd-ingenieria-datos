-- Ejecutar con psql; las operaciones inválidas se capturan y se comprueban.
\set ON_ERROR_STOP on
\echo '1. Playlist 10: canciones y artistas en orden'
SELECT ps.position, s.song_id, s.title,
       string_agg(a.name || ' (' || x.role || ')', ', ' ORDER BY CASE x.role WHEN 'principal' THEN 0 ELSE 1 END, a.name) AS artists
FROM playlist_song ps JOIN songs s USING(song_id)
JOIN artist_song x USING(song_id) JOIN artists a USING(artist_id)
WHERE ps.playlist_id = 10 GROUP BY ps.position, s.song_id, s.title ORDER BY ps.position;

\echo '2. Suscriptores por plan, incluidos los planes vacíos'
SELECT p.name, count(s.subscriber_id) AS subscribers
FROM subscriptions p LEFT JOIN subscribers s USING(subscription_id)
GROUP BY p.subscription_id, p.name ORDER BY p.subscription_id;

\echo '3. Canciones sin álbum'
SELECT s.song_id, s.title FROM songs s
WHERE NOT EXISTS (SELECT 1 FROM album_song x WHERE x.song_id = s.song_id)
ORDER BY s.song_id;

\echo '4. Contenido de todas las bibliotecas (incluso vacías)'
SELECT s.email, 'canción' AS kind, so.song_id AS item_id, so.title
FROM subscribers s JOIN library_song ls USING(subscriber_id) JOIN songs so USING(song_id)
UNION ALL
SELECT s.email, 'álbum', a.album_id, a.title
FROM subscribers s JOIN library_album la USING(subscriber_id) JOIN albums a USING(album_id)
UNION ALL
SELECT s.email, 'vacía', NULL::integer, NULL::varchar
FROM subscribers s WHERE NOT EXISTS (SELECT 1 FROM library_song ls WHERE ls.subscriber_id=s.subscriber_id)
AND NOT EXISTS (SELECT 1 FROM library_album la WHERE la.subscriber_id=s.subscriber_id)
ORDER BY 1,2,3;

\echo '5. Canción más escuchada históricamente'
SELECT s.song_id, s.title, sum(d.num_rep) AS reproducciones
FROM songs s JOIN song_daily_play d USING (song_id)
GROUP BY s.song_id, s.title ORDER BY reproducciones DESC, s.song_id LIMIT 1;

\echo 'Top 100 de la última semana completa (UTC)'
SELECT s.song_id, s.title, sum(d.num_rep) AS reproducciones
FROM song_daily_play d JOIN songs s USING (song_id)
WHERE d.play_date >= (date_trunc('week', now() AT TIME ZONE 'UTC')::date - 7)
  AND d.play_date < date_trunc('week', now() AT TIME ZONE 'UTC')::date
GROUP BY s.song_id, s.title ORDER BY reproducciones DESC, s.song_id LIMIT 100;

\echo 'Las 20 canciones más escuchadas del suscriptor 1'
SELECT s.song_id, s.title, p.num_rep FROM subscriber_song_play p
JOIN songs s USING (song_id) WHERE p.subscriber_id = 1
ORDER BY p.num_rep DESC, s.song_id LIMIT 20;


\echo 'Verificación de los datos y resultados esperados'
DO $$ BEGIN
 IF (SELECT count(*) FROM songs) <> 8 OR (SELECT count(*) FROM albums) <> 6 OR
    (SELECT count(*) FROM subscribers) <> 4 OR (SELECT count(*) FROM playlists) <> 5 THEN
   RAISE EXCEPTION 'Faltan registros de Laura'; END IF;
 IF (SELECT array_agg(song_id ORDER BY position) FROM playlist_song WHERE playlist_id=10) <> ARRAY[101,102,103] THEN
   RAISE EXCEPTION 'Orden incorrecto de playlist 10'; END IF;
 IF (SELECT count(*) FROM subscribers WHERE subscription_id=1) <> 1 OR
    (SELECT count(*) FROM subscribers WHERE subscription_id=2) <> 1 OR
    (SELECT count(*) FROM subscribers WHERE subscription_id=3) <> 2 OR
    (SELECT count(*) FROM subscribers WHERE subscription_id=4) <> 0 THEN
   RAISE EXCEPTION 'Conteos por suscripción incorrectos'; END IF;
 IF (SELECT array_agg(song_id ORDER BY song_id) FROM songs s WHERE NOT EXISTS
     (SELECT 1 FROM album_song x WHERE x.song_id=s.song_id)) <> ARRAY[108] THEN
   RAISE EXCEPTION 'Canciones sin álbum incorrectas'; END IF;
 IF (SELECT count(*) FROM library_song) <> 5 OR (SELECT count(*) FROM library_album) <> 3 OR
    (SELECT count(*) FROM artist_song) <> 12 OR (SELECT count(*) FROM album_song) <> 8 OR
    (SELECT count(*) FROM playlist_song) <> 10 THEN
   RAISE EXCEPTION 'Faltan relaciones de las muestras'; END IF;
 IF NOT EXISTS (SELECT 1 FROM artists a WHERE a.artist_id='A11' AND NOT EXISTS
   (SELECT 1 FROM artist_song x WHERE x.artist_id=a.artist_id) AND NOT EXISTS
   (SELECT 1 FROM albums b WHERE b.artist_id=a.artist_id)) OR EXISTS
   (SELECT 1 FROM playlist_song WHERE playlist_id=13) THEN
   RAISE EXCEPTION 'Faltan casos límite'; END IF;
 RAISE NOTICE 'Datos y consultas verificadas';
END $$;

\echo 'Restricciones: se intenta romper cada tipo y se exige el rechazo'
DO $$ BEGIN
 -- PK: no se puede repetir el identificador de un plan.
 BEGIN INSERT INTO subscriptions VALUES(1,'Otro',1,false); RAISE EXCEPTION 'PK no se rechazó';
 EXCEPTION WHEN unique_violation THEN RAISE NOTICE 'PK rechazada'; END;
 -- UNIQUE: el email identifica como máximo un suscriptor.
 BEGIN INSERT INTO subscribers(email,registered_at,subscription_id) VALUES('ana@mail.com','2026-01-01',1); RAISE EXCEPTION 'UNIQUE no se rechazó';
 EXCEPTION WHEN unique_violation THEN RAISE NOTICE 'UNIQUE rechazada'; END;
 -- NOT NULL: cada suscriptor tiene email.
 BEGIN INSERT INTO subscribers(email,registered_at,subscription_id) VALUES(NULL,'2026-01-01',1); RAISE EXCEPTION 'NOT NULL no se rechazó';
 EXCEPTION WHEN not_null_violation THEN RAISE NOTICE 'NOT NULL rechazado'; END;
 -- FK: no se puede asignar un plan inexistente.
 BEGIN INSERT INTO subscribers(email,registered_at,subscription_id) VALUES('fk-test@example.test','2026-01-01',99999); RAISE EXCEPTION 'FK no se rechazó';
 EXCEPTION WHEN foreign_key_violation THEN RAISE NOTICE 'FK rechazada'; END;
 -- CHECK: la duración debe ser positiva.
 BEGIN INSERT INTO songs VALUES (99999,'Inválida',0,1); RAISE EXCEPTION 'CHECK no se rechazó';
 EXCEPTION WHEN check_violation THEN RAISE NOTICE 'CHECK rechazado'; END;
 -- Restricción diferida: una cuenta no puede quedar sin perfil y biblioteca.
 BEGIN
   INSERT INTO subscribers(subscriber_id,email,registered_at,subscription_id) VALUES(99999,'incompleto@example.test','2026-01-01',1);
   SET CONSTRAINTS ALL IMMEDIATE;
   RAISE EXCEPTION 'Cuenta incompleta no se rechazó';
 EXCEPTION WHEN check_violation THEN RAISE NOTICE 'Cuenta incompleta rechazada'; END;
 -- Restricción diferida: no se puede dejar una canción sin artista.
 BEGIN
   INSERT INTO songs VALUES (99999,'Sin artista',100,1);
   SET CONSTRAINTS ALL IMMEDIATE;
   RAISE EXCEPTION 'Canción sin artista no se rechazó';
 EXCEPTION WHEN check_violation THEN RAISE NOTICE 'Canción sin artista rechazada'; END;
 -- Restricción diferida: no se puede dejar un álbum sin canciones.
 BEGIN
   INSERT INTO albums VALUES (99999,'Vacío',2026,'cover.jpg',NULL);
   SET CONSTRAINTS ALL IMMEDIATE;
   RAISE EXCEPTION 'Álbum vacío no se rechazó';
 EXCEPTION WHEN check_violation THEN RAISE NOTICE 'Álbum vacío rechazado'; END;
END $$;

\echo 'Registro exitoso: transacción completa'
BEGIN;
INSERT INTO subscribers(subscriber_id,email,registered_at,subscription_id) VALUES(900001,'prueba-transaccion@example.test','2026-01-01',1);
INSERT INTO profiles VALUES(900001,'Prueba',NULL,'MX');
INSERT INTO libraries VALUES(900001);
INSERT INTO playlists VALUES(900001,900001,'Prueba','2026-01-01');
INSERT INTO playlist_song VALUES(900001,101,1,'2026-01-01');
INSERT INTO library_song VALUES(900001,101);
INSERT INTO library_album VALUES(900001,201);
COMMIT;
DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM subscribers s JOIN profiles p USING(subscriber_id)
 JOIN libraries l USING(subscriber_id) WHERE s.subscriber_id=900001) THEN RAISE EXCEPTION 'Registro falló'; END IF; END $$;

\echo 'Registro fallido: error intermedio seguido de rollback'
BEGIN;
INSERT INTO subscribers(subscriber_id,email,registered_at,subscription_id) VALUES(900002,'fallo-registro@example.test','2026-01-01',1);
\set ON_ERROR_STOP off
INSERT INTO profiles VALUES(900002,NULL,NULL,'MX'); -- NOT NULL intencional
\set ON_ERROR_STOP on
ROLLBACK;
DO $$ BEGIN IF EXISTS (SELECT 1 FROM subscribers WHERE subscriber_id=900002) OR
 EXISTS (SELECT 1 FROM profiles WHERE subscriber_id=900002) OR
 EXISTS (SELECT 1 FROM libraries WHERE subscriber_id=900002) THEN RAISE EXCEPTION 'Rollback del registro falló'; END IF; END $$;
SELECT count(*) AS registros_residuales_esperados_cero FROM subscribers WHERE subscriber_id=900002;

\echo 'Eliminación fallida: se borran dependencias, se produce un error y se revierte todo'
CREATE TEMP TABLE before_delete AS
 SELECT (SELECT count(*) FROM subscribers WHERE subscriber_id=900001) AS subscriber_count,
        (SELECT count(*) FROM profiles WHERE subscriber_id=900001) AS profile_count,
        (SELECT count(*) FROM libraries WHERE subscriber_id=900001) AS library_count,
        (SELECT count(*) FROM library_song WHERE subscriber_id=900001) AS saved_songs,
        (SELECT count(*) FROM library_album WHERE subscriber_id=900001) AS saved_albums,
        (SELECT count(*) FROM playlists WHERE subscriber_id=900001) AS playlist_count,
        (SELECT count(*) FROM playlist_song WHERE playlist_id=900001) AS playlist_songs;
BEGIN;
DELETE FROM subscriber_song_play WHERE subscriber_id=900001;
DELETE FROM playlist_song WHERE playlist_id IN (SELECT playlist_id FROM playlists WHERE subscriber_id=900001);
DELETE FROM playlists WHERE subscriber_id=900001;
DELETE FROM library_song WHERE subscriber_id=900001;
DELETE FROM library_album WHERE subscriber_id=900001;
DELETE FROM libraries WHERE subscriber_id=900001;
\set ON_ERROR_STOP off
SELECT 1 / 0; -- fallo intencional a medio camino
\set ON_ERROR_STOP on
ROLLBACK;
DO $$ DECLARE actual record; expected record; BEGIN
 SELECT * INTO expected FROM before_delete;
 SELECT (SELECT count(*) FROM subscribers WHERE subscriber_id=900001),
        (SELECT count(*) FROM profiles WHERE subscriber_id=900001),
        (SELECT count(*) FROM libraries WHERE subscriber_id=900001),
        (SELECT count(*) FROM library_song WHERE subscriber_id=900001),
        (SELECT count(*) FROM library_album WHERE subscriber_id=900001),
        (SELECT count(*) FROM playlists WHERE subscriber_id=900001),
        (SELECT count(*) FROM playlist_song WHERE playlist_id=900001) INTO actual;
 IF actual IS DISTINCT FROM expected THEN RAISE EXCEPTION 'Rollback de eliminación falló'; END IF;
END $$;
SELECT 'antes' AS estado, * FROM before_delete
UNION ALL SELECT 'después', (SELECT count(*) FROM subscribers WHERE subscriber_id=900001),
 (SELECT count(*) FROM profiles WHERE subscriber_id=900001),(SELECT count(*) FROM libraries WHERE subscriber_id=900001),
 (SELECT count(*) FROM library_song WHERE subscriber_id=900001),(SELECT count(*) FROM library_album WHERE subscriber_id=900001),
 (SELECT count(*) FROM playlists WHERE subscriber_id=900001),(SELECT count(*) FROM playlist_song WHERE playlist_id=900001);

\echo 'Eliminación exitosa y explícita; el catálogo debe conservarse'
CREATE TEMP TABLE before_catalog AS SELECT (SELECT count(*) FROM songs) AS songs,
 (SELECT count(*) FROM albums) AS albums, (SELECT count(*) FROM artists) AS artists;
BEGIN;
DELETE FROM subscriber_song_play WHERE subscriber_id=900001;
DELETE FROM playlist_song WHERE playlist_id IN (SELECT playlist_id FROM playlists WHERE subscriber_id=900001);
DELETE FROM playlists WHERE subscriber_id=900001;
DELETE FROM library_song WHERE subscriber_id=900001;
DELETE FROM library_album WHERE subscriber_id=900001;
DELETE FROM libraries WHERE subscriber_id=900001;
DELETE FROM profiles WHERE subscriber_id=900001;
-- song_daily_play conserva el historial agregado; el top semanal no cambia.
DELETE FROM subscribers WHERE subscriber_id=900001;
COMMIT;
DO $$ BEGIN
 IF EXISTS (SELECT 1 FROM subscribers WHERE subscriber_id=900001) OR
    EXISTS (SELECT 1 FROM profiles WHERE subscriber_id=900001) OR
    EXISTS (SELECT 1 FROM libraries WHERE subscriber_id=900001) OR
    EXISTS (SELECT 1 FROM playlists WHERE subscriber_id=900001) OR
    EXISTS (SELECT 1 FROM playlist_song WHERE playlist_id=900001) THEN RAISE EXCEPTION 'Eliminación incompleta'; END IF;
 IF (SELECT ROW((SELECT count(*) FROM songs),(SELECT count(*) FROM albums),(SELECT count(*) FROM artists)))
    IS DISTINCT FROM (SELECT ROW(songs,albums,artists) FROM before_catalog) THEN RAISE EXCEPTION 'Cambió el catálogo'; END IF;
 RAISE NOTICE 'Eliminación y catálogo verificados';
END $$;
\echo 'FIN: las dos líneas ERROR anteriores son intencionales; todas las verificaciones posteriores deben pasar.'
