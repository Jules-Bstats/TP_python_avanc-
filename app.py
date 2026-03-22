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

# fonction 


def CA(data):
    """
    La fonction permet de calculer le chiffre d'affaire, c'est à dire prix fois quantité.
    Renvoie le chiffre d'affaire
    """
    return data["Total_price"].sum()

def top10(data):
    """
    La fonction prend en entrée la table de données et vient calculer le CA total 
    après remise et retourne le résultat
    """
    top_10 = data.groupby(["Product_Category","Gender"])[["Total_price"]]

    return top_10.agg('sum').reset_index().sort_values(["Total_price"], ascending = False).head(20)

def indicateur_mois(data, current_month):
    """
    Pour un mois donné, calcule :
    - Le CA du mois en cours (n)
    - Le CA du même mois en n-1
    - La variation du CA entre n et n-1
    - Le nombre de ventes en n et en n-1
    
    Paramètres :
    - data : DataFrame contenant les transactions
    - current_month : mois cible au format datetime (ex: pd.Timestamp("2023-06-01"))
    """
    
    # Définir le mois n-1
    previous_month = current_month - pd.DateOffset(months=1)
    
    # Filtrer les données pour n et n-1
    data_n = data[data['Transaction_Date'].dt.to_period('M') == current_month.to_period('M')]
    data_n1 = data[data['Transaction_Date'].dt.to_period('M') == previous_month.to_period('M')]
    
    # Calcul du CA via ta fonction CA()
    ca_n = CA(data_n)
    ca_n1 = CA(data_n1)
    

    
    # Calcul du nombre de ventes
    nb_ventes_n = len(data_n)
    nb_ventes_n1 = len(data_n1)
    
    # Résultat sous forme de dictionnaire
    resultat = {
    "mois"          : current_month.strftime("%B"),
    "ca_n"          : round(ca_n, 2),
    "ca_n1"         : round(ca_n1, 2),
    "nb_ventes_n"   : nb_ventes_n,
    "nb_ventes_n1"  : nb_ventes_n1,
}
    return resultat

# table 100 dernières ventes
data100 = data.sort_values("Transaction_Date", ascending  = False).head(100)

# Top 10 graphe 
import plotly.express as px 
import pandas as pd

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
                               .sort_values(ascending=False)  # ascending=True car l'axe Y est inversé dans plotly
                               .index.tolist()
    },
    title = "Top 10 des produits qui rapporte le plus par genre", 
    labels = {'Total_price':"Chiffre d'affaires", 'Product_Category': 'Catégorie de produit'}
)

# Graphe évolution CA semaine 
import plotly.express as px

data["semaine"] = data["Transaction_Date"].dt.to_period("W") # On ajoute une colonne "semaine" au data frame en prenant les semaines
ca_hebdo = data.groupby("semaine")["Total_price"].sum().reset_index()
ca_hebdo["semaine"] = ca_hebdo["semaine"].dt.to_timestamp()
ca_hebdo

graph_evolCA = px.line(ca_hebdo, x = "semaine", y = "Total_price", title= "Evolution du chiffre d'affaires par semaine",
              labels= {"semaine": "Semaine", "Total_price": "Chiffre d'affaires (€)"})

# Indicateurs

import plotly.graph_objects as go

indicateur_vente= go.Figure()
indicateur_vente.add_trace(
    go.Indicator(value = indicateur_mois(data, current_month)["nb_ventes_n"], 
        mode = "number+delta"
    )
)

indicateur_vente.update_layout( 
    
    template = {'data' : {'indicator': [{ 
    	'title': {'text': indicateur_mois(data, current_month)["mois"]}, 
        'mode' : "number+delta+gauge",
        'delta' : {'reference': indicateur_mois(data, current_month)["nb_ventes_n1"]}}]
        }
     }
)


import plotly.graph_objects as go

indicateur_CA = go.Figure()
indicateur_CA.add_trace(
    go.Indicator(value = indicateur_mois(data, current_month)["ca_n"], 
        mode = "number+delta", 
        domain = {'row': 1, 'column': 1}
    )
)

indicateur_CA.update_layout( 
    grid = {
        'rows': 1, 'columns': 1, 
        'pattern': "independent"
    },
    template = {'data' : {'indicator': [{ 
    	'title': {'text': indicateur_mois(data, current_month)["mois"]}, 
        'mode' : "number+delta+gauge",
        'delta' : {'reference': indicateur_mois(data, current_month)["ca_n1"]}}]
        }
     }
)

# APP 




app.layout = dbc.Container(
    fluid=True,
    children=[
        dbc.Row([
                dbc.Col(children= html.H2("ECAP Store"),
                        style={"margin": "0", "lineHeight": "50px"},
                        width=6),# Première ligne avec une colonne
                dbc.Col(children= 
                    dcc.Dropdown(
                                options=[{"label": loc, "value": loc} for loc in data["Location"].unique()],
                                value=None,  # aucune valeur sélectionnée par défaut
                                multi=True,
                                searchable=True,
                                placeholder="Sélectionner une ville",
                                disabled=False,
                                style= {'margin':'6px',"marginRight": "10px"}
                ),
                    width=6)
                    ],style={'height':'50px', 'background-color':'skyblue'}
                ),
    
        dbc.Row(
            style={"height": "100vh", "margin": "0"},
            children=[

                # ── COLONNE GAUCHE (5/12) ──────────────────────────────────
                dbc.Col(
                    width=5,
                    style={"padding": "0"},
                    children=[

                        # Ligne 1 gauche : a (indicateur CA) + b (indicateur vente)
                        dbc.Row(
                            style={
                                "height": "30%",
                                "margin":"O"
                            },
                            children=[
                                #  indicateur CA
                                dbc.Col(
                                    width=6,
                                    style={
                                        "padding": "5px",
                                        "height": "100%",
                                    },
                                    children=dcc.Graph(
                                        figure=indicateur_CA,
                                        style={"width": "100%", "height": "100%"},
                                    ),
                                ),
                                # indicateur vente
                                dbc.Col(
                                    width=6,
                                    style={
                                        "padding": "0",
                                        "height": "100%"
                                        },
                                    children=dcc.Graph(
                                        figure=indicateur_vente,
                                        style={"width": "100%","height": "100%"},
                                    ),
                                ),
                            ],
                        ),

                        #fig_top10
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

                # ── COLONNE DROITE (7/12) ──────────────────────────────────
                dbc.Col(
                    width=7,
                    style={"padding": "0"},
                    children=[

                        # Graphe evolution du CA
                        dbc.Row(
                            style={
                                "height": "50%",
                                "margin": "0",
                                
                            },
                            children=[
                                dbc.Col(
                                    width=12,
                                    style={"padding": "8px", "height": "100%"},
                                    children=
                                    dcc.Graph( figure=graph_evolCA,
                                        style={"width": "100%", "height": "100%"}) ,
                                )
                            ],
                        ),

                        # DataTable
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
                                                columns=[
                                                    {"name": col, "id": col}
                                                    for col in data100.columns
                                                ],
                                                page_size=10,
                                                style_table={
                                                    "width": "100%",
                                                    "overflowX": "auto",
                                                    "height": "250px",
                                                },
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
    app.run_server(debug=True, port = 8060, jupyter_mode = "external") 