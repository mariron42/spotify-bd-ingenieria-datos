import json, os
from collections import Counter
from pathlib import Path
import psycopg
expected=Counter()
for line in Path('/app/data/raw/sent.log').read_text(encoding='utf-8').splitlines():
    e=json.loads(line)
    if e['ms_played']>=30000: expected[e['song_id']]+=1
with psycopg.connect(host=os.environ['POSTGRES_HOST'], dbname=os.environ['POSTGRES_DB'], user=os.environ['POSTGRES_USER'], password=os.environ['POSTGRES_PASSWORD']) as conn:
    daily=dict(conn.execute('SELECT song_id, sum(num_rep) FROM song_daily_play GROUP BY song_id').fetchall())
    users=dict(conn.execute('SELECT song_id, sum(num_rep) FROM subscriber_song_play GROUP BY song_id').fetchall())
errors=[]
for song in sorted(set(expected)|set(daily)|set(users)):
    if expected[song]!=daily.get(song,0) or expected[song]!=users.get(song,0): errors.append(f'canción {song}: enviados={expected[song]}, diarios={daily.get(song,0)}, usuarios={users.get(song,0)}')
print('\n'.join(errors) if errors else f'OK: {sum(expected.values())} reproducciones válidas en {len(expected)} canciones')
raise SystemExit(bool(errors))
