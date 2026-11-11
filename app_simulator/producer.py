import heapq, json, logging, os, random, signal, time, uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
import psycopg
from confluent_kafka import Producer

Path('/app/logs').mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', handlers=[logging.FileHandler('/app/logs/producer.log'), logging.StreamHandler()])
log = logging.getLogger('producer')
stop = False
def shutdown(*_):
    global stop
    stop = True
signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

def main():
    interval = float(os.environ['INTERVAL_SECONDS'])
    skip, duplicate = float(os.environ['SKIP_RATE']), float(os.environ['DUPLICATE_RATE'])
    delay, age = int(os.environ['MAX_DUPLICATE_DELAY_SECONDS']), int(os.environ['MAX_PLAY_AGE_DAYS'])
    if interval <= 0 or not (0 <= skip <= 1 and 0 <= duplicate <= 1 and 0 <= delay <= 300 and age > 0):
        raise ValueError('Configuración inválida')
    with psycopg.connect(host=os.environ['POSTGRES_HOST'], dbname=os.environ['POSTGRES_DB'], user=os.environ['POSTGRES_USER'], password=os.environ['POSTGRES_PASSWORD']) as conn:
        subscribers = [r[0] for r in conn.execute('SELECT subscriber_id FROM subscribers')]
        songs = [r[0] for r in conn.execute('SELECT song_id FROM songs')]
    if not subscribers or not songs:
        raise ValueError('Se necesitan suscriptores y canciones en la base')
    kafka = Producer({'bootstrap.servers': 'kafka:9092', 'message.timeout.ms': 30000})
    pending = []
    Path('/app/data/raw').mkdir(parents=True, exist_ok=True)
    def send(payload):
        outcome = []
        kafka.produce(os.environ.get('KAFKA_TOPIC', 'streams'), payload.encode(), on_delivery=lambda err, msg: outcome.append(err))
        kafka.flush(35)
        if not outcome or outcome[0]:
            raise RuntimeError(f'Kafka no confirmó el envío: {outcome}')
    with open('/app/data/raw/sent.log', 'a', encoding='utf-8', buffering=1) as sent:
        next_send = time.monotonic()
        while not stop:
            now = time.monotonic()
            while pending and pending[0][0] <= now:
                _, _, payload = heapq.heappop(pending)
                send(payload)
                log.info('Duplicado enviado: %s', payload)
            if now >= next_send:
                event = {'event_id': str(uuid.uuid4()), 'subscriber_id': random.choice(subscribers), 'song_id': random.choice(songs), 'played_at': (datetime.now(timezone.utc) - timedelta(seconds=random.uniform(0, age*86400))).isoformat(), 'ms_played': random.randint(0,29999) if random.random() < skip else random.randint(30000,240000)}
                payload = json.dumps(event, separators=(',', ':'))
                send(payload)
                sent.write(payload+'\n'); sent.flush(); os.fsync(sent.fileno())
                log.info('Enviado: %s', payload)
                if random.random() < duplicate:
                    heapq.heappush(pending, (time.monotonic()+random.uniform(0,delay), event['event_id'], payload))
                next_send = time.monotonic()+interval
            time.sleep(0.1)
    log.info('Productor detenido; %s duplicados programados no enviados', len(pending))
if __name__ == '__main__':
    try: main()
    except Exception:
        log.exception('Error en productor'); raise
