import pandas as pd
import plotly.graph_objects as go 
import calendar 
import dash
from dash import html, dcc 
import dash_bootstrap_components as dbc 
import plotly.express as px
import pandas as pd
from dash import dash_table


app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# importation de la table de données
data = pd.read_csv("datasets/data.csv")

# Nettoyage des données
data = data.drop(columns=['Unnamed: 0', 'Tenure_Months','Transaction_ID', 'Product_SKU', 'Product_Description','Delivery_Charges','Coupon_Status','GST', 'Date', 'Offline_Spend', 'Online_Spend', 'Coupon_Code'])
data["CustomerID"] = data["CustomerID"].fillna(0) 
data = data[data['CustomerID'] != 0]
data["CustomerID"] = data["CustomerID"].astype("int32")
data["Transaction_Date"] = pd.to_datetime(data["Transaction_Date"], errors='coerce')
data["Total_price"] = data["Quantity"] * (data["Avg_Price"] *(1 - (data["Discount_pct"]*0.01)))

# Définition du mois courant (dernier mois présent dans les données)
current_month = data["Transaction_Date"].max().to_period("M").to_timestamp()

# fonctions 

def CA(data):
    return data["Total_price"].sum()

def top10(data):
    top_10 = data.groupby(["Product_Category","Gender"])[["Total_price"]]
    return top_10.agg('sum').reset_index().sort_values(["Total_price"], ascending = False).head(20)

def indicateur_mois(data, current_month):
    previous_month = current_month - pd.DateOffset(months=1)
    data_n = data[data['Transaction_Date'].dt.to_period('M') == current_month.to_period('M')]
    data_n1 = data[data['Transaction_Date'].dt.to_period('M') == previous_month.to_period('M')]
    ca_n = CA(data_n)
    ca_n1 = CA(data_n1)
    nb_ventes_n = len(data_n)
    nb_ventes_n1 = len(data_n1)
    resultat = {
        "mois"          : current_month.strftime("%B"),
        "ca_n"          : round(ca_n, 2),
        "ca_n1"         : round(ca_n1, 2),
        "nb_ventes_n"   : nb_ventes_n,
        "nb_ventes_n1"  : nb_ventes_n1,
    }
    return resultat

# table 100 dernières ventes
data100 = data.sort_values("Transaction_Date", ascending=False).head(100)

# Top 10 graphe 
df = top10(data)
fig_top10 = px.bar(
    df,
    x='Total_price',
    y='Product_Category',
    color='Gender',              
    barmode='group',             
    category_orders={
        'Product_Category': df.groupby('Product_Category')['Total_price']
                               .sum()
                               .sort_values(ascending=False)
                               .index.tolist()
    },
    title="Top 10 des produits qui rapporte le plus par genre", 
    labels={'Total_price':"Chiffre d'affaires", 'Product_Category': 'Catégorie de produit'}
)

# Graphe évolution CA semaine 
data["semaine"] = data["Transaction_Date"].dt.to_period("W")
ca_hebdo = data.groupby("semaine")["Total_price"].sum().reset_index()
ca_hebdo["semaine"] = ca_hebdo["semaine"].dt.to_timestamp()

graph_evolCA = px.line(ca_hebdo, x="semaine", y="Total_price", title="Evolution du chiffre d'affaires par semaine",
              labels={"semaine": "Semaine", "Total_price": "Chiffre d'affaires (€)"})

# Indicateurs
indicateur_vente = go.Figure()
indicateur_vente.add_trace(
    go.Indicator(value=indicateur_mois(data, current_month)["nb_ventes_n"], 
        mode="number+delta"
    )
)
indicateur_vente.update_layout( 
    template={'data': {'indicator': [{ 
        'title': {'text': "Ventes — " + indicateur_mois(data, current_month)["mois"]}, 
        'mode': "number+delta+gauge",
        'delta': {'reference': indicateur_mois(data, current_month)["nb_ventes_n1"]}}]
        }
     }
)

indicateur_CA = go.Figure()
indicateur_CA.add_trace(
    go.Indicator(value=indicateur_mois(data, current_month)["ca_n"], 
        mode="number+delta", 
        domain={'row': 1, 'column': 1}
    )
)
indicateur_CA.update_layout( 
    grid={'rows': 1, 'columns': 1, 'pattern': "independent"},
    template={'data': {'indicator': [{ 
        'title': {'text': "CA (€) — " + indicateur_mois(data, current_month)["mois"]}, 
        'mode': "number+delta+gauge",
        'delta': {'reference': indicateur_mois(data, current_month)["ca_n1"]}}]
        }
     }
)

# APP LAYOUT
app.layout = dbc.Container(
    fluid=True,
    children=[
        dbc.Row([
                dbc.Col(children=html.H2("ECAP Store"),
                        style={"margin": "0", "lineHeight": "50px"},
                        width=6),
                dbc.Col(children= 
                    dcc.Dropdown(
                                options=[{"label": loc, "value": loc} for loc in data["Location"].unique()],
                                value=None,
                                multi=True,
                                searchable=True,
                                placeholder="Sélectionner une ville",
                                disabled=False,
                                style={'margin':'6px',"marginRight": "10px"}
                ),
                    width=6)
                    ], style={'height':'50px', 'background-color':'skyblue'}
                ),
    
        dbc.Row(
            style={"height": "100vh", "margin": "0"},
            children=[

                # COLONNE GAUCHE (5/12)
                dbc.Col(
                    width=5,
                    style={"padding": "0"},
                    children=[
                        dbc.Row(
                            style={"height": "30%", "margin": "0"},
                            children=[
                                dbc.Col(
                                    width=6,
                                    style={"padding": "5px", "height": "100%"},
                                    children=dcc.Graph(
                                        figure=indicateur_CA,
                                        style={"width": "100%", "height": "100%"},
                                    ),
                                ),
                                dbc.Col(
                                    width=6,
                                    style={"padding": "0", "height": "100%"},
                                    children=dcc.Graph(
                                        figure=indicateur_vente,
                                        style={"width": "100%", "height": "100%"},
                                    ),
                                ),
                            ],
                        ),
                        dbc.Row(
                            style={"height": "65%", "margin": "0"},
                            children=[
                                dbc.Col(
                                    width=12,
                                    style={"padding": "0", "height": "100%"},
                                    children=dcc.Graph(
                                        figure=fig_top10,
                                        style={"width": "100%", "height": "100%"},
                                    ),
                                )
                            ],
                        ),
                    ],
                ),

                # COLONNE DROITE (7/12)
                dbc.Col(
                    width=7,
                    style={"padding": "0"},
                    children=[
                        dbc.Row(
                            style={"height": "50%", "margin": "0"},
                            children=[
                                dbc.Col(
                                    width=12,
                                    style={"padding": "8px", "height": "100%"},
                                    children=dcc.Graph(figure=graph_evolCA,
                                        style={"width": "100%", "height": "100%"}),
                                )
                            ],
                        ),
                        dbc.Row(
                            style={"height": "50%", "margin": "0"},
                            children=[
                                dbc.Col(
                                    width=12,
                                    style={"padding": "8px", "height": "100%"},
                                    children=html.Div(
                                        children=[
                                            html.H4("Table des 100 dernières ventes"),
                                            dash_table.DataTable(
                                                data=data100.to_dict("records"),
                                                columns=[{"name": col, "id": col} for col in data100.columns],
                                                page_size=10,
                                                style_table={"width": "100%", "overflowX": "auto", "height": "250px"},
                                                filter_action="native",
                                                sort_action="native",
                                                style_cell={"textAlign": "left"},
                                            ),
                                        ],
                                        style={"width": "100%", "display": "block"},
                                    ),
                                )
                            ],
                        ),
                    ],
                ),
            ],
        )
    ],
)

if __name__ == "__main__":
    app.run(debug=False)
