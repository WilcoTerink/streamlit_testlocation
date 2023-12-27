import streamlit as st
from streamlit_geolocation import streamlit_geolocation
import pandas as pd
import geopandas as gpd
import numpy as np
from streamlit_folium import st_folium
import folium
from folium.plugins import Draw
import sqlalchemy
import psycopg2
import geoalchemy2
import time
from streamlit_js_eval import streamlit_js_eval
import haversine as hs
import json
from io import StringIO
#import base64
#from PIL import Image

# https://folium.streamlit.app/draw_support

myTile = "https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/grijs/EPSG:3857/{z}/{x}/{y}.png"
myTile = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
#myTile = "https://service.pdok.nl/rvo/brpgewaspercelen/wms/v1_0?request=GetCapabilities&service=WMS"
myAttr = "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"

def initDB():
    """
    Initialiseer verbinding met PostgreSQL database
    """
    db = st.secrets
    url    = f"postgresql+psycopg2://{db['username']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}"
    return sqlalchemy.create_engine(url, client_encoding='utf8')

st.title('Welkom bij de beregeningsdetector')
st.subheader('Met deze app trachten we de beregening in Nederland in kaart te brengen')
col1, col2 = st.columns([0.32, 0.68])

with col1:

    st.image("./logo-knowh2o-uk.png")

    st.text(f"Datum: {pd.Timestamp('now').date().strftime('%d %B %Y')}")
    st.text("Deze app werkt het beste\nin landscape mode")

    st.markdown("###### Doorloop onderstaande stappen:")
    st.markdown("###### 1. Bepaal je locatie", help="Check je privacy-instellingen in je telefoon om locatiebepaling toe te staan")

    location = streamlit_geolocation()
    lat = location['latitude']
    lon = location['longitude']

    if lat:

        with col2:
            # call to render Folium map in Streamlit 
            m = folium.Map(location=[lat, lon], zoom_start=16, tiles=myTile, attr=myAttr)
            Draw(export=False, draw_options={"polyline": False, "polygon": False, "rectangle": False, "circle": False, "circlemarker": False,
            "marker": {"repeatMode": False}}).add_to(m)
            icon = folium.Icon(color="green", icon="crosshairs", prefix="fa")
            myLocation = folium.Marker([lat, lon], tooltip="mijn locatie", icon=icon).add_to(m)
            
            st.caption(f"Locatie nauwkeurigheid is {location['accuracy']} m")
            st_data = st_folium(m, width=725, center=[lat, lon], zoom=30)

        # Selecteer/ markeer punt voor waarneming
        st.markdown('###### 2. Markeer maximaal 1 perceel op de kaart voor waarneming', help="Klik hiervoor eerst de 'marker' knop op de kaart onder de zoom knoppen")
        try:
            nPoints = len(st_data["all_drawings"])
            markedLocation = st_data["all_drawings"][nPoints-1]["geometry"]["coordinates"]
            # Distance check tussen gebruiken en gemarkeerd perceel
            dist = hs.haversine((lat, lon), (markedLocation[1], markedLocation[0])) * 1000
        except:
            markedLocation = False
        
        if markedLocation:
            if nPoints == 1:
                if dist <= 100:
                    # Laat rest van formulier zien zodra waarneming is gemarkeerd op kaart en voldoet aan de eisen.
                    loc_lon = markedLocation[0]
                    loc_lat = markedLocation[1]
                    st.text((loc_lat, loc_lon))

                    st.markdown('###### 3. Beantwoord de volgende vragen')

                    gewassen = ['kale grond', 'gras', 'mais', 'aardappel', 'suikerbieten', 'weet ik niet']
                    landgebruik = st.selectbox('Landgebruik/gewas?', gewassen, placeholder='weet ik niet', index=len(gewassen)-1)

                    beregening = st.toggle('Haspel en/of sproeier aanwezig op perceel?')
                    if beregening:
                        
                        beregening_actief = st.toggle('Staat de beregening nu aan?')

                        bron = st.selectbox(
                            'Wat is de bron van beregening?',
                            ['grondwater', 'oppervlaktewater', 'weet ik niet'], placeholder='weet ik niet', index=2)
                    else:
                        beregening_actief = False

                    opmerking = st.text_area("Opmerkingen:")

                    pic = st.camera_input('Foto toevoegen?')
                    if pic:
                        # st.subheader('De volgende foto wordt ge-upload')
                        # st.image(pic)
                        #st.write(pic)
                        # image test to read as bytes
                        st.write(pic)

                        # # PIL test to convert to np array
                        # img = Image.open(pic)
                        # #st.write(img)
                        # img = np.array(img)
                        # st.write(img)

                    else:
                        pic = False


                    submit = st.button('Upload waarneming')
                    if submit:
                        with st.spinner('Moment a.u.b. Uw waarneming wordt ge-upload...'):
                            # Initialize connection.
                            engine = initDB()

                            if engine:
                                # Create new db entry
                                df_new = pd.DataFrame(columns=['lon', 'lat', 'landgebruik', 'beregening', 'beregening_actief', 'bron', 'opmerking', 'geometry', 'picture'])
                                df_new.loc[0, 'lon'] = loc_lon
                                df_new.loc[0, 'lat'] = loc_lat
                                df_new.loc[0, 'geometry'] = gpd.points_from_xy(df_new.lon, df_new.lat, crs='EPSG:4326')[0]
                                if landgebruik != 'weet ik niet':
                                    df_new.loc[0, 'landgebruik'] = landgebruik
                                df_new.loc[0, 'beregening'] = beregening
                                df_new.loc[0, 'beregening_actief'] = beregening_actief
                                if beregening and (bron != 'weet ik niet'):
                                    df_new.loc[0, 'bron'] = bron
                                if len(opmerking) > 0:
                                    df_new.loc[0, 'opmerking'] = opmerking
                                # df_new.loc[0, 'lon'] = lon
                                # df_new.loc[0, 'lat'] = lat
                                # df_new.loc[0, 'geometry_user'] = gpd.points_from_xy(df_new.lon, df_new.lat, crs='EPSG:4326')[0]
                                df_new.drop(['lon', 'lat'], axis=1, inplace=True)
                                # UTC timestamp
                                df_new['timestamp'] = pd.Timestamp.utcnow()     #pd.Timestamp('now')                                
                                df_new = gpd.GeoDataFrame(df_new, geometry='geometry', crs='EPSG:4326')
                                # Add picture
                                if pic:
                                    # Decode bytes to latin1, otherwise it can't be stored in json
                                    df_new['picture'] = pic.getvalue().decode('latin1')
                                    #df_new['picture'] = base64.b64encode(pic.getvalue()) #.decode('utf-8')
                                st.write(df_new)
                                # Convert fields to suitable json format and convert df to json
                                df_new['timestamp'] = df_new['timestamp'].astype(str)                                
                                js = df_new.to_json()

                                # Create virtual file to push to NEXUS
                                myFile = StringIO()
                                myFile.write(js)
                                st.write(myFile.getvalue())
                                # Test
                                with open('mytext.json', 'w') as f:
                                    f.write(myFile.getvalue())

                                # # Get latest entry from db
                                # df_latest = pd.read_sql('select * from streamlit_test.crowd_beregening order by timestamp desc limit 3', con=engine)
                                # latest_id = 1
                                # if len(df_latest) > 0:
                                #     latest_id = int(df_latest.id.iloc[0])
                                #     if latest_id is not None:
                                #         latest_id += 1
                                # df_new.loc[0, 'id'] = latest_id
                                # df_new.to_postgis('crowd_beregening', con=engine, schema='streamlit_test', if_exists="append")
                        
                        st.success('Waarneming is ge-upload naar het beregeningsportaal. We danken u voor uw medewerking. App wordt binnen enkele seconden herladen.')
                        time.sleep(5)
                        #streamlit_js_eval(js_expressions="parent.window.location.reload()")
                else:
                    st.markdown('###### :red[Selecteer een perceel dichtbij je locatie]')
            else:
                st.markdown('###### :red[Markeer maximaal 1 locatie]')

    # Laat zonder locatie de kaart van Nederland zien
    else:
        with col2:
            lat = 52.5
            lon = 5.8
            m = folium.Map(location=[lat, lon], zoom_start=7.5, tiles=myTile, attr=myAttr)
            # call to render Folium map in Streamlit
            st_data = st_folium(m, width=725)