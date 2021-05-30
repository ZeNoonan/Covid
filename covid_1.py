import requests
import streamlit as st
import json
import pandas as pd
import altair as alt
import datetime
# from vega_datasets import data
import copy
st.set_page_config(layout="wide")

# I USED SOURCERY ON THIS FILE

# https://stackoverflow.com/questions/41100303/convert-api-to-pandas-dataframe
# response = requests.get("https://opendata.arcgis.com/datasets/d9be85b30d7748b5b7c09450b8aede63_0.geojson")
# # response = requests.get("https://services1.arcgis.com/eNO7HHeQ3rUcBllm/arcgis/rest/services/CovidStatisticsProfileHPSCIrelandOpenData/FeatureServer/0")
# x = response.json()
# st.write (x)
# df=pd.read_json('https://services1.arcgis.com/eNO7HHeQ3rUcBllm/arcgis/rest/services/Covid19CountyStatisticsHPSCIreland/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json')
# st.write (df)

# st.write (response)
# source = data.iowa_electricity()
# st.write (source.head())
@st.cache
def prep_data(url):
    return pd.read_csv(url)

# data = pd.read_csv('http://opendata-geohive.hub.arcgis.com/datasets/d8eb52d56273413b84b0187a4e9117be_0.csv?outSR={%22latestWkid%22:3857,%22wkid%22:102100}')

@st.cache
def covid_data():
    return prep_data('http://opendata-geohive.hub.arcgis.com/datasets/d8eb52d56273413b84b0187a4e9117be_0.csv?outSR={%22latestWkid%22:3857,%22wkid%22:102100}').copy()

@st.cache
def data_cache(allow_output_mutation=True):
    df_county = prep_data('http://opendata-geohive.hub.arcgis.com/datasets/d9be85b30d7748b5b7c09450b8aede63_0.csv?outSR={%22latestWkid%22:3857,%22wkid%22:102100}').copy()
    df_county['Date'] = pd.to_datetime( df_county['TimeStamp'] )
    return df_county

df_county_1=data_cache().copy()

def format_table(x):
    return x.style.format({'Moving_7_day_Average': "{:,.0f}", 'per_hundred_thousand': '{:,.0f}','cases_shift': '{:,.0f}', 'PopulationCensus16': '{:,.0f}',
    'cases_movement': '{:,.0f}'})

# st.write ('the original df county should have all the columns',df_county)
# df_county['Date'] = pd.to_datetime( df_county['TimeStamp'] )
# df_county['Cases_County_Rolling'] = df_county.groupby (['CountyName', 'TimeStamp'])['ConfirmedCovidCases'].cumsum()

# def movement_cases(x):
#     x = x.sort_values(by=['CountyName','TimeStamp'], ascending =[True,True])
#     x['cases_shift'] = x['ConfirmedCovidCases'].shift(1)
#     x['cases_movement'] = x['ConfirmedCovidCases'] - x['cases_shift']
#     return x

def movement_cases(x):
    x['cases_shift'] = x.groupby('CountyName')['ConfirmedCovidCases'].shift()
    x['cases_movement'] = x['ConfirmedCovidCases'] - x['cases_shift']
    return x

df_county = movement_cases(df_county_1)
# df_county['Cases_Rolling_Average'] = df_county['ConfirmedCovidCases'].rolling(window=7,min_periods=7).mean()
df_county['Moving_7_day_Average'] = df_county.groupby('CountyName')['cases_movement'].transform(lambda x: x.rolling(7, 1).mean())
df_county['per_hundred_thousand'] = (df_county['Moving_7_day_Average'] / df_county['PopulationCensus16'])*100000
# st.write ('this is df county after running the function', df_county)
# df_county['hospitalisation_per_census'] = df_county['']
cols_to_move = ['CountyName','Date','cases_movement','Moving_7_day_Average','per_hundred_thousand','PopulationCensus16','ConfirmedCovidCases','cases_shift' ]
cols = cols_to_move + [col for col in df_county if col not in df_county]

def covid_area_chart(data,col_selection, tickcount_county):
    return (
        alt.Chart(data)
        .mark_area()
        .encode(
            x=alt.X('Date:T',
                    axis=alt.Axis(
                    title='Date',
                    labelAngle=90,
                    tickCount=tickcount_county,
                    format='%d-%b',
                ),
            ),
            y=alt.Y(col_selection),
            color=alt.Color('CountyName:N',legend=alt.Legend(orient="bottom")),
            # order = alt.Order('cases_movement'),
            # color=alt.Color('CountyName:N', sort = alt.EncodingSortField('ConfirmedCovidCases', op='min')),
            tooltip=['CountyName'],
        ).interactive().properties(width=1400,height=600)
    )

def covid_line_chart(data,col_selection, tickcount_county):
    return (
        alt.Chart(data)
        .mark_line()
        .encode(
            x=alt.X('Date:T',
                    axis=alt.Axis(
                    title='Date',
                    labelAngle=90,
                    tickCount=tickcount_county,
                    format='%d-%b',
                ),
            ),
            y=alt.Y(col_selection),
            color=alt.Color('CountyName:N',legend=alt.Legend(orient="bottom")),
            # order = alt.Order('cases_movement'),
            # color=alt.Color('CountyName:N', sort = alt.EncodingSortField('ConfirmedCovidCases', op='min')),
            tooltip=['CountyName'],
        ).interactive().properties(width=1400,height=600)
    )

def test(data,col_selection, tickcount_county):
    
    highlight = alt.selection(type='single', on='mouseover',fields=['CountyName'], nearest=True)

    base = alt.Chart(data).encode(x=alt.X('Date:T',
                    axis=alt.Axis(
                    title='Date',
                    labelAngle=90,
                    tickCount=tickcount_county,
                    format='%d-%b',
                ),
            ),
            y=alt.Y(col_selection),
            # color=alt.Color('CountyName:N'))
            color=alt.Color('CountyName:N',legend=alt.Legend(orient="bottom")),tooltip=['CountyName']).properties(width=1400,height=600)

    # points = base.mark_circle().encode(opacity=alt.value(0)).add_selection(highlight).properties(width=600)
    points = base.mark_circle().encode(opacity=alt.value(0)).add_selection(highlight)

    lines = base.mark_line().encode(size=alt.condition(~highlight, alt.value(1), alt.value(6)))
    # lines = base.mark_line().encode(size=alt.condition(~highlight, alt.value(1), alt.value(3)))


    return points + lines

def test_area(data,col_selection, tickcount_county):
    
    highlight = alt.selection(type='single', on='mouseover',fields=['CountyName'], nearest=True)

    base = alt.Chart(data).encode(x=alt.X('Date:T',
                    axis=alt.Axis(
                    title='Date',
                    labelAngle=90,
                    tickCount=tickcount_county,
                    format='%d-%b',
                ),
            ),
            y=alt.Y(col_selection),
            # color=alt.Color('CountyName:N'))
            color=alt.Color('CountyName:N',legend=alt.Legend(orient="bottom")),tooltip=['CountyName']).properties(width=1400,height=600)

    # points = base.mark_circle().encode(opacity=alt.value(0)).add_selection(highlight).properties(width=600)
    points = base.mark_circle().encode(opacity=alt.value(1)).add_selection(highlight)

    lines = base.mark_line().encode(size=alt.condition(~highlight, alt.value(1), alt.value(.05)))
    # lines = base.mark_line().encode(size=alt.condition(~highlight, alt.value(1), alt.value(3)))


    return points + lines



# st.write ('this is df county after columns moved', df_county[cols])
# st.write ('this sorted', df_county[cols].sort_values(by='County', ascending=True))
with st.beta_expander('County Detail Data - select county to see'):
    st.write ('Which county would you like to see the data for?')
    county_names=df_county['CountyName'].unique()
    names_selected = st.selectbox('Which county would you like to see the data for?',county_names, index=5)
    def county_select(x, names_selected):
        x= x[x['CountyName']==names_selected]
        return x[cols].sort_values(by=['Date','Moving_7_day_Average'], ascending =[False,False]) 
    st.write (format_table(county_select(df_county,names_selected)))

with st.beta_expander('County Detail Data sorted by Highest Rolling 7 day Average'):
    st.write ('County sorted by Highest Rolling 7 day Average',format_table(df_county[cols].sort_values(by=['Date','Moving_7_day_Average'], ascending =[False,False])))

df_county= df_county[df_county['Date']>'2020-04-01']
tickcount_county = df_county['Date'].nunique()


with st.beta_expander('County moving 7 Day Average of Cases'):
    # st.altair_chart(covid_area_chart(df_county,'cases_movement:Q', tickcount_county),use_container_width=True)
    st.altair_chart(covid_area_chart(df_county,'Moving_7_day_Average:Q', tickcount_county),use_container_width=True)

with st.beta_expander('County per 100,000 of population moving 7 Day Average of Cases'):
    # st.altair_chart(covid_line_chart(df_county,'per_hundred_thousand:Q', tickcount_county),use_container_width=True)
    # st.write('Chart by County for cases per hundred thousand')
    st.altair_chart(test(df_county,'per_hundred_thousand:Q', tickcount_county),use_container_width=True)


# st.altair_chart(covid_area_chart(df_county,'cases_movement:Q', tickcount_county),use_container_width=True)
# st.altair_chart(covid_area_chart(df_county,'Moving_7_day_Average:Q'),use_container_width=True)
# st.write('this is the data i am using LOOKS FINE')
# st.write (df_county)

# def streamlit_chart(data):
#     return(alt.Chart(data).mark_area().encode(alt.X('Date:T'),alt.Y('Moving_7_day_Average:Q'),alt.Color('CountyName:N')))
# st.altair_chart(streamlit_chart(df_county),use_container_width=True) #THIS WORKS!!!!!!!!!!!!!!!!


# st.write (df)
df=covid_data().copy()
df['Deaths_Rolling_Average'] = df['ConfirmedCovidDeaths'].rolling(window=7,min_periods=7).mean()
df['Cases_Rolling_Average'] = df['ConfirmedCovidCases'].rolling(window=7,min_periods=7).mean()
# df['Date'] = df['Date'].apply(lambda d: datetime.datetime.fromtimestamp(int(d)/1000).strftime('%Y-%m-%d %H:%M:%S'))
df['Date'] = pd.to_datetime( df['Date'] )
df['Hospital_shift'] = df['HospitalisedCovidCases'].shift()
df['Hospital_movement'] = df['HospitalisedCovidCases'] - df['Hospital_shift']
df['Hospital_Moving_7_day_Average'] = df['Hospital_movement'].rolling(window=7,min_periods=1).mean()
# https://stackoverflow.com/questions/58193274/converting-unix-13-digits-to-datetime-timestamp-format-with-pandas
# st.write ('original dataframe want to see ICU', df)
# st.write('hospitalisation', df.head())
df1=df.loc[:,['Date','ConfirmedCovidDeaths','Deaths_Rolling_Average']]
cases=df.loc[:,['Date','ConfirmedCovidCases','Cases_Rolling_Average']]
hospitalisation = df.loc[:,['Date','Hospital_movement','Hospital_Moving_7_day_Average']]
df3=df1.melt(id_vars=['Date'],var_name='Type',value_name='Deaths')
cases_melt = cases.melt(id_vars=['Date'],var_name='Type',value_name='Cases')
hospitalisation_melt = hospitalisation.melt(id_vars=['Date'],var_name='Type',value_name='Hospital_Cases')
df4= df3[df3['Date']>'2020-03-01']
cases_melt = cases_melt[cases_melt['Date']>'2020-03-01']
tickcount_dates = (df4['Date'].nunique() )
tickcount_dates_cases = (cases_melt['Date'].nunique() )
tickcount_hosp =(hospitalisation_melt['Date'].nunique() )

def data_prep(x,col1, col2, type_of_case,min_date):
    x = x.loc[:,['Date',col1,col2]]
    x = x.melt(id_vars=['Date'],var_name='Type',value_name=type_of_case)
    return x[x['Date']>min_date]

cases_1 = data_prep(df,'ConfirmedCovidCases','Cases_Rolling_Average','Cases','2020-03-01' ) 
# https://github.com/d3/d3-time-format#locale_format
# https://altair-viz.github.io/user_guide/generated/core/altair.Axis.html
# https://stackoverflow.com/questions/59699412/altair-display-all-axis-ticks-but-only-some-tick-labels
# https://altair-viz.github.io/user_guide/customization.html?highlight=axis%20tick#adjusting-axis-labels
def covid_chart(data,type_scale,death_case,tickcount_data):
    return (
        alt.Chart(data)
        .mark_line(point=True)
        .encode(
            x=alt.X('Date:T',
                    axis=alt.Axis(
                    title='Date',
                    labelAngle=90,
                    tickCount=tickcount_data,
                    format='%d-%b',
                ),
            ),
            y=alt.Y(death_case, scale=alt.Scale(type=type_scale)),
            color=alt.Color('Type',legend=alt.Legend(orient="bottom")),
            tooltip=[death_case],
        ).properties(width=1400,height=600)
    )

st.write('Using container_width BELOW')
with st.beta_expander('Cases Chart'):
    st.altair_chart(covid_chart(cases_1,'linear','Cases',tickcount_dates_cases),use_container_width=True)
# st.write('Using CUSTOMISED width height below')
# st.altair_chart(covid_chart(cases_1,'linear','Cases',tickcount_dates_cases))
# st.write('Using container_width BELOW')
with st.beta_expander('Deaths Chart'):
    st.altair_chart(covid_chart(df4,'linear','Deaths',tickcount_dates),use_container_width=True)
# st.write('Using CUSTOMISED width height below')
# st.altair_chart(covid_chart(df4,'linear','Deaths',tickcount_dates))
# st.write('Using container_width BELOW')
with st.beta_expander('Hospitalisations Chart'):
    st.altair_chart(covid_chart(hospitalisation_melt,'linear','Hospital_Cases',tickcount_hosp),use_container_width=True)
# st.write('Using CUSTOMISED width height below')
# st.altair_chart(covid_chart(hospitalisation_melt,'linear','Hospital_Cases',tickcount_hosp))
# st.altair_chart(covid_chart(cases_melt,'log','Cases',tickcount_dates_cases),use_container_width=True)
# st.altair_chart(covid_chart(df4,'log','Deaths',tickcount_dates),use_container_width=True)

# st.altair_chart(test_area(df_county,'per_hundred_thousand:Q', tickcount_county),use_container_width=True)
with st.beta_expander('Cases by County per 100,000'):
    st.altair_chart(test(df_county,'per_hundred_thousand:Q', tickcount_county),use_container_width=True)




# https://stackoverflow.com/questions/55794391/altair-interactive-line-plot-make-line-pop-and-highlighted-when-clicking-icon-o/55796860#55796860
# def test_again_line(data,col_selection, tickcount_county):
#     background = alt.Chart(data).mark_line(point=True, size=10).encode(x=alt.X('Date:T',
#                     axis=alt.Axis(
#                     title='Date',
#                     labelAngle=90,
#                     tickCount=tickcount_county,
#                     format='%d-%b',
#                 ),
#             ),
#             y=alt.Y(col_selection),
#             # color=alt.Color('CountyName:N'))
#             color=alt.Color('CountyName:N'),tooltip=['CountyName'])

#     foreground = background.encode(
#         color=alt.Color(col_selection, legend=None,
#                         scale=alt.Scale(scheme='category10'))
#     ).transform_filter(
#         selection
#     )


#     legend = alt.Chart(data).mark_point(filled=True, size=200).encode(
#         y=alt.Y(col_selection),
#         color=color
#     ).add_selection(
#         selection
#     )

#     return (background + foreground) | legend