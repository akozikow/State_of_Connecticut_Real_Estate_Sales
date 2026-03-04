import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
import branca
from streamlit_folium import st_folium
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
@st.cache_data
def load_data(url1, url2):
    data1 = gpd.read_file(url1)
    data2 = pd.read_csv(url2)
    return data1, data2

conn_geojson, conn_data = load_data(
'https://raw.githubusercontent.com/akozikow/State_of_Connecticut_Real_Estate_Sales/main/conn_geopandas.geojson',
'https://github.com/akozikow/State_of_Connecticut_Real_Estate_Sales/raw/refs/heads/main/conn_cleaned_data.csv'
)
st.header('Connecticut Housing Data')
st.write('Original data from the State of Connecticut Office of Policy and Management and sourced via Data.gov at the following link: https://catalog.data.gov/dataset/real-estate-sales-2001-2018.')
st.write('Geojson data used in folium mapping was sourced from the following source: https://deepmaps.ct.gov/datasets/CTDEEP::connecticut-and-vicinity-town-boundary-set/explore?layer=1&location=41.323050%2C-72.511382%2C9.')
st.write('Data was cleaned and filtered to omit extreme values (e.g., homes with sale prices exceeding 2 Million USD), and filters out every property type except Single Family Homes. '
         'The sidebar can be used to choose the desired statistic (Percent Change or Raw Change) in Median Sale Price, as well as the two years to compare.')
st.write('NOTE: Years have dissimilar amounts of data (early years are light on data). Towns with no data for the selected year will be empty and have no color in the map below, and likewise will have a value of "None" in the table.')
st.sidebar.subheader('Select Report Type')
chosen_stat = st.sidebar.selectbox('Report Type',['Percent Change', 'Raw Change'])
st.sidebar.subheader('Select Start and End Year')
start_year = st.sidebar.selectbox('Start Year', sorted(conn_data['Date Recorded'].unique())[:-1], index = 15)
end_year = st.sidebar.selectbox('End Year', sorted(conn_data['Date Recorded'].unique())[1:], index = 19)
if end_year <= start_year:
    st.sidebar.warning('Warning: End Year should be greater than Start Year')

conn_data_start = conn_data.copy()
conn_data_end = conn_data.copy()
start_year_input = start_year
end_year_input = end_year
conn_data_start = conn_data_start[conn_data_start['Date Recorded'] == start_year]
conn_data_end = conn_data_end[conn_data_end['Date Recorded'] == end_year]
conn_df_start = pd.DataFrame(conn_data_start.groupby('Town')['Sale Amount'].median()).reset_index()
conn_df_start.rename(columns={'Town':'TOWN_NAME', 'Sale Amount':'START_YEAR_SALE_AMOUNT'}, inplace=True)
conn_df_end = pd.DataFrame(conn_data_end.groupby('Town')['Sale Amount'].median()).reset_index()
conn_df_end.rename(columns={'Town':'TOWN_NAME', 'Sale Amount':'END_YEAR_SALE_AMOUNT'}, inplace=True)
conn_df1 = pd.merge(conn_geojson, conn_df_start, how = 'left', on = 'TOWN_NAME')
conn_df2 = pd.merge(conn_df1, conn_df_end, how = 'left', on = 'TOWN_NAME')
conn_df2['Percent Change'] = ((conn_df2['END_YEAR_SALE_AMOUNT'] - conn_df2['START_YEAR_SALE_AMOUNT']) / conn_df2['START_YEAR_SALE_AMOUNT'])*100
conn_df2['Raw Change'] = (conn_df2['END_YEAR_SALE_AMOUNT'] - conn_df2['START_YEAR_SALE_AMOUNT'])

z = folium.Map(location = [41.5658, -72.7734],
               zoom_start= 8,
               zoom_control = False,
               scroll_wheel_zoom = False,
               dragging = False,
               min_zoom = 8,
               max_zoom = 8,
               width = 600)

colormap = branca.colormap.LinearColormap(
    vmin=conn_df2[chosen_stat].quantile(0.0),
    vmax=conn_df2[chosen_stat].quantile(1),
    colors=['darkgreen','yellow', 'red'],
    caption=f'{chosen_stat} from {start_year}-{end_year}',
)

tooltip = folium.GeoJsonTooltip(
    fields=["TOWN_NAME", chosen_stat],
    aliases=["Town:", f'{chosen_stat}'],
    localize=True,
    sticky=False,
    labels=True,
    style="""
        background-color: #F0EFEF;
        border: 2px solid black;
        border-radius: 3px;
        box-shadow: 3px;
    """,
    max_width=400
)

folium.GeoJson(
    conn_df2,
    style_function=lambda x: {
        "fillColor": colormap(x["properties"][chosen_stat])
        if x["properties"][chosen_stat] is not None
        else "transparent",
        "color": "black",
        "fillOpacity": 0.7,
    },
    tooltip = tooltip,
).add_to(z)
colormap.width = 500
colormap.add_to(z)

st.divider()

st.subheader(f'{chosen_stat} in Median Sale Price of Single Family Homes from {start_year}-{end_year}')
st.write('The interactive map and the table below both display the chosen summary statistic (either Percent Change or Raw Change) '
         'in the Median Sale Price of Single Family Homes between the chosen years.')

col1, col2 = st.columns([3, 1])

with col1:
    st.write(f'Map of Connecticut: {chosen_stat}')
    st.data = st_folium(z, height=400, width = 600, use_container_width= True)
with col2:
    st.write(f'{chosen_stat} by Town')
    st.dataframe((conn_df2[['TOWN_NAME', chosen_stat]]).rename(columns = {'TOWN_NAME': 'Town'}).set_index('Town').sort_values(by = chosen_stat, ascending = False))

st.divider()

start_hist_data = conn_data.copy()
start_hist_data['Sale Amount'] = start_hist_data['Sale Amount'] / 1000
end_hist_data = conn_data.copy()
end_hist_data['Sale Amount'] = end_hist_data['Sale Amount'] / 1000
start_hist_data = start_hist_data[start_hist_data['Date Recorded'] == start_year]
end_hist_data = end_hist_data[end_hist_data['Date Recorded'] == end_year]
fig, ax = plt.subplots()
plt.ticklabel_format(style='plain', axis='x')
ax.hist(start_hist_data['Sale Amount'], bins=100, color='blue', alpha = 0.5, label = f'{start_year}')
ax.hist(end_hist_data['Sale Amount'], bins=100, color='red', alpha = 0.5, label = f'{end_year}')
plt.legend()
plt.title(f'Comparing Volume and Price of Homes Sold: {start_year} and {end_year}')
plt.ylabel('Number of Homes Sold')
plt.xlabel('Sale Amount (in Thousands of Dollars)')

st.subheader('Comparison of Home Sale Volume and Price by Year')
st.write('The below histogram compares the volume and price of homes sold for the selected years. '
         'Blue data is from the chosen Start Year, and Red Data is from the chosen End Year. '
         'The Purple data, which is not seen in the legend, is the overlap of the two data distributions')
col1, col2, col3 = st.columns([1, 4, 1])
with col2:
    st.pyplot(fig, width=500)

