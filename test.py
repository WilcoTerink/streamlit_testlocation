import streamlit as st
from streamlit_geolocation import streamlit_geolocation
import pandas as pd
from streamlit_folium import st_folium
import folium


# https://folium.streamlit.app/draw_support

myTile = "https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/grijs/EPSG:3857/{z}/{x}/{y}.png"
myTile = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
#myTile = "https://service.pdok.nl/rvo/brpgewaspercelen/wms/v1_0?request=GetCapabilities&service=WMS"
myAttr = "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"

st.title('Welkom bij de beregeningsdetector')
st.subheader(f"Vandaag is het {pd.Timestamp('now').date().strftime('%d %B %Y')}")

st.write('1. Klik op onderstaande knop om je locatie te bepalen.')

location = streamlit_geolocation()
st.write('2. Doorloop daarna de stappen links.')
st.write("Je huidige lokatie is:")
st.write(f"Lat: {location['latitude']}, Lon: {location['longitude']}")


if location['latitude'] != None:
    lat = location['latitude']
    lon = location['longitude']
    m = folium.Map(location=[lat, lon], zoom_start=16, tiles=myTile, attr=myAttr)
    myLocation = folium.Marker([lat, lon], popup="Mijn locatie").add_to(m)
    df = pd.DataFrame(data={'lat': lat, 'lon': lon}, index=[0])
else:
    lat = 52.25
    lon = 5.25
    m = folium.Map(location=[lat, lon], zoom_start=8, tiles=myTile, attr=myAttr)
    df = None

# call to render Folium map in Streamlit
st_data = st_folium(m, width=725)

if df is not None:
    st.write(f"Nauwkeurigheid: {location['accuracy']} m")
    st.map(df, zoom=16, size=location['accuracy'])

# st.dataframe(dataframe.style.highlight_max(axis=0))
#st.slider('x')


st.sidebar.markdown('### Beantwoord onderstaande vragen')

gewassen = ['Kale grond', 'Gras', 'Mais', 'Aardappel', 'Suikerbieten', 'Weet ik niet']
landgebruik = st.sidebar.selectbox('Landgebruik/gewas?', gewassen, placeholder='Weet ik niet', index=len(gewassen)-1)

#beregening = st.sidebar.radio('Is het perceel beregend?', ['Ja', 'Nee'], index=0)
beregening = st.sidebar.toggle('Beregening?')
#st.write(beregening)


#if beregening == 'Ja':
if beregening:
    bron = st.sidebar.selectbox(
        'Wat is de bron van beregening?',
        ['Grondwater', 'Oppervlaktewater', 'Weet ik niet'], index=None, placeholder='Maak keuze')


opmerking = st.sidebar.text_area("Opmerkingen:")

pic = st.sidebar.camera_input('Foto toevoegen?')
if pic:
    st.sidebar.subheader('De volgende foto wordt ge-upload')
    st.sidebar.image(pic)



submit = st.sidebar.button('Upload waarneming naar beregeningsportaal')
if submit:
    st.sidebar.write('Waarneming is ge-upload naar het beregeningsportaal')



