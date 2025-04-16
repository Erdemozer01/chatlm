import dash_bootstrap_components as dbc




navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Sohbet Geçmişi", href="#")),

    ],
    brand="NavbarSimple",
    brand_href="/",
    color="primary",
    dark=True,

)

