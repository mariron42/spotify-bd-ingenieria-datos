-- Datos de las tablas A-D, más un plan y un artista sin relaciones.
BEGIN;
INSERT INTO countries VALUES ('MX','México'),('US','Estados Unidos'),('CO','Colombia'),('AR','Argentina'),('PR','Puerto Rico');
INSERT INTO subscriptions VALUES (1,'Gratuita',0,true),(2,'Premium',129,false),(3,'Familiar',199,false),(4,'Estudiante',79,false);
INSERT INTO subscribers (subscriber_id,email,registered_at,subscription_id) VALUES
 (1,'ana@mail.com','2025-11-02',2),(2,'luis@mail.com','2026-01-15',1),
 (3,'marta@mail.com','2026-05-20',3),(4,'diego@mail.com','2026-09-01',3);
SELECT setval(pg_get_serial_sequence('subscribers','subscriber_id'), 4, true);
INSERT INTO profiles VALUES (1,'anaruiz','a1.jpg','MX'),(2,'luis.s','l2.jpg','MX'),(3,'marta_g',NULL,'AR'),(4,'diegol','d4.jpg','MX');
INSERT INTO libraries VALUES (1),(2),(3),(4);
INSERT INTO genres VALUES (1,'Regional mexicano'),(2,'Reguetón'),(3,'Pop latino'),(4,'Pop'),(5,'R&B');
INSERT INTO artists VALUES
 ('A1','Karol G','CO'),('A2','Shakira','CO'),('A3','Miley Cyrus','US'),('A4','SZA','US'),
 ('A5','Bizarrap','AR'),('A6','Eslabon Armado','US'),('A7','Peso Pluma','MX'),
 ('A8','Bad Bunny','PR'),('A9','Chencho Corleone','PR'),('A10','Los del Pitic','MX'),
 ('A11','Artista sin lanzamientos','MX');
INSERT INTO songs VALUES
 (101,'Ella Baila Sola',165,1),(102,'TQG',197,2),(103,'Bzrp Music Sessions #53',213,3),
 (104,'Flowers',200,4),(105,'Kill Bill',153,5),(106,'Tití Me Preguntó',243,2),
 (107,'Me Porto Bonito',178,2),(108,'Calor de Agosto',185,1);
INSERT INTO artist_song VALUES
 ('A6',101,'principal'),('A7',101,'feat.'),('A1',102,'principal'),('A2',102,'feat.'),
 ('A5',103,'principal'),('A2',103,'feat.'),('A3',104,'principal'),('A4',105,'principal'),
 ('A8',106,'principal'),('A8',107,'principal'),('A9',107,'feat.'),('A10',108,'principal');
INSERT INTO albums VALUES
 (201,'Desvelado',2023,'desvelado.jpg','A6'),(202,'Mañana Será Bonito',2023,'msb.jpg','A1'),
 (203,'Endless Summer Vacation',2023,'esv.jpg','A3'),(204,'SOS',2022,'sos.jpg','A4'),
 (205,'Un Verano Sin Ti',2022,'uvst.jpg','A8'),(206,'Las Mujeres Ya No Lloran',2024,'lmynl.jpg','A2');
INSERT INTO album_song VALUES (201,101,6),(202,102,6),(203,104,1),(204,105,2),(205,107,3),(205,106,4),(206,103,11),(206,102,12);
INSERT INTO playlists VALUES
 (10,1,'Gym','2026-03-01'),(11,1,'Para estudiar','2026-04-10'),
 (12,2,'Gym','2026-05-02'),(13,3,'Viaje','2026-06-15'),(14,2,'Favoritas','2026-06-20');
INSERT INTO playlist_song VALUES
 (10,101,1,'2026-03-01'),(10,102,2,'2026-03-01'),(10,103,3,'2026-03-04'),
 (11,104,1,'2026-04-10'),(11,101,2,'2026-04-12'),
 (12,102,1,'2026-05-02'),(12,105,2,'2026-05-02'),
 (14,103,1,'2026-06-20'),(14,104,2,'2026-06-21'),(14,102,3,'2026-06-22');
INSERT INTO library_song VALUES (1,102),(1,104),(2,103),(4,101),(4,108);
INSERT INTO library_album VALUES (1,205),(2,204),(2,206);
COMMIT;
