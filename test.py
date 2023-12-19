import streamlit as st
from streamlit_geolocation import streamlit_geolocation
import pandas as pd
from streamlit_folium import st_folium
import folium
import sqlalchemy
import psycopg2
import geopandas as gpd
import numpy as np
import geoalchemy2
import time
from streamlit_js_eval import streamlit_js_eval

# https://folium.streamlit.app/draw_support

myTile = "https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/grijs/EPSG:3857/{z}/{x}/{y}.png"
myTile = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
#myTile = "https://service.pdok.nl/rvo/brpgewaspercelen/wms/v1_0?request=GetCapabilities&service=WMS"
myAttr = "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"


def initDB():

    db = st.secrets.connections.postgresql
    url    = f"postgresql+psycopg2://{db['username']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}"
    return sqlalchemy.create_engine(url, client_encoding='utf8')

st.title('Welkom bij de beregeningsdetector')
col1, col2 = st.columns([0.32, 0.68])

with col1:

    # st.text("")
    # st.text("")
    # st.text("")

    st.image("./logo-knowh2o-uk.png")

    st.text(f"Datum: {pd.Timestamp('now').date().strftime('%d %B %Y')}")
    
    st.markdown("##### Doorloop onderstaande stappen")
    st.write('Bepaal je locatie')

    location = streamlit_geolocation()
    lat = location['latitude']
    lon = location['longitude']

    if lat:
        m = folium.Map(location=[lat, lon], zoom_start=16, tiles=myTile, attr=myAttr)
        myLocation = folium.Marker([lat, lon], popup="Mijn locatie").add_to(m)
        df = pd.DataFrame(data={'lat': lat, 'lon': lon}, index=[0])

        with col2:
            # call to render Folium map in Streamlit
            
            st.map(df, zoom=16, size=location['accuracy'])
            st.caption(f"Locatie nauwkeurigheid is {location['accuracy']} m")
            #st_data = st_folium(m, width=725)

        gewassen = ['kale grond', 'gras', 'mais', 'aardappel', 'suikerbieten', 'weet ik niet']
        landgebruik = st.selectbox('Landgebruik/gewas?', gewassen, placeholder='weet ik niet', index=len(gewassen)-1)

        beregening = st.toggle('Beregening?')
        if beregening:
            bron = st.selectbox(
                'Wat is de bron van beregening?',
                ['grondwater', 'oppervlaktewater', 'weet ik niet'], index=None, placeholder='maak keuze')

        opmerking = st.text_area("Opmerkingen:")

        submit = st.button('Upload waarneming')
        if submit:
            with st.spinner('Moment a.u.b. Uw waarneming wordt ge-upload...'):
                # Initialize connection.
                engine = initDB()

                if engine:
                    # Create new db entry
                    df_new = pd.DataFrame(columns=['id', 'geometry', 'lon', 'lat', 'landgebruik', 'beregend', 'opmerking', 'bron'])
                    df_new.loc[0, 'lon'] = lon
                    df_new.loc[0, 'lat'] = lat
                    df_new.loc[0, 'geometry'] = gpd.points_from_xy(df_new.lon, df_new.lat, crs='EPSG:4326')[0]
                    df_new.drop(['lon', 'lat'], axis=1, inplace=True)
                    if landgebruik != 'weet ik niet':
                        df_new.loc[0, 'landgebruik'] = landgebruik
                    df_new.loc[0, 'beregend'] = beregening
                    if beregening and (bron != 'Weet ik niet'):
                        #if bron != :
                        df_new.loc[0, 'bron'] = bron
                    if len(opmerking) > 0:
                        df_new.loc[0, 'opmerking'] = opmerking
                    df_new['timestamp'] = pd.Timestamp('now')
                    df_new = gpd.GeoDataFrame(df_new, geometry='geometry', crs='EPSG:4326')

                    # Get latest entry from db
                    df_latest = pd.read_sql('select * from streamlit_test.crowd_beregening order by timestamp desc limit 3', con=engine)
                    latest_id = 1
                    if len(df_latest) > 0:
                        latest_id = int(df_latest.id.iloc[0])
                        if latest_id is not None:
                            latest_id += 1
                    df_new.loc[0, 'id'] = latest_id
                    df_new.to_postgis('crowd_beregening', con=engine, schema='streamlit_test', if_exists="append")
            
            st.success('Waarneming is ge-upload naar het beregeningsportaal. App wordt binnen enkele seconden herladen.')

            time.sleep(4)
            streamlit_js_eval(js_expressions="parent.window.location.reload()")

    else:
        with col2:
            lat = 52.25
            lon = 5.25
            m = folium.Map(location=[lat, lon], zoom_start=8, tiles=myTile, attr=myAttr)
            # call to render Folium map in Streamlit
            st_data = st_folium(m, width=725)

# # pic = st.sidebar.camera_input('Foto toevoegen?')
# # if pic:
# #     st.sidebar.subheader('De volgende foto wordt ge-upload')
# #     st.sidebar.image(pic)
# # else:
# #     pic = False

# # if pic:
# #     from io import BytesIO
# #     from PIL import Image
# #     # Create a binary stream
# #     image_stream = Image.open(pic)
# #     st.write(image_stream)
# #     img_array = np.array(image_stream)
# #     st.write(img_array)
