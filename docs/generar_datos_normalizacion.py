"""Exporta tablas de cada etapa desde el seed. Requiere psql y una BD cargada.

Opcional: PGHOST, PGPORT, PGUSER y PGDATABASE. Ejemplo: PGPORT=55432 ...
"""
import os
from pathlib import Path
import subprocess

OUT = Path(__file__).parent / 'normalizacion_datos'
OUT.mkdir(exist_ok=True)
psql = os.environ.get('PSQL', 'psql')
queries = {
 '1fn_A_playlists': "SELECT p.playlist_id,p.name,p.created_at,s.email,sub.name AS subscription,sub.monthly_price_mxn,sub.has_ads FROM playlists p JOIN subscribers s USING(subscriber_id) JOIN subscriptions sub USING(subscription_id) ORDER BY p.playlist_id",
 '1fn_A_canciones': "SELECT ps.playlist_id,ps.position,ps.song_id,s.title,s.duration_seconds,ps.added_at FROM playlist_song ps JOIN songs s USING(song_id) ORDER BY 1,2",
 '1fn_B_creditos': "SELECT s.song_id,a.artist_id,s.title,s.duration_seconds,g.name AS genre,a.name AS artist,c.country_code,c.name AS country,x.role FROM artist_song x JOIN songs s USING(song_id) JOIN genres g USING(genre_id) JOIN artists a USING(artist_id) JOIN countries c USING(country_code) WHERE a.artist_id <> 'A11' ORDER BY s.song_id,a.artist_id",
 '1fn_C_canciones_album': "SELECT a.album_id,x.song_id,a.title AS album,a.release_year,a.cover,a.artist_id,ar.name AS artist,x.track_number,s.title AS song FROM album_song x JOIN albums a USING(album_id) LEFT JOIN artists ar USING(artist_id) JOIN songs s USING(song_id) ORDER BY a.album_id,x.track_number",
 '1fn_D_suscriptores': "SELECT s.email,s.registered_at,sub.name AS subscription,p.display_name,p.photo,c.country_code,c.name AS country FROM subscribers s JOIN subscriptions sub USING(subscription_id) JOIN profiles p USING(subscriber_id) JOIN countries c USING(country_code) ORDER BY s.subscriber_id",
 '1fn_D_canciones': "SELECT s.email,x.song_id FROM library_song x JOIN subscribers s USING(subscriber_id) ORDER BY s.subscriber_id,x.song_id",
 '1fn_D_albumes': "SELECT s.email,x.album_id FROM library_album x JOIN subscribers s USING(subscriber_id) ORDER BY s.subscriber_id,x.album_id",
 '2fn_A_playlists': "SELECT p.playlist_id,p.name,p.created_at,s.email FROM playlists p JOIN subscribers s USING(subscriber_id) ORDER BY p.playlist_id",
 '2fn_A_suscripcion_suscriptor': "SELECT DISTINCT s.email,sub.name AS subscription,sub.monthly_price_mxn,sub.has_ads FROM playlists p JOIN subscribers s USING(subscriber_id) JOIN subscriptions sub USING(subscription_id) ORDER BY s.email",
 '2fn_A_canciones': "SELECT DISTINCT s.song_id,s.title,s.duration_seconds FROM playlist_song ps JOIN songs s USING(song_id) ORDER BY s.song_id",
 '2fn_A_playlist_song': "SELECT playlist_id,position,song_id,added_at FROM playlist_song ORDER BY playlist_id,position",
 '2fn_B_songs': "SELECT s.song_id,s.title,s.duration_seconds,g.name AS genre FROM songs s JOIN genres g USING(genre_id) ORDER BY s.song_id",
 '2fn_B_artists': "SELECT a.artist_id,a.name,c.country_code,c.name AS country FROM artists a JOIN countries c USING(country_code) WHERE a.artist_id <> 'A11' ORDER BY a.artist_id",
 '2fn_B_artist_song': "SELECT song_id,artist_id,role FROM artist_song ORDER BY song_id,artist_id",
 '2fn_C_albums': "SELECT a.album_id,a.title,a.release_year,a.cover,a.artist_id,ar.name AS artist FROM albums a LEFT JOIN artists ar USING(artist_id) ORDER BY a.album_id",
 '2fn_C_songs': "SELECT DISTINCT s.song_id,s.title FROM album_song x JOIN songs s USING(song_id) ORDER BY s.song_id",
 '2fn_C_album_song': "SELECT album_id,song_id,track_number FROM album_song ORDER BY album_id,track_number",
 '2fn_D_suscriptores': "SELECT s.email,s.registered_at,sub.name AS subscription,p.display_name,p.photo,c.country_code,c.name AS country FROM subscribers s JOIN subscriptions sub USING(subscription_id) JOIN profiles p USING(subscriber_id) JOIN countries c USING(country_code) ORDER BY s.subscriber_id",
 '2fn_D_canciones': "SELECT s.email,x.song_id FROM library_song x JOIN subscribers s USING(subscriber_id) ORDER BY s.subscriber_id,x.song_id",
 '2fn_D_albumes': "SELECT s.email,x.album_id FROM library_album x JOIN subscribers s USING(subscriber_id) ORDER BY s.subscriber_id,x.album_id",
}
for table in ('countries','subscriptions','subscribers','profiles','libraries','genres','artists','songs','albums','artist_song','album_song','playlists','playlist_song','library_song','library_album'):
    queries['3fn_' + table] = 'SELECT * FROM ' + table + ' ORDER BY 1,2' if table != 'libraries' else 'SELECT * FROM libraries ORDER BY 1'

for name, query in queries.items():
    result = subprocess.run([psql, '-X', '-v', 'ON_ERROR_STOP=1', '-c', 'COPY (' + query + ') TO STDOUT WITH (FORMAT csv, HEADER true)'], check=True, capture_output=True)
    (OUT / (name + '.csv')).write_bytes(result.stdout)
print(f'{len(queries)} tablas exportadas en {OUT}')
