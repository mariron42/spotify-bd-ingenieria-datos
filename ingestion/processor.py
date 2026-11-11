import json, logging, os, sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import psycopg
Path('/app/logs').mkdir(parents=True,exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', handlers=[logging.FileHandler('/app/logs/processor.log')])
log=logging.getLogger('processor')
def main():
    raw=Path('/app/data/raw/streams.log')
    if not raw.exists():
        log.warning('Crudo aún no disponible'); return
    stats=Counter()
    with psycopg.connect(host=os.environ['POSTGRES_HOST'], dbname=os.environ['POSTGRES_DB'], user=os.environ['POSTGRES_USER'], password=os.environ['POSTGRES_PASSWORD']) as pg:
        pg.execute('SELECT pg_advisory_xact_lock(745311)')
        subscriber_ids={r[0] for r in pg.execute('SELECT subscriber_id FROM subscribers')}
        song_ids={r[0] for r in pg.execute('SELECT song_id FROM songs')}
        with sqlite3.connect('/app/data/raw/state.sqlite') as state:
            state.executescript("""CREATE TABLE IF NOT EXISTS checkpoint (id INTEGER PRIMARY KEY, pos INTEGER NOT NULL);
            INSERT OR IGNORE INTO checkpoint VALUES (1,0);
            CREATE TABLE IF NOT EXISTS seen (event_id TEXT PRIMARY KEY);
            CREATE TABLE IF NOT EXISTS users (subscriber INTEGER, song INTEGER, n INTEGER, PRIMARY KEY(subscriber,song));
            CREATE TABLE IF NOT EXISTS daily (song INTEGER, day TEXT, n INTEGER, PRIMARY KEY(song,day));""")
            pos=state.execute('SELECT pos FROM checkpoint WHERE id=1').fetchone()[0]
            if raw.stat().st_size < pos: raise RuntimeError('El crudo se redujo: se requiere restaurar el archivo original')
            with raw.open('rb') as f:
                f.seek(pos)
                while True:
                    line=f.readline()
                    if not line or not line.endswith(b'\n'): break
                    stats['leídos']+=1
                    try:
                        e=json.loads(line); eid=e['event_id']; sub=e['subscriber_id']; song=e['song_id']; ms=e['ms_played']
                        if not isinstance(eid,str) or not eid or type(sub) is not int or type(song) is not int or type(ms) is not int or ms < 0: raise ValueError('tipos')
                        timestamp=datetime.fromisoformat(e['played_at'].replace('Z','+00:00'))
                        if timestamp.utcoffset() is None or song not in song_ids or sub not in subscriber_ids: raise ValueError('referencia o fecha inválida')
                    except (ValueError,KeyError,TypeError,UnicodeDecodeError):
                        stats['inválidos']+=1; pos=f.tell(); continue
                    if state.execute('INSERT OR IGNORE INTO seen VALUES (?)',(eid,)).rowcount==0:
                        stats['duplicados']+=1; pos=f.tell(); continue
                    if ms < 30000: stats['skips']+=1; pos=f.tell(); continue
                    day=timestamp.astimezone(timezone.utc).date().isoformat()
                    state.execute('INSERT INTO users VALUES (?,?,1) ON CONFLICT(subscriber,song) DO UPDATE SET n=n+1',(sub,song))
                    state.execute('INSERT INTO daily VALUES (?,?,1) ON CONFLICT(song,day) DO UPDATE SET n=n+1',(song,day))
                    stats['válidos']+=1; pos=f.tell()
            state.execute('UPDATE checkpoint SET pos=? WHERE id=1',(pos,))
            state.commit()
            # Tras un fallo, SQLite conserva los agregados y la siguiente corrida los vuelve a publicar.
            users=[(a,b,n) for a,b,n in state.execute('SELECT subscriber,song,n FROM users') if a in subscriber_ids and b in song_ids]
            daily=[(a,b,n) for a,b,n in state.execute('SELECT song,day,n FROM daily') if a in song_ids]
            pg.execute('DELETE FROM subscriber_song_play'); pg.execute('DELETE FROM song_daily_play')
            with pg.cursor() as cur:
                cur.executemany('INSERT INTO subscriber_song_play VALUES (%s,%s,%s)',users)
                cur.executemany('INSERT INTO song_daily_play VALUES (%s,%s,%s)',daily)
    log.info('Corrida incremental: %s', dict(stats))
if __name__ == '__main__':
    try: main()
    except Exception:
        log.exception('Falló procesamiento'); raise
