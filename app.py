import json
import pandas as pd
import altair as alt
import pydeck as pdk
import streamlit as st
from db import *
from session import SessionState, get


def get_config(path='config.json'):
    return json.load(open(path, 'r'))

def get_interactive_linechar(df):
    line = alt.Chart(df).mark_line(interpolate = 'basis').encode(
        x = 'date:T',
        y = '# of the people:Q',
        color = 'category:N',
    )
    nearest = alt.selection(
        type = 'single', 
        nearest = True,
        on = 'mouseover', 
        fields = ['date'], 
        empty = 'none'
    )
    selectors = alt.Chart(df).mark_point().encode(
        x = 'date:T', 
        opacity = alt.value(0)
    ).add_selection(nearest)

    points = line.mark_point().encode(
        opacity = alt.condition(nearest, alt.value(1), alt.value(0))
    )

    text = line.mark_text(align = 'left', dx = 5, dy = -5).encode(
        text = alt.condition(nearest, '# of the people:Q', alt.value(''))
    )
    line_chart = alt.layer(line, selectors, points, text).interactive()
    return line_chart

def display_country_page(db):
    all_countries = None
    session_state = get(all_countries=None)
    if session_state.all_countries is None:
        message = st.text('Loading data...')
        all_countries = get_all_countries(db)
        session_state.all_countries = all_countries
        message.text('')
    country = st.selectbox('Choose a country', session_state.all_countries)
    
    all_documents = get_all_documents(db, {"country": country})
    df = pd.DataFrame(get_daily_data(all_documents), 
                        columns = [
                            'date', 'confirmed_daily', 'deaths_daily', 'recovered_daily'])
    df = df.melt('date', var_name='category', value_name='# of the people')
    daily_linechart = get_interactive_linechar(df).properties(
        width = 1000,
        height = 500
    )
    

    df = pd.DataFrame(get_acc_data(all_documents, 'date'), columns = ['date', 'confirmed', 'deaths', 'recovered']).melt('date', var_name = 'category', value_name = '# of the people')
    acc_linechart = get_interactive_linechar(df).properties(
        width = 1000,
        height = 500
    )
    st.subheader(f'Covid-19 daily statistics in {country}')
    st.altair_chart(daily_linechart, use_container_width = True)
    st.subheader(f'Covid-19 cumulative statistics in {country}')
    st.altair_chart(acc_linechart, use_container_width = True)

def display_global_page(db):
    message = st.text('Loading data...')
    all_documents = get_all_documents(db, global_agg = True)
    message.text('')

    df = pd.DataFrame(get_acc_data(all_documents, '_id'), columns = ['date', 'confirmed', 'deaths', 'recovered']).melt('date', var_name = 'category', value_name = '# of the people')
    st.subheader('Covid-19 global cumulative statistics')
    acc_linechart = get_interactive_linechar(df).properties(
        width = 1000,
        height = 500
    )
    st.altair_chart(acc_linechart, use_container_width = True)

    message = st.text('Loading map...')
    top_latest_dates = get_k_latest_dates(db, 14)
    date = st.slider('Chooose a date', top_latest_dates[-1], top_latest_dates[0], top_latest_dates[0])
    all_documents = get_all_documents(db, {"date": date}, collection = 'global')
    coordinates_data = get_coordinates_data(all_documents)

    df = pd.DataFrame(coordinates_data, columns = ['confirmed_daily', 'coordinates'])
    layer = pdk.Layer(
        "ScatterplotLayer",
        df,
        pickable=True,
        opacity=0.8,
        stroked=True,
        filled=True,
        radius_scale=6,
        radius_min_pixels=2,
        radius_max_pixels=100,
        line_width_min_pixels=1,
        get_position="coordinates",
        get_radius="confirmed_daily",
        get_fill_color=[240, 60, 45],
        get_line_color=[0, 0, 0],
    )
    message.text('')
    st.subheader('Covid-19 in the world on' + f' {date.strftime("%d/%m/%Y")}')
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
        latitude = 10.762622,
        longitude = 106.660172,
        zoom = 2,
        pitch = 50,
        ),
        layers = [layer]
    ))



if __name__ == '__main__':
    config = get_config()
    db = connect_database(**config)

    st.title('Covid-19 Data Visualization')
    nav_box = st.sidebar.selectbox('Choose a page', ['Global', 'Country'], index = 0)
    if nav_box == 'Country':
        display_country_page(db)
    else:
        display_global_page(db)
