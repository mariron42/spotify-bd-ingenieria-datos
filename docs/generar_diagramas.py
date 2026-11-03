"""Genera los dos diagramas PNG con Pillow; no es necesario para ejecutar SQL."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent
font_path = 'C:/Windows/Fonts/arial.ttf'
bold_path = 'C:/Windows/Fonts/arialbd.ttf'
def font(n, bold=False):
    return ImageFont.truetype(bold_path if bold else font_path, n)

relations = [
 ('subscriptions','agrupa','subscribers','1..1','0..N'),
 ('subscribers','tiene','profiles','1..1','1..1'),
 ('subscribers','posee','libraries','1..1','1..1'),
 ('subscribers','crea','playlists','1..1','0..N'),
 ('libraries','registra','library_album','1..1','0..N'),
 ('albums','referencia','library_album','1..1','0..N'),
 ('libraries','registra','library_song','1..1','0..N'),
 ('songs','referencia','library_song','1..1','0..N'),
 ('playlists','incluye','playlist_song','1..1','0..N'),
 ('songs','referencia','playlist_song','1..1','0..N'),
 ('albums','contiene','album_song','1..1','1..N'),
 ('songs','aparece en','album_song','1..1','0..N'),
 ('artists','participa en','artist_song','1..1','0..N'),
 ('songs','acredita','artist_song','1..1','1..N'),
 ('artists','publica','albums','0..1','0..N'),
 ('countries','ubica','profiles','1..1','0..N'),
 ('countries','ubica','artists','1..1','0..N'),
 ('genres','clasifica','songs','1..1','0..N'),
]
fields = {
 'countries':['country_code char(2) PK','name varchar(100) UQ'],
 'subscriptions':['subscription_id integer PK','name varchar(100) UQ','monthly_price_mxn numeric(8,2)','has_ads boolean'],
 'subscribers':['subscriber_id integer PK','email varchar(255) UQ','registered_at date','subscription_id integer FK'],
 'profiles':['subscriber_id integer PK, FK','display_name varchar(100)','photo varchar(255) NULL','country_code char(2) FK'],
 'libraries':['subscriber_id integer PK, FK'],
 'artists':['artist_id varchar(10) PK','name varchar(150)','country_code char(2) FK'],
 'genres':['genre_id integer PK','name varchar(100) UQ'],
 'songs':['song_id integer PK','title varchar(200)','duration_seconds integer','genre_id integer FK'],
 'albums':['album_id integer PK','title varchar(200)','release_year integer','cover varchar(255)','artist_id varchar(10) FK NULL'],
 'playlists':['playlist_id integer PK','subscriber_id integer FK','name varchar(200)','created_at date'],
 'artist_song':['artist_id varchar(10) PK, FK','song_id integer PK, FK','role varchar(20)'],
 'album_song':['album_id integer PK, FK','song_id integer PK, FK','track_number integer; UQ por álbum'],
 'playlist_song':['playlist_id integer PK, FK','song_id integer PK, FK','position integer; UQ por playlist','added_at date'],
 'library_song':['subscriber_id integer PK, FK','song_id integer PK, FK'],
 'library_album':['subscriber_id integer PK, FK','album_id integer PK, FK'],
}
def card_symbol(d,x,y,card,direction):
    # End labels give the exact cardinality; lines show crow's-foot notation.
    side = 1 if direction == 'right' else -1
    mn,mx=card.split('..')
    if mn=='0':
        cx=x+side*35
        d.ellipse((cx-7,y-7,cx+7,y+7),outline='#18372b',width=3)
    else:
        xx=x+side*35; d.line((xx,y-13,xx,y+13),fill='#18372b',width=3)
    if mx=='N':
        xx=x+side*14
        d.line((x,y,xx,y-15),fill='#18372b',width=3)
        d.line((x,y,xx,y),fill='#18372b',width=3)
        d.line((x,y,xx,y+15),fill='#18372b',width=3)
    else:
        xx=x+side*14; d.line((xx,y-13,xx,y+13),fill='#18372b',width=3)

def make(conceptual):
    width=2400; top=240; row_h=90; rel_h=len(relations)*row_h
    extra=0 if conceptual else 1540
    image=Image.new('RGB',(width,top+rel_h+extra+190),'#f7faf8')
    d=ImageDraw.Draw(image)
    d.rectangle((0,0,width,160),fill='#163c2d')
    title='Modelo conceptual de Spotify' if conceptual else 'Diagrama entidad-relación de Spotify'
    d.text((70,30),title,font=font(58,True),fill='white')
    d.text((72,100),'Cardinalidad en cada extremo: cantidad de esa entidad por instancia del extremo opuesto.',font=font(27),fill='#dcf5e6')
    d.text((72,177),'Entidades repetidas por relación para facilitar la lectura · círculo = 0 · barra = 1 · pata = N',font=font(27),fill='#203e31')
    for i,(left,verb,right,lcard,rcard) in enumerate(relations):
        y=top+i*row_h
        d.rounded_rectangle((60,y,750,y+70),12,fill='#e0f2e6',outline='#6b9f7f',width=2)
        d.rounded_rectangle((1650,y,2340,y+70),12,fill='#e0f2e6',outline='#6b9f7f',width=2)
        d.text((85,y+17),left,font=font(30,True),fill='#123c2a')
        d.text((1675,y+17),right,font=font(30,True),fill='#123c2a')
        cy=y+35
        d.line((750,cy,1650,cy),fill='#18372b',width=3)
        card_symbol(d,750,cy,lcard,'right'); card_symbol(d,1650,cy,rcard,'left')
        d.rounded_rectangle((1030,y+7,1370,y+63),9,fill='#f7faf8')
        box=d.textbbox((0,0),verb,font=font(25)); d.text((1200-(box[2]-box[0])/2,y+20),verb,font=font(25),fill='#244a37')
        d.text((810,y-2),lcard,font=font(23),fill='#244a37')
        d.text((1515,y-2),rcard,font=font(23),fill='#244a37')
    if not conceptual:
        y0=top+rel_h+40
        d.text((70,y0),'Atributos y claves',font=font(45,True),fill='#163c2d')
        d.text((70,y0+60),'PK: primaria · FK: foránea · UQ: única · los atributos son NOT NULL salvo los marcados NULL',font=font(26),fill='#203e31')
        items=list(fields.items())
        cols=3; card_w=740; card_h=250
        for i,(name,cols_data) in enumerate(items):
            col=i%cols; row=i//cols; x=70+col*760; y=y0+110+row*260
            d.rounded_rectangle((x,y,x+card_w,y+card_h-10),14,fill='white',outline='#93b7a0',width=2)
            d.rounded_rectangle((x,y,x+card_w,y+46),12,fill='#2d6e4e')
            d.text((x+14,y+6),name,font=font(29,True),fill='white')
            for j,line in enumerate(cols_data): d.text((x+16,y+54+j*34),line,font=font(24),fill='#1d3428')
    d.text((70,image.height-85),'Basado en la entrevista y los datos de Laura; diferencias y supuestos en README.md.',font=font(24),fill='#365242')
    image.save(OUT/('diagrama_conceptual.png' if conceptual else 'diagrama_er.png'),optimize=True)

make(True)
make(False)
