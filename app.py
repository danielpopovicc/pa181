from dash import Dash, html, dcc, Output, Input, State
import dash_leaflet as dl
import dash_leaflet.express as dlx
import pandas as pd
from dash_extensions.javascript import assign

color_prop = 'final_rel'

df = pd.read_csv('assets/adresní_místa___Address_points.csv')
METRIC_FOLDER = 'datasets_computations/dataset_outputs/'

# traffic

df_traffic = pd.read_csv(METRIC_FOLDER + 'traffic.csv', index_col=0, header=None)
df['trafic_score'] = df_traffic.loc[:, 1]
df['trafic_score'] = df['trafic_score'].fillna(0)
df['trafic_score_rel'] = df['trafic_score'] / df['trafic_score'].abs().max()

# skolky
df_skolka = pd.read_csv(METRIC_FOLDER + 'skolky.csv', index_col=0, header=None)
df_skolka_join = df.join(df_skolka, how='left')
df['skolka_score'] = df_skolka_join.loc[:, 1]
df['skolka_score'] = df['skolka_score'].fillna(0)
df['skolka_score_rel'] = df['skolka_score'] / df['skolka_score'].abs().max()

# prach
df_prach = pd.read_csv(METRIC_FOLDER + 'particles.csv')
df['prach'] = df_prach['pm10_1h']
df['prach_rel'] = (df['prach'] - df['prach'].min()) / (df['prach'] - df['prach'].min()).abs().max()

# brownies
df_brownies = pd.read_csv(METRIC_FOLDER + 'brownfields.csv', index_col=0, header=None)
df_brownies_join = df.join(df_brownies, how='left')
df['brownies_score'] = df_brownies_join.loc[:, 1]
df['brownies_score'] = df['brownies_score'].fillna(0)
df['brownies_score_rel'] = df['brownies_score'] / df['brownies_score'].abs().max()


# df['final_rel'] = 5


def get_final_score(w_skolka, w_traffic, w_brownies, w_prach):
    if w_skolka == 0 and w_traffic == 0 and w_brownies == 0 and w_prach == 0:
        df['final_rel'] = 0
        return

    df['final'] = w_skolka * df['skolka_score_rel'] - w_traffic * df['trafic_score_rel'] - w_brownies * df[
        'brownies_score_rel'] - w_prach * df['prach_rel']

    if df['final'].min() < 0:
        df['final'] = df['final'] - df['final'].min()
        df['final_rel'] = ((df['final'] / df['final'].abs().max()) * 10).round().astype(int)
    elif df['final'].min() > 0:
        df['final'] = df['final'] - df['final'].min()
        df['final_rel'] = ((df['final'] / df['final'].abs().max()) * 10).round().astype(int)
    else:
        df['final_rel'] = ((df['final'] / df['final'].abs().max()) * 10).round().astype(int)


get_final_score(1, 1, 1, 1)
# df = df[['Y', 'X', 'ulice_nazev', color_prop]]  # drop irrelevant columns
dicts = df.to_dict('records')

for item in dicts:
    item["tooltip"] = "{} ({:.1f})".format(item['ulice_nazev'], item[color_prop])  # bind tooltip

geojson = dlx.dicts_to_geojson(dicts, 'Y', 'X')
geobuf = dlx.geojson_to_geobuf(geojson)  # convert to geobuf

# Create a colorbar.
colorscale = ['red', 'yellow', 'green']  # rainbow
colorbar = dl.Colorbar(colorscale=colorscale, width=20, height=150, min=0, max=10, unit='')

# Geojson rendering logic, must be JavaScript as it is executed in clientside.
chroma = "https://cdnjs.cloudflare.com/ajax/libs/chroma-js/2.1.0/chroma.min.js"  # js lib used for colors
point_to_layer = assign("""function(feature, latlng, context){
    const {min, max, colorscale, circleOptions, colorProp} = context.props.hideout;
    const csc = chroma.scale(colorscale).domain([min, max]);  // chroma lib to construct colorscale
    circleOptions.fillColor = csc(feature.properties[colorProp]);  // set color based on color prop.
    return L.circleMarker(latlng, circleOptions);  // sender a simple circle marker.
}""")

cluster_to_layer = assign("""function(feature, latlng, index, context){
    const {min, max, colorscale, circleOptions, colorProp} = context.props.hideout;
    const csc = chroma.scale(colorscale).domain([min, max]);
    // Set color based on mean value of leaves.
    const leaves = index.getLeaves(feature.properties.cluster_id);
    let valueSum = 0;
    for (let i = 0; i < leaves.length; ++i) {
        valueSum += leaves[i].properties[colorProp]
    }
    const valueMean = valueSum / leaves.length;
    // Render a circle with the number of leaves written in the center.
    const icon = L.divIcon.scatter({
        html: '<div><span>' + feature.properties.point_count_abbreviated + '</span></div>',
        className: "marker-cluster",
        iconSize: L.point(40, 40),
        color: csc(valueMean)
    });
    return L.marker(latlng, {icon : icon})
}""")

# Create geojson.
geojson = dl.GeoJSON(data=geobuf, id="geojson", cluster=True, format="geobuf",
                     # zoomToBounds=True,  # when true, zooms to bounds when data changes
                     options=dict(pointToLayer=point_to_layer),  # how to draw points
                     clusterToLayer=cluster_to_layer,  # how to draw clusters
                     superClusterOptions=dict(radius=220, maxZoom=16),  # adjust cluster size
                     hideout=dict(colorProp=color_prop, circleOptions=dict(fillOpacity=1, stroke=True, radius=5), min=0,
                                  max=10, colorscale=colorscale))

# Create the app.
app = Dash(external_scripts=[chroma], prevent_initial_callbacks=False)

app.layout = html.Div([
    dcc.Checklist(
        options=[{'value': 'brown_fields', 'label': 'Brownfields', 'disabled': True},
                 {'value': 'kindergarten', 'label': 'Kindergartens', 'disabled': True},
                 {'value': 'air', 'label': 'Air quality', 'disabled': True},
                 {'value': 'traffic', 'label': 'Vehicle traffic intensity', 'disabled': True}
                 ],
        value=['brown_fields', 'air', 'kindergarten', 'traffic'], id='checklist',
        style={"display": "flex", "alignContent": "center", "justifyContent": "space-evenly", 'marginBottom': '2em'}),
    # html.Button('Apply preferences', id='submit-val', style={"display": "flex", "justifyContent": "center"}),
    html.Div(id='hidden-div', children='foo', style={'display': 'none'}),
    dl.Map([dl.TileLayer(), geojson, colorbar], id='map', center=(49.22, 16.75), zoom=10, maxZoom=18),
], style={'width': '100%', 'height': '800px', 'margin': "auto", "display": "block", "position": "relative"})

#
# @app.callback(
#     Output('geojson', 'options'),
#     Output('geojson', 'clusterToLayer'),
#     Input('submit-val', 'n_clicks'),
#     State('checklist', 'value')
# )
# def update_output(n_clicks, checklist):
#     skolka, traffic, brown, prach = False, False, False, False
#     if len(checklist) > 0:
#         if 'brown_fields' in checklist:
#             brown = True
#         if 'kindergarten' in checklist:
#             skolka = True
#         if 'air' in checklist:
#             prach = True
#         if 'traffic' in checklist:
#             traffic = True
#     get_final_score(skolka, traffic, brown, prach)
#
#     point_to_layer = assign("""function(feature, latlng, context){
#         const {min, max, colorscale, circleOptions, colorProp} = context.props.hideout;
#         const csc = chroma.scale(colorscale).domain([min, max]);  // chroma lib to construct colorscale
#         circleOptions.fillColor = csc(feature.properties[colorProp]);  // set color based on color prop.
#         return L.circleMarker(latlng, circleOptions);  // sender a simple circle marker.
#     }""")
#
#     cluster_to_layer = assign("""function(feature, latlng, index, context){
#         const {min, max, colorscale, circleOptions, colorProp} = context.props.hideout;
#         const csc = chroma.scale(colorscale).domain([min, max]);
#         // Set color based on mean value of leaves.
#         const leaves = index.getLeaves(feature.properties.cluster_id);
#         let valueSum = 0;
#         for (let i = 0; i < leaves.length; ++i) {
#             valueSum += leaves[i].properties[colorProp]
#         }
#         const valueMean = valueSum / leaves.length;
#         // Render a circle with the number of leaves written in the center.
#         const icon = L.divIcon.scatter({
#             html: '<div><span>' + feature.properties.point_count_abbreviated + '</span></div>',
#             className: "marker-cluster",
#             iconSize: L.point(40, 40),
#             color: csc(valueMean)
#         });
#         return L.marker(latlng, {icon : icon})
#     }""")
#
#     return dict(pointToLayer=point_to_layer), cluster_to_layer


if __name__ == '__main__':
    app.run_server(debug=True)
