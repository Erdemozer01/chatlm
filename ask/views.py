from dash import dcc, html, Input, Output, State, ctx, ALL, MATCH, clientside_callback, DiskcacheManager, \
    ClientsideFunction
import dash_bootstrap_components as dbc

from django_plotly_dash import DjangoDash
from django.shortcuts import render

external_style = 'https://use.fontawesome.com/releases/v5.8.2/css/all.css'


def ask(request):

    app = DjangoDash(

        name='ask',
        external_stylesheets=[dbc.themes.BOOTSTRAP, external_style],

        update_title="Güncelleniyor...",
    )

    app.layout = html.Div(
        id='app-container',

        style={
            'display': 'flex',
            'height': '100vh',
            'fontFamily': 'Segoe UI',
        },

        children=[

            html.Div(
                id='offcanvas-menu',

                style={
                    'width': '250px',
                    'backgroundColor': '#f8f9fa',
                    'borderRight': '1px solid #dee2e6',
                    'padding': '20px',
                    'position': 'fixed',
                    'top': 0,
                    'left': '-250px',
                    'bottom': 0,
                    'zIndex': 1000,
                    'transition': 'left 0.3s ease-in-out',
                    'overflowY': 'auto',
                },

                children=[
                    html.H4('Menü', style={'marginBottom': '20px'}),

                    html.Hr(style={'borderColor': '#ddd', 'margin': '15px 0'}),

                    dcc.Link('🏠 Ana Sayfa', href='/',
                             style={'marginBottom': '10px', 'display': 'block', 'color': 'inherit',
                                    'textDecoration': 'none', 'alignItems': 'center'}),
                    dcc.Link('⚙️ Ayarlar', href='/ayarlar',
                             style={'marginBottom': '10px', 'display': 'block', 'color': 'inherit',
                                    'textDecoration': 'none', 'alignItems': 'center'}),
                    dcc.Link('❓ Yardım', href='/yardim',
                             style={'marginBottom': '10px', 'display': 'block', 'color': 'inherit',
                                    'textDecoration': 'none', 'alignItems': 'center'}),
                ]
            ),

            html.Div(

                id='content-area',  # Bu ID'yi ekledik

                style={
                    'flexGrow': 1,
                    'display': 'flex',
                    'flexDirection': 'column',
                    'marginLeft': '0px',
                    'transition': 'margin-left 0.3s ease-in-out',
                },

                children=[

                    html.Div(

                        style={
                            'padding': '15px',
                            'backgroundColor': '#f0f0f0',
                            'borderBottom': '1px solid #ddd',
                            'display': 'flex',
                            'justifyContent': 'space-between',

                        },

                        children=[

                            html.Button(
                                '☰',
                                id='toggle-offcanvas-button',
                                n_clicks=0,
                                style={
                                    'padding': '8px 12px',
                                    'borderRadius': '5px',
                                    "background-color: transparent;"
                                    'color': 'white',
                                    'border': 'none',
                                    'cursor': 'pointer',
                                    'fontSize': '1.2em',
                                    'marginRight': '15px',
                                }
                            ),

                            html.H3('ChatwithLLM', style={'margin': '0'}, className="text-primary"),

                            html.Div(
                                style={'display': 'flex', 'alignItems': 'center', 'gap': '5px'},  # gap ekledik
                                children=[
                                    html.Button(

                                        id='new-chat-button',
                                        n_clicks=0,
                                        className="fa fa-plus text-primary",
                                        style={
                                            'borderRadius': '5px',
                                            'color': 'white',
                                            'border': 'none',
                                            'cursor': 'pointer',
                                            'fontSize': '1em',
                                            "marginRight": "0",
                                            "marginLeft": "0",

                                        }
                                    ),
                                    html.Button(
                                        '🌙',  # İkon (ay)
                                        id='dark-mode-button',
                                        n_clicks=0,
                                        style={
                                            'padding': '8px 15px',
                                            'borderRadius': '5px',
                                            'color': 'white',
                                            'border': 'none',
                                            'cursor': 'pointer',
                                            "marginRight": "0",
                                            "marginLeft": "0",
                                            'fontSize': '1em',  # İkonun boyutunu ayarlayabilirsiniz
                                        }
                                    ),
                                ]
                            ),

                        ]
                    ),

                    html.Div(
                        id='chat-log',
                        style={
                            'flexGrow': 1,
                            'overflowY': 'auto',
                            'padding': '15px',
                            'backgroundColor': '#fff',
                            'color': '#333',
                        }
                    ),

                    html.Div(
                        style={
                            'padding': '15px',
                            'display': 'flex',
                            'borderTop': '1px solid #ddd',
                            'backgroundColor': '#eee',
                        },
                        children=[
                            dcc.Input(
                                id='user-input',
                                type='text',
                                placeholder='Mesajınızı yazın...',
                                style={
                                    'flexGrow': 1,
                                    'marginRight': '10px',
                                    'padding': '10px',
                                    'borderRadius': '5px',
                                    'border': '1px solid #ccc',
                                }
                            ),
                            html.Button(
                                'Gönder',
                                id='send-button',
                                n_clicks=0,
                                style={
                                    'padding': '10px 15px',
                                    'borderRadius': '5px',
                                    'backgroundColor': '#007bff',
                                    'color': 'white',
                                    'border': 'none',
                                    'cursor': 'pointer',
                                }
                            ),
                        ],
                    ),

                    dcc.Store(id='chat-history', data=[]),
                    dcc.Store(id='offcanvas-open', data=False),
                    dcc.Store(id='theme-store', data='light'),

                ]
            ),
        ]
    )

    @app.callback(
        Output('offcanvas-open', 'data'),
        [Input('toggle-offcanvas-button', 'n_clicks')],
        [State('offcanvas-open', 'data')],
        prevent_initial_call=True
    )
    def toggle_offcanvas(n_clicks, is_open):
        return not is_open

    @app.callback(
        Output('theme-store', 'data'),
        [Input('dark-mode-button', 'n_clicks')],
        [State('theme-store', 'data')],
        prevent_initial_call=True
    )
    def toggle_dark_mode(n_clicks, current_theme):
        return 'dark' if n_clicks % 2 == 1 else 'light'

    @app.callback(
        Output('app-container', 'style'),
        Output('chat-log', 'style'),
        Output('offcanvas-menu', 'style'),
        Output('content-area', 'style'),  # Burayı düzelttik
        Output('user-input', 'style'),
        [Input('theme-store', 'data'), Input('offcanvas-open', 'data')],
        prevent_initial_call=True
    )
    def update_styles(theme, is_offcanvas_open):
        # Tema ve menü durumuna göre stilleri belirle
        if theme == 'dark':
            app_bg = '#333'
            app_color = '#f0f0f0'
            chat_bg = '#444'
            input_bg = '#555'
            input_color = '#f0f0f0'
            border_color = '#555'
            menu_bg = '#444'
            menu_color = '#f0f0f0'
            menu_border = '#555'
        else:  # light mode
            app_bg = 'white'
            app_color = 'black'
            chat_bg = '#fff'
            input_bg = '#eee'
            input_color = '#333'
            border_color = '#ddd'
            menu_bg = '#f8f9fa'
            menu_color = 'black'
            menu_border = '#dee2e6'

        offcanvas_left = '0px' if is_offcanvas_open else '-250px'
        content_margin_left = '250px' if is_offcanvas_open else '0px'

        return {  # app-container style
            'display': 'flex',
            'height': '100vh',
            'fontFamily': 'Segoe UI',
            'backgroundColor': app_bg,
            'color': app_color,
        }, {  # chat-log style
            'flexGrow': 1,
            'overflowY': 'auto',
            'padding': '15px',
            'backgroundColor': chat_bg,
            'color': app_color,
        }, {  # offcanvas-menu style
            'width': '250px',
            'backgroundColor': menu_bg,
            'borderRight': f'1px solid {menu_border}',
            'padding': '20px',
            'position': 'fixed',
            'top': 0,
            'left': offcanvas_left,
            'bottom': 0,
            'zIndex': 1000,
            'transition': 'left 0.3s ease-in-out',
            'overflowY': 'auto',
            'color': menu_color,
        }, {  # content-area style
            'flexGrow': 1,
            'display': 'flex',
            'flexDirection': 'column',
            'marginLeft': content_margin_left,
            'transition': 'margin-left 0.3s ease-in-out',
        }, {  # user-input style
            'flexGrow': 1,
            'marginRight': '10px',
            'padding': '10px',
            'borderRadius': '5px',
            'border': f'1px solid {border_color}',
            'backgroundColor': 'white' if theme == 'light' else '#666',
            'color': input_color,
        }

    @app.callback(
        Output('chat-log', 'children'),
        [Input('chat-history', 'data')]
    )
    def update_chat_log(history):
        chat_messages = []
        for msg in history:
            sender, text = msg.split(": ", 1)
            style = {'textAlign': 'left', 'padding': '8px', 'borderRadius': '5px', 'marginBottom': '8px'}
            if sender == "Siz":
                style['backgroundColor'] = '#e6f7ff' if app.layout['theme-store'].data == 'light' else '#555'
                style['color'] = 'black' if app.layout['theme-store'].data == 'light' else '#f0f0f0'
            else:
                style['backgroundColor'] = '#f9f9f9' if app.layout['theme-store'].data == 'light' else '#666'
                style['color'] = 'black' if app.layout['theme-store'].data == 'light' else '#f0f0f0'
                style['borderLeft'] = '3px solid #007bff' if app.layout[
                                                                 'theme-store'].data == 'light' else '3px solid #64b5f6'
            chat_messages.append(html.P(msg, style=style))
        return chat_messages

    @app.callback(
        [Output('chat-history', 'data'),
         Output('user-input', 'value')],
        [Input('send-button', 'n_clicks'),
         Input('user-input', 'n_submit')],
        [State('user-input', 'value'),
         State('chat-history', 'data')],
        prevent_initial_call=True
    )
    def process_user_input(n_clicks, n_submit, user_input, history):
        if not user_input:
            return history, ""

        history.append(f"Siz: {user_input}")
        bot_response = f"Size nasıl yardımcı olabilirim?"
        history.append(f"Bot: {bot_response}")

        return history, ""

    return render(request, 'ask.html')
