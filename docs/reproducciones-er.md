# Tablas de reproducción

```mermaid
erDiagram
    subscribers ||--o{ subscriber_song_play : escucha
    songs ||--o{ subscriber_song_play : acumula
    songs ||--o{ song_daily_play : registra
    subscriber_song_play {
        integer subscriber_id PK,FK
        integer song_id PK,FK
        bigint num_rep
    }
    song_daily_play {
        integer song_id PK,FK
        date play_date PK
        bigint num_rep
    }
```

La primera tabla guarda conteos históricos por usuario y canción; la segunda conserva el total diario por canción en UTC. Los eventos individuales permanecen en archivos, fuera de PostgreSQL.
