import logging, os, signal
from pathlib import Path
from confluent_kafka import Consumer, KafkaError
Path('/app/logs').mkdir(parents=True, exist_ok=True)
Path('/app/data/raw').mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', handlers=[logging.FileHandler('/app/logs/consumer.log'), logging.StreamHandler()])
log = logging.getLogger('consumer')
stop = False
def shutdown(*_):
    global stop
    stop = True
signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)
def main():
    consumer = Consumer({'bootstrap.servers':'kafka:9092', 'group.id':'ingestion', 'auto.offset.reset':'earliest', 'enable.auto.commit':False, 'allow.auto.create.topics':True})
    consumer.subscribe([os.environ.get('KAFKA_TOPIC','streams')])
    try:
        with open('/app/data/raw/streams.log','a',encoding='utf-8',buffering=1) as raw:
            while not stop:
                msg=consumer.poll(1)
                if msg is None: continue
                if msg.error():
                    log.warning('Kafka: %s', msg.error()); continue
                value=msg.value().decode('utf-8')
                if '\n' in value or '\r' in value:
                    log.error('Mensaje multilínea omitido; offset %s', msg.offset()); consumer.commit(message=msg, asynchronous=False); continue
                raw.write(value+'\n'); raw.flush(); os.fsync(raw.fileno())
                consumer.commit(message=msg, asynchronous=False)
                log.info('Guardado offset %s', msg.offset())
    finally: consumer.close()
if __name__ == '__main__':
    try: main()
    except Exception:
        log.exception('Error en consumidor'); raise
