import streamlit as st
import pandas as pd 
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import time

# Config
st.set_page_config(
    page_title="GetAround Delay",
    page_icon="🚗 ",
    layout="wide"
)

DATA_URL = ("https://full-stack-assets.s3.eu-west-3.amazonaws.com/Deployment/get_around_delay_analysis.xlsx")


def client_friction(df, threshold, scope=None, indices=False):

    rentals_w_prev_driver = df[df["previous_ended_rental_id"].notna()]["rental_id"].tolist()
    rentals_w_next_driver = df[df["previous_ended_rental_id"].notna()]["previous_ended_rental_id"].tolist()
    ids = rentals_w_prev_driver + rentals_w_next_driver
    df = df[df["rental_id"].isin(ids)]

    if scope == "mobile" or scope == "connect":
                df = df[df["checkin_type"] == scope]

    client_firction = 0
    client_firction_indicies = []
    cancelations = 0

    for i, ids in df["rental_id"].items():
        current_rental = df[df["rental_id"] == ids]
        previous_rental = df[df.loc[:,"rental_id"] == current_rental.iloc[0,5]]
        
        if not previous_rental.empty:
            if previous_rental.iloc[0,4] > 0:
                if previous_rental.iloc[0,4] > (current_rental.iloc[0,6] + threshold):
                    client_firction += 1
                    client_firction_indicies.append(i)
                    if current_rental.iloc[0,3] == "canceled":
                        cancelations += 1
    if indices is True:
        return client_firction_indicies
    else:
         return client_firction, cancelations

def affected_rentals(df, threshold, scope=None, indices=False):
    if scope == "mobile" or scope == "connect":
        df = df[df["checkin_type"] == scope]

    time_deltas = df["time_delta_with_previous_rental_in_minutes"]
    affected_rentals = 0
    affected_rentals_indices = []

    for index, time in time_deltas.items():
        if time < threshold:
            affected_rentals += 1
            affected_rentals_indices.append(index)

    if indices is True:
        return affected_rentals_indices
    else: 
        return affected_rentals
    
def affected_owner_shares(df, threshold, scope=None, metric="mean"):
    revenue_index_per_car = df["car_id"].value_counts().reindex(df["car_id"].unique(), fill_value=0)
    revenue_index_per_car_with_feature = df.drop(affected_rentals(df, threshold, scope, indices=True))["car_id"].value_counts().reindex(df["car_id"].unique(), fill_value=0)
    rev_impact = pd.DataFrame(data={"number_of_rents" : revenue_index_per_car.values, "number_of_rents_after_feature" : revenue_index_per_car_with_feature.values}, index=revenue_index_per_car.index)
    rev_impact["loss"] = rev_impact.apply(lambda x: x.number_of_rents - x.number_of_rents_after_feature, axis=1)
    rev_impact["loss_percent"] = rev_impact.apply(lambda x: (x.loss / x.number_of_rents)*100, axis=1)
    if metric == "mean":
        return round(rev_impact["loss_percent"].mean(),1)
    if metric == "max":
        return round(rev_impact["loss_percent"].max(),1)
    if metric == "median":
        return round(rev_impact["loss_percent"].median(),1)

### App
st.title("Decision helper for the new delay feature")

st.markdown("---")


@st.cache_data
def load_data():
    data = pd.read_excel(DATA_URL, engine='openpyxl')
    return data


data_load_state = st.text('Loading data...')
data = load_data()
data_load_state.text("") # change text from "Loading data..." to "" once the the load_data function has run

# Body
## Remove rentals that were cancelled and for which there were no subsequent rentals
mask = (data["delay_at_checkout_in_minutes"].isna()) & (data["previous_ended_rental_id"].isna() & (data["state"] == "canceled"))
data = data.drop(data[mask].index)

st.header("Driver punctuality and Impact on subsequent drivers")

def early_late(x):
    if x < 0:
        return "early"
    elif x > 0:
        return "late"
    elif x == 0:
        return "on-time"
    
data["timing"] = data["delay_at_checkout_in_minutes"].apply(lambda x: early_late(x))
data["next_driver"] = data["previous_ended_rental_id"].apply(lambda x: "single rental" if np.isnan(x) else "back-to-back rental")
data.head()

vals = data["timing"].value_counts()

colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

trace1 = go.Pie(
    labels=["Late drivers", "Early drivers","On time drivers"], 
    values=[vals[0], vals[1], vals[2]], 
    hole=.5,
    title="Driver puntuality",
    marker=dict(colors=colors, line=dict(color='#000000', width=2))
    )

fig = go.Figure(data=[trace1])

st.plotly_chart(fig, use_container_width=True, theme=None)


st.write(f"Drivers were late about :red[{(vals[0]/vals.sum()*100):.1f}%] of the time, which generated :red[{client_friction(data, 0)[0]}] problems in back-to-back rentals")

st.markdown('''
As pointed out, a delay feature between rentals might help mitigate these problems. 
In the following, an analysis of the impact of different delay thresholds is presented in order to help our product manager decide on the  the best course of action.''')

st.markdown("---")

st.header("Effect of the delay feature on rental activity")

st.subheader("Choose delay scope (type of check-in)")


scope = st.selectbox(
   "Select scope",["all", "mobile", "connect"])
   

with st.spinner("Please wait..."):
    feature_effect = pd.DataFrame(data={"delay_threshold" : np.arange(0, 390, 30).tolist()})

    feature_effect[["unhappy_clients","canceled_rentals"]] = feature_effect.apply(lambda x: client_friction(data, x["delay_threshold"], scope),axis=1, result_type='expand')
    feature_effect["affected_rentals"] = feature_effect["delay_threshold"].apply(lambda x: affected_rentals(data, x, scope))
    feature_effect["owner_share_loss"] = feature_effect["delay_threshold"].apply(lambda x: affected_owner_shares(data, x, scope, "mean"))

    trace1 = go.Bar(name='Ended rentals', 
                    x=feature_effect.delay_threshold, 
                    y=(feature_effect.unhappy_clients - feature_effect.canceled_rentals), 
                    hovertemplate = 'Ended: %{y}',
                    marker_color='#1f77b4')
    trace2 = go.Bar(name='Canceled rentals', 
                    x=feature_effect.delay_threshold, 
                    y=feature_effect.canceled_rentals, 
                    hovertemplate = 'Canceled: %{y}',
                    marker_color='#ff7f0e')

    fig = go.Figure(data=[trace1, trace2])
    # Change the bar mode
    fig.update_layout(barmode='stack',
                      title="Driver unsatifaction (due to late check-outs) given a delay threshold between rentals",
                      xaxis = dict(
                      title = "Delay threshold in minutes",
                      tickmode = 'array',
                      tickvals = np.arange(0, 390, 30).tolist()),
                      yaxis_title="Number of unsatisfied drivers",
                      legend_title="Rental status")

    st.plotly_chart(fig, use_container_width=True, theme=None)

    st.write("A 30 min delay threshold greatly diminishes instances of unsatisfied drivers due to late check-outs. This effet, however, fades the higher the threshold.")

    trace3 = go.Bar(name='Affected rentals', 
                x=feature_effect.delay_threshold, 
                y=feature_effect.affected_rentals, 
                hovertemplate = 'Removed rentals: %{y}',
                marker_color='#1f77b4',
                yaxis='y', 
                offsetgroup=1)
    trace4 = go.Bar(name='Mean owner loss', 
                    x=feature_effect.delay_threshold, 
                    y=feature_effect.owner_share_loss, 
                    hovertemplate = 'Mean owner loss: %{y:.2f}%',
                    marker_color='#ff7f0e', 
                    yaxis='y2', 
                    offsetgroup=2)
    
    fig = go.Figure(data=[trace3, trace4], 
                    layout={
                            'yaxis': {'title': 'Number of affected back-to-back rentals', 'title_font_color':"#1f77b4"},
                            'yaxis2': {'title': 'Percent of mean owner rental losses', 'overlaying': 'y', 'side': 'right', 'title_font_color':"#ff7f0e"}
        })
    # Change the bar mode
    fig.update_layout(title="Effect of a delay between rentals on rental numbers and owner losses",
                      xaxis = dict(
                      title = "Delay threshold in minutes",
                      tickmode = 'array',
                      tickvals = np.arange(0, 390, 30).tolist()),
                      showlegend=False)
    
    st.plotly_chart(fig, use_container_width=True, theme=None)

    st.markdown("""
    - Percent of affected rentals was computed as the number rentals among all back-to-back rentals that would go missing from searches given a delay threshold
    - Percent of owner share losses was computed as the number rentals an owner might lose due to a delay between rentals.
    """)
    st.write("*Delay threshold should be chosen in order to minimize the number of unsatisfied drivers, affected rentals and owner losses*")