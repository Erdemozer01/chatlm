# llm/views.py - COMPLETE AND FINAL CODE
import base64
import io
import os
import datetime

# Dash importları
from dash import dcc, html, Input, Output, State, ctx, ALL, MATCH, clientside_callback, DiskcacheManager, no_update

# Clientside Callback için importlar
from dash import clientside_callback, ClientsideFunction
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

# django_plotly_dash ve django importları
from django_plotly_dash import DjangoDash
from django.shortcuts import render, redirect

# LangChain importları
from langchain_anthropic.chat_models import ChatAnthropic

# ChatMessageHistory için doğru import
from langchain_community.chat_message_histories import ChatMessageHistory

# RunnableWithMessageHistory için import
from langchain_core.runnables.history import RunnableWithMessageHistory

from langchain_core.prompts import PromptTemplate

# LangChain mesaj türleri import edildi
from langchain_core.messages import HumanMessage, AIMessage

from dotenv import load_dotenv

# BASE_DIR, Path(__file__).resolve().parent.parent # Kullanılmıyorsa kaldırılabilir

external_style = 'https://use.fontawesome.com/releases/v5.8.2/css/all.css'  # Font Awesome v5

# .env dosyasını yükle
load_dotenv()

# Ortam değişkeninden API key'i alın
api_key = os.environ.get("ANTHROPIC_API_KEY")

# Model adını tanımlayın
MODEL_NAME = "claude-3-7-sonnet-20250219"  # Claude modelleri görsel yeteneklere sahiptir

# Prompt template global kalabilir. LLM'ye hem metin hem görsel geldiğinde nasıl davranacağını anlatmak önemlidir.
prompt = PromptTemplate.from_template("""
The following is a friendly conversation between a human and an AI.
The AI is talkative and provides lots of specific details from its context.
If the AI does not know the answer to a question, it truthfully says it does not know.

You are capable of analyzing images provided by the user. When an image is provided along with text, interpret both together to answer the user's query about the image.

# === YENİ TALİMAT ===
When providing code examples, ALWAYS format them using Markdown code blocks with the language specified, like this:
```python
# Your Python code here
print("Hello")
Current conversation:
{chat_history}
Human: {input}
AI:
""")

custom_css = "static/css/style.css"
custom_js = "static/js/clientside.js"

# --- DjangoDash uygulamasını oluşturma ---
app = DjangoDash(
    name='ChatLLM',
    external_stylesheets=[dbc.themes.BOOTSTRAP, external_style, custom_css],
    external_scripts=[custom_js],
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ]
)


# --- view ---
def ChatLmmView(request):
    if not request.user.is_authenticated:
        return redirect('/login/')  # Login sayfanıza yönlendirin (Django URL adı veya yolu)
    # --- app.layout ---
    app.layout = html.Div(
        id='app-container',
        children=[
            html.Div(
                id='offcanvas-menu',
                children=[

                    html.H4(f'Hoşgeldiniz, {request.user}', style={'marginBottom': '20px'}),

                    html.Hr(id='menu-hr', style={'margin': '15px 0'}),

                    dbc.Button(
                        [
                            # --- İkonu buradan değiştirin ---
                            html.I(className="fas fa-eraser", style={'marginRight': '8px'}),

                            " Sohbeti Temizle"  # Metin etiketi
                        ],
                        id='new-chat-button',  # ID aynı kalmalı
                        n_clicks=0,
                        # Style callback'ten gelecek
                    ),

                    html.Div(id='offcanvas-menu-bottom', children=[
                        html.A([html.I(className="fas fa-home mr-2"), "Ana Sayfa"], href='/',
                               style={'marginBottom': '10px', 'display': 'block', 'textDecoration': 'none',
                                      'alignItems': 'center'}),
                        dcc.Link([html.I(className="fas fa-sliders-h mr-2"), "Ayarlar"], href='/ayarlar',
                                 style={'marginBottom': '10px', 'display': 'block', 'textDecoration': 'none',
                                        'alignItems': 'center'}),
                        dcc.Link([html.I(className="fas fa-info-circle mr-2"), "Yardım"], href='/yardim',
                                 style={'marginBottom': '10px', 'display': 'block', 'textDecoration': 'none',
                                        'alignItems': 'center'}),
                    ]),
                ]
            ),  # offcanvas-menu sonu

            html.Div(
                id='content-area',
                children=[
                    html.Div(
                        id='top-bar',
                        children=[
                            html.Button(html.I(className="fas fa-bars"), id='toggle-offcanvas-button', n_clicks=0,
                                        title="Menüyü aç/kapat"),

                            html.H3('ChatwithLLM', style={'margin': '0', 'flexGrow': 1, 'textAlign': 'center'},
                                    className="text-primary"),

                            html.Div(
                                style={'display': 'flex', 'alignItems': 'center'},
                                children=[
                                    # --- TEMA DEĞİŞTİR BUTONU ---

                                    html.Button(
                                        html.I(className="fas fa-moon"),
                                        # Varsayılan ikon (light tema için seçilen ikon: fas fa-moon)
                                        id='dark-mode-button',
                                        n_clicks=0, title="Temayı değiştir",
                                    ),

                                    # --- LOGOUT BUTONU (CLIENTSIDE TETİKLEYİCİ) ---

                                    html.Button(
                                        html.I(className="fas fa-sign-out-alt"),  # Seçilen ikon: fas fa-sign-out-alt
                                        id='logout-button-trigger',
                                        # Bu ID Clientside Callback'te ve style callback'te kullanılacak
                                        title="Çıkış Yap",
                                        n_clicks=0,  # Buton click sayacı
                                    ),

                                ]
                            )
                        ]
                    ),  # top-bar sonu

                    html.Div(id='chat-log', children=[]),  # chat-log sonu

                    # --- YENİ RESİM ÖNİZLEME ALANI ---
                    # Yüklenen resim önizlemesinin görüneceği div
                    html.Div(id='image-preview-area', children=[], style={'textAlign': 'center', 'padding': '10px'}),
                    # --- YENİ RESİM ÖNİZLEME ALANI SONU ---

                    html.Div(
                        id='input-area',
                        children=[
                            dbc.Textarea(
                                id='user-input',
                                placeholder='Mesajınızı yazın...',
                                value='',
                            ),
                            # --- END USER INPUT AREA ---
                            html.Button(html.I(className="fas fa-paper-plane"), id='send-button', title="Gönder",
                                        n_clicks=0),

                            # --- DOSYA YÜKLEME BİLEŞENİ (dcc.Upload) ---
                            dcc.Upload(
                                id='upload-image',  # Yeni ID: resim yükleme bileşeni
                                children=html.Button(  # Tıklanabilir alan bir buton olacak
                                    html.I(className="fas fa-paperclip"),
                                    # Ataş ikonu (veya başka bir ikon seçebilirsiniz)
                                    id='attach-file-button',  # Butonun kendi ID'si (stil için kullanılabilir)
                                    title="Resim Yükle",
                                    # Style managed by update_styles (bu butonun stilini update_styles'ta ayarlayacağız)
                                ),
                                # Sadece resim dosyalarını kabul et
                                accept='image/*',
                                # Tek seferde sadece 1 dosya yüklemeye izin ver
                                multiple=False
                            ),
                            # --- DOSYA YÜKLEME BİLEŞENİ SONU ---

                        ],
                    ),  # input-area sonu

                    # --- Store tanımları ---
                    dcc.Store(id='chat-history', data=[], storage_type='session'),  # Chat geçmişi Store'u (KALACAK)
                    dcc.Store(id='offcanvas-open', data=False),  # Menü durumu Store'u (KALACAK)
                    dcc.Store(id='theme-store', data='light'),  # Tema Store'u (KALACAK)
                    dcc.Store(id='uploaded-image-data', data=None),  # Yüklenen resim Store'u (KALACAK)
                    dcc.Store(id='username-store', data=None),  # Kullanıcı adı Store'u (KALACAK)
                ]
            ),  # content-area sonu
        ]
    )  # app.layout sonu

    return render(request, 'llm.html')


# llm/views.py dosyasında, herhangi bir fonksiyonun dışında, örneğin diğer callback'lerden önce veya sonra

# --- Fonksiyon: Resim Önizleme Baloncuğu Oluştur ---
# Yüklenen resim verisini alır ve sohbet baloncuğu formatında bir önizleme elementi döndürür.
def create_image_preview_bubble(base64_image_url, filename, theme):
    # Bu fonksiyon, sadece resim önizlemesini içeren bir mesaj baloncuk elementi oluşturur.
    # Kullanıcı mesajı stili kullanılır.

    # Baloncuk ve Konteyner Stilleri (render_chat_log_with_welcome'daki gibi)
    bubble_style = {
        'padding': '10px 15px', 'borderRadius': '15px', 'marginBottom': '0px', 'maxWidth': '85%',
        'wordWrap': 'break-word', 'display': 'inline-block', 'textAlign': 'left', 'fontSize': '0.95em'
    }
    container_style = {
        'overflow': 'auto', 'marginBottom': '10px', 'paddingLeft': '5px', 'paddingRight': '5px',
        'textAlign': 'right'  # Kullanıcı mesajı hizalaması
    }

    # Tema renklerini kullanıcı balonu için uygula
    bubble_style['backgroundColor'] = '#007bff' if theme == 'light' else '#0d6efd'
    bubble_style['color'] = 'white'  # Yazı rengi (resim balonunda metin olmayabilir ama stil gereği)

    # Resim elementini oluştur
    image_element = html.Img(src=base64_image_url, style={
        'maxWidth': '100%',  # Baloncuğun genişliğini aşmasın
        'height': 'auto',  # Orantısını koru
        'marginTop': '0px',  # Sadece resim varsa üstünde boşluk olmasın
    })

    # Resim altına dosya adı veya bir başlık eklemek isterseniz:
    # filename_caption = html.Div(filename, style={'fontSize': '0.8em', 'color': 'white', 'marginTop': '5px', 'textAlign': 'center'})
    # message_content_element = html.Div([image_element, filename_caption])

    # Şimdilik sadece resim elementini baloncuk içeriği yapalım
    message_content_element = image_element

    # Baloncuk div'i ve konteyner div'i oluştur
    bubble_div = html.Div(message_content_element, style=bubble_style)
    container_div = html.Div(bubble_div, style=container_style)  # Konteyner hizalamayı sağlar

    return container_div  # Oluşturulan baloncuk konteyneri elementini döndür


# --- Fonksiyon Sonu ---


# --- CALLBACKS ---


# llm/views.py dosyasında, start_new_chat fonksiyonunun içinde

@app.callback(
    Output('chat-history', 'clear_data'),
    Output('user-input', 'value', allow_duplicate=True),
    Output('offcanvas-open', 'data', allow_duplicate=True),
    Input('new-chat-button', 'n_clicks'),
    prevent_initial_call=True
)
def start_new_chat(n_clicks):
    if n_clicks is not None and n_clicks > 0:
        return True, "", False
    raise PreventUpdate


@app.callback(  # toggle_modal callback'i
    Output("upload-modal", "is_open"),
    Input("attach-file-button", "n_clicks"),
    Input("close-modal-button", "n_clicks"),
    State("upload-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_modal(open_clicks, close_clicks, is_open):
    if ctx.triggered_id:
        return not is_open
    return is_open


@app.callback(
    Output('offcanvas-open', 'data'),
    Input('toggle-offcanvas-button', 'n_clicks'),
    State('offcanvas-open', 'data'),
    prevent_initial_call=True
)
def toggle_offcanvas(n_clicks, is_open):
    if n_clicks is not None and n_clicks > 0:
        return not is_open
    raise PreventUpdate


# --- Tema Değiştirme Callback'i ---
@app.callback(
    Output('theme-store', 'data'),
    # Output artık string '🌙'/'☀️' değil, html.I elementi olacak
    Output('dark-mode-button', 'children'),
    Input('dark-mode-button', 'n_clicks'),
    State('theme-store', 'data'),
    prevent_initial_call=True  # İlk yüklemede çalışma (layout'taki varsayılan ikon görünür)
)
def toggle_dark_mode(n_clicks, current_theme):
    if n_clicks is None:
        raise PreventUpdate  # İlk yüklemede çalışma

    if n_clicks % 2 != 0:  # Tek tıklama -> dark tema
        new_theme = 'dark'
        button_icon = html.I(className="fas fa-sun")  # Güneş ikonu
    else:  # Çift tıklama -> light tema
        new_theme = 'light'
        button_icon = html.I(className="fas fa-moon")  # Ay ikonu

    return new_theme, button_icon


# --- Stil Güncelleme Callback'i ---
# Tüm dinamik stilleri yönetir. dcc.Textarea için stil güncellendi.
@app.callback(
    Output('app-container', 'style'),  # 1
    Output('chat-log', 'style'),  # 2
    Output('offcanvas-menu', 'style'),  # 3
    Output('new-chat-button', 'style'),  # 4
    Output('offcanvas-menu-bottom', 'style'),  # 5
    Output('content-area', 'style'),  # 6
    Output('user-input', 'style'),  # 7 <-- Output user_input_style için
    Output('top-bar', 'style'),  # 8
    Output('input-area', 'style'),  # 9
    Output('toggle-offcanvas-button', 'style'),  # 10
    Output('dark-mode-button', 'style'),  # 11
    Output('send-button', 'style'),  # 12
    Output('attach-file-button', 'style'),  # 13
    Output('menu-hr', 'style'),  # 14
    Output('logout-button-trigger', 'style'),  # 15 (Logout BUTON stili)
    # --- OUTPUTS SONU ---
    Input('theme-store', 'data'),
    Input('offcanvas-open', 'data')
)
def update_styles(theme, is_offcanvas_open):
    if theme == 'dark':
        app_bg = '#212529'
        app_color = '#f8f9fa'
        chat_bg = '#343a40'
        chat_border = '#495057'
        input_bg = '#495057'
        input_color = '#f8f9fa'
        border_color = '#495057'
        menu_bg = '#343a40'
        menu_color = '#f8f9fa'
        menu_border = '#495057'
        hr_color = '#495057'
        top_bar_bg = '#343a40'
        top_bar_border = '#495057'
        input_area_bg = '#343a40'
        input_area_border = '#495057'
        send_button_bg = '#0d6efd';
        send_button_color = 'white'
        icon_button_color = '#adb5bd'
        link_color = '#64b5f6'
        menu_button_bg = '#2d3135'
        menu_button_color = '#c2e7ff'
    else:  # light mode
        app_bg = '#ffffff'
        app_color = '#212529'
        chat_bg = '#ffffff'
        chat_border = '#dee2e6'
        input_bg = '#ffffff'
        input_color = '#212529'
        border_color = '#dee2e6'
        menu_bg = '#f8f9fa'
        menu_color = '#212529'
        menu_border = '#dee2e6'
        hr_color = '#dee2e6'
        top_bar_bg = '#f8f9fa'
        top_bar_border = '#dee2e6'
        input_area_bg = '#f8f9fa'
        input_area_border = '#dee2e6'
        send_button_bg = '#007bff'
        send_button_color = 'white'
        icon_button_color = '#6c757d'
        link_color = '#007bff'
        menu_button_bg = '#c2e7ff'
        menu_button_color = '#072d4b'

    offcanvas_left = '0px' if is_offcanvas_open else '-250px'
    content_margin_left = '250px' if is_offcanvas_open else '0px'

    # Responsive tasarım için temel değişkenler
    offcanvas_width = '250px'
    offcanvas_width_small = '80%'  # Küçük ekranlarda menü genişliği

    app_container_style = {
        'display': 'flex',
        'height': '100vh',
        'fontFamily': 'Segoe UI, sans-serif',
        'backgroundColor': app_bg,
        'color': app_color,
        'overflow': 'hidden',
        'position': 'relative'  # Pozisyon değişikliği
    }
    chat_log_style = {
        'flexGrow': 1,
        'overflowY': 'auto',
        'padding': '15px',
        'backgroundColor': chat_bg,
        'borderTop': f'1px solid {chat_border}',
        'borderBottom': f'1px solid {chat_border}',
        'wordBreak': 'break-word'  # Uzun metinlerin taşmasını önler
    }

    content_area_style = {
        'flexGrow': 1,
        'display': 'flex',
        'flexDirection': 'column',
        'height': '100vh',
        'marginLeft': content_margin_left,
        'transition': 'margin-left 0.3s ease-in-out',
        'backgroundColor': app_bg,
        'width': '100%',  # Tam genişlik
        'maxWidth': '100%'  # Maksimum genişlik sınırı
    }
    # --- USER INPUT AREA STYLE (dcc.Textarea için ayarlandı) ---
    user_input_style = {
        'flexGrow': 1,
        'marginRight': '10px',
        'padding': '15px 15px',
        'borderRadius': '10px',
        'border': f'1px solid {border_color}',
        'backgroundColor': input_bg,
        'color': input_color,
        'minHeight': '50px',  # Daha küçük minimum yükseklik
        'maxHeight': '150px',  # Maksimum yükseklik sınırı
        'resize': 'vertical',
        'boxSizing': 'border-box',
        'lineHeight': '1.4',
        'width': '100%',
        'fontSize': '0.95rem'  # Daha küçük font size
    }
    # --- End USER INPUT AREA STYLE ---

    top_bar_style = {
        'padding': '10px',
        'backgroundColor': top_bar_bg,
        'borderBottom': f'1px solid {top_bar_border}',
        'display': 'flex',
        'alignItems': 'center',
        'justifyContent': 'space-between',
        'color': app_color,
        'flexWrap': 'wrap',  # Küçük ekranlarda sarma
        'minHeight': '60px'  # Minimum yükseklik
    }

    # Input alanı için responsive stil
    input_area_style = {
        'padding': '10px',  # Daha az padding
        'display': 'flex',
        'alignItems': 'center',
        'borderTop': f'1px solid {input_area_border}',
        'backgroundColor': input_area_bg,
        'flexWrap': 'nowrap',  # Sarma yok
        'position': 'relative',  # Pozisyon ayarı
        'gap': '5px'  # Elementler arası boşluk
    }

    # Offcanvas menü için responsive stil
    offcanvas_menu_style = {
        'width': offcanvas_width,
        'backgroundColor': menu_bg,
        'borderRight': f'1px solid {menu_border}',
        'padding': '20px',
        'position': 'fixed',
        'top': 0,
        'left': offcanvas_left,
        'bottom': 0,
        'zIndex': 1050,
        'transition': 'left 0.3s ease-in-out',
        'overflowY': 'auto',
        'color': menu_color,
        'display': 'flex',
        'flexDirection': 'column',
        'boxShadow': '2px 0 10px rgba(0,0,0,0.1)',  # Gölge ekle
        # Küçük ekranlarda genişliği ayarla
        'media_query': {
            'width': offcanvas_width_small
        }
    }

    hr_style = {
        'borderColor': hr_color,
        'margin': '15px 0',
        'width': '100%'  # Tam genişlik
    }

    new_chat_button_style = {
        'marginBottom': '10px',
        'display': 'flex',
        'alignItems': 'center',
        'textDecoration': 'none',
        'textAlign': 'left',
        'width': '100%',
        'padding': '10px 15px',
        'borderRadius': '16px',
        'fontWeight': '500',
        'border': 'none',
        'boxShadow': 'none',
        'backgroundColor': menu_button_bg,
        'color': menu_button_color,
        'fontSize': '0.9rem'  # Daha küçük font
    }

    offcanvas_menu_bottom_style = {
        'position': 'absolute',
        'bottom': '0',
        'left': '0',
        'width': '100%',
        'padding': '10px 20px',
        'backgroundColor': menu_bg,
        'borderTop': f'1px solid {menu_border}',
        'color': link_color,
        'zIndex': 1  # z-index ekle
    }

    base_icon_button_style = {
        'background': 'none',
        'border': 'none',
        'cursor': 'pointer',
        'padding': '8px',  # Daha büyük tıklama alanı
        'fontSize': '1.2em',
        'lineHeight': '1',
        'color': icon_button_color,
        'borderRadius': '50%',  # Yuvarlak butonlar
        'display': 'flex',
        'alignItems': 'center',
        'justifyContent': 'center',
        'minWidth': '36px',  # Minimum genişlik
        'minHeight': '36px',  # Minimum yükseklik
        'transition': 'background-color 0.2s'  # Hover efekti için geçiş
    }

    toggle_offcanvas_button_style = {
        **base_icon_button_style,
        'marginRight': '10px',
        'fontSize': '1.5em',
        'zIndex': 2  # Üstte kalması için z-index
    }

    dark_mode_button_style = {
        **base_icon_button_style,
        'fontSize': '1.2em',
        'marginLeft': '5px'  # Biraz boşluk ekle
    }

    attach_file_button_style = {
        **base_icon_button_style,
        'fontSize': '1.2em',
        'marginLeft': '5px'
    }

    logout_button_style = {
        **base_icon_button_style,
        'marginLeft': '10px',
        'fontSize': '1.2em'
    }

    send_button_style = {
        'padding': '8px 12px',
        'borderRadius': '20px',
        'border': 'none',
        'cursor': 'pointer',
        'marginLeft': '5px',  # Azaltılmış margin
        'fontSize': '1em',
        'lineHeight': '1',
        'backgroundColor': send_button_bg,
        'color': send_button_color,
        'display': 'flex',
        'alignItems': 'center',
        'justifyContent': 'center',
        'minWidth': '36px',  # Minimum genişlik
        'minHeight': '36px',  # Minimum yükseklik
        'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'  # Hafif gölge
    }

    # Return all style dictionaries
    return (
        app_container_style, chat_log_style, offcanvas_menu_style,
        new_chat_button_style,
        offcanvas_menu_bottom_style, content_area_style,
        user_input_style,
        top_bar_style, input_area_style,
        toggle_offcanvas_button_style, dark_mode_button_style, send_button_style,
        attach_file_button_style, hr_style, logout_button_style
    )


# llm/views.py dosyasında, önceki add_welcome_message_on_load ve update_chat_log callback'lerinin yerine gelecek

# --- CALLBACK: Chat Log'u Çizme ve Karşılama Mesajı Ekleme ---
# Bu callback hem mesajları çizer hem de ilk yüklendiğinde karşılama mesajını ekler.
@app.callback(
    Output('chat-log', 'children'),  # 1. Çıktı: Sohbet baloncuklarının listesi
    Output('chat-history', 'data', allow_duplicate=True),
    # 2. Çıktı: chat-history store'unu güncelle (Karşılama mesajını eklemek için)
    Input('chat-history', 'data'),  # Tetikleyici: chat-history data değiştiğinde (ilk yükleme dahil)
    State('theme-store', 'data'),  # State: Mevcut tema bilgisini al
    State('username-store', 'data'),  # State: Kullanıcı adını al

    prevent_initial_call='initial_duplicate'  # İlk yüklemede de çalışmasına izin ver
)
def render_chat_log_with_welcome(history_data, theme, username):
    # Debug print statements
    print("DEBUG: >>> render_chat_log_with_welcome callback tetiklendi <<<")
    print(
        f"DEBUG: >>> render_chat_log_with_welcome received history_data (length {len(history_data) if history_data is not None else 'None'}): {history_data[:5] if history_data is not None else 'None'}{'...' if history_data is not None and len(history_data) > 5 else ''} <<<")
    print(f"DEBUG: >>> render_chat_log_with_welcome received username: {username} <<<")

    # Karşılama mesajının yapısını tanımla
    welcome_text = "Merhaba! Size nasıl yardımcı olabilirim? Ben bir yapay zeka asistanıyım."
    if username:
        welcome_text = f"Merhaba, {username}! Size nasıl yardımcı olabilirim? Ben bir yapay zeka asistanıyım."
    welcome_message_item = {"sender": "Bot", "text": welcome_text, "image_url": None}

    # Check if history data is None or empty OR if the first message is NOT the welcome message
    history_is_empty_or_none = history_data is None or len(history_data) == 0
    first_message_is_not_welcome = True  # Varsayılan olarak ilk mesaj karşılama mesajı değil

    if not history_is_empty_or_none:
        if isinstance(history_data, list) and len(history_data) > 0:
            first_message = history_data[0]
            if isinstance(first_message, dict) and \
                    first_message.get("sender") == welcome_message_item["sender"] and \
                    first_message.get("text") == welcome_message_item["text"] and \
                    first_message.get("image_url") == welcome_message_item["image_url"]:
                first_message_is_not_welcome = False

    updated_history = history_data  # Başlangıçta alınan history_data ile başla

    # Eğer geçmiş boşsa VEYA (geçmiş boş değilse AMA ilk mesaj karşılama mesajı değilse)
    # karşılama mesajını eklememiz gerekiyor (veya en başa almamız).
    if history_is_empty_or_none or first_message_is_not_welcome:
        print(
            "DEBUG: render_chat_log_with_welcome: Gecmis bos/None veya ilk mesaj karsilama degil, karsilama mesaji ekleniyor.")
        # Yeni geçmiş listesi oluştur: Karşılama mesajıyla başla
        if history_is_empty_or_none:
            updated_history = [welcome_message_item]  # Sadece karşılama mesajı içeren liste
        else:
            # Karşılama mesajını mevcut geçmişin başına ekle
            # Eğer history_data None ise, bunu [] olarak varsay ve karşılama mesajını ekle
            current_history_list = history_data if history_data is not None else []
            updated_history = [welcome_message_item] + current_history_list

        print("DEBUG: render_chat_log_with_welcome: Karsilama mesaji ile guncellenmis gecmis donduruluyor.")
        # Hem oluşturulan/güncellenen baloncukları döndür (aşağıda çizilecek) HEM de güncellenmiş geçmişi Store'a yaz
        # Çıktı 1: chat-log children (render edilecek baloncuklar)
        # Çıktı 2: chat-history data (güncellenmiş geçmiş)
        chat_messages = []  # Render edilecek baloncuklar

        # Güncellenmiş history'yi çizmeye devam et
        if updated_history is not None:  # Güncellenmiş history None olmamalı, ama güvenlik için
            print("DEBUG: Proceeding to build chat bubbles from updated_history (welcome added).")
            # ... Geri kalan baloncuk oluşturma döngüsü ve return chat_messages (updated_history kullanarak) ...
            for msg_data in updated_history:
                sender = msg_data.get("sender")
                text = msg_data.get("text")
                image_url = msg_data.get("image_url")
                timestamp_str = msg_data.get("timestamp")

                if not sender or (not text and not image_url and not timestamp_str):
                    continue

                bubble_style = {'padding': '10px 15px', 'borderRadius': '15px', 'marginBottom': '0px',
                                'maxWidth': '85%', 'wordWrap': 'break-word', 'display': 'inline-block',
                                'textAlign': 'left', 'fontSize': '0.95em'}
                container_style = {'overflow': 'auto', 'marginBottom': '10px', 'paddingLeft': '5px',
                                   'paddingRight': '5px'}
                is_user = sender == "Siz"
                if is_user:
                    bubble_style['backgroundColor'] = '#007bff' if theme == 'light' else '#0d6efd'
                    bubble_style['color'] = 'white'
                    container_style['textAlign'] = 'right'
                else:
                    bubble_style['backgroundColor'] = '#e9ecef' if theme == 'light' else '#495057'
                    bubble_style['color'] = '#212529' if theme == 'light' else '#f8f9fa'
                    container_style['textAlign'] = 'left'

                message_parts = []
                if text: message_parts.append(dcc.Markdown(text, className='chat-markdown',
                                                           style={'color': 'inherit', 'fontSize': 'inherit',
                                                                  'lineHeight': '1.4'}))
                if image_url: message_parts.append(html.Img(src=image_url, style={'maxWidth': '100%', 'height': 'auto',
                                                                                  'marginTop': '5px' if text else '0px'}))
                if timestamp_str:
                    try:
                        timestamp_dt = datetime.datetime.fromisoformat(
                            timestamp_str); formatted_timestamp = timestamp_dt.strftime('%H:%M')
                    except ValueError:
                        formatted_timestamp = "Geçersiz Zaman"; print(
                            f"ERROR: Failed to parse timestamp string: {timestamp_str}")
                    timestamp_element = html.Div(formatted_timestamp,
                                                 style={'fontSize': '0.7em', 'color': '#888', 'marginTop': '5px',
                                                        'textAlign': 'right' if is_user else 'left', })
                    message_parts.append(timestamp_element)

                if not message_parts: continue
                if len(message_parts) > 1:
                    message_content_element = html.Div(message_parts)
                elif message_parts:
                    message_content_element = message_parts[0]
                else:
                    continue
                bubble_div = html.Div(message_content_element, style=bubble_style)
                chat_messages.append(html.Div(bubble_div, style=container_style))
                print("DEBUG: Bubble created and added to chat_messages list.")

        print(f"DEBUG: render_chat_log_with_welcome returning {len(chat_messages)} bubbles and updated history.")
        # Döndür: Çizilecek baloncuklar listesi VE güncellenmiş geçmiş listesi (Store'a yazılacak)
        return chat_messages, updated_history  # İKİ DEĞER DÖNDÜR

    else:
        # Geçmiş boş değil VE ilk mesaj karşılama mesajı. Zaten olması gereken durumda.
        # Sadece mevcut geçmişi çiz. Geçmişi Store'da güncellemeye gerek yok (no_update kullan)
        print("DEBUG: render_chat_log_with_welcome: Gecmis zaten dolu ve karsilama mesaji basta, sadece ciziliyor.")
        chat_messages = []  # Render edilecek baloncuklar

        # Mevcut history_data'yı çiz
        if history_data is not None:  # history_data None olmamalı
            print(
                "DEBUG: Proceeding to build chat bubbles from received history_data (no welcome message added this run).")
            # ... Geri kalan baloncuk oluşturma döngüsü ve return chat_messages (history_data kullanarak) ...
            for msg_data in history_data:
                sender = msg_data.get("sender")
                text = msg_data.get("text")
                image_url = msg_data.get("image_url")
                timestamp_str = msg_data.get("timestamp")

                if not sender or (not text and not image_url and not timestamp_str):
                    continue

                bubble_style = {'padding': '10px 15px', 'borderRadius': '15px', 'marginBottom': '0px',
                                'maxWidth': '85%', 'wordWrap': 'break-word', 'display': 'inline-block',
                                'textAlign': 'left', 'fontSize': '0.95em'}
                container_style = {'overflow': 'auto', 'marginBottom': '10px', 'paddingLeft': '5px',
                                   'paddingRight': '5px'}
                is_user = sender == "Siz"
                if is_user:
                    bubble_style['backgroundColor'] = '#007bff' if theme == 'light' else '#0d6efd'
                    bubble_style['color'] = 'white'
                    container_style['textAlign'] = 'right'
                else:
                    bubble_style['backgroundColor'] = '#e9ecef' if theme == 'light' else '#495057'
                    bubble_style['color'] = '#212529' if theme == 'light' else '#f8f9fa'
                    container_style['textAlign'] = 'left'

                message_parts = []
                if text: message_parts.append(dcc.Markdown(text, className='chat-markdown',
                                                           style={'color': 'inherit', 'fontSize': 'inherit',
                                                                  'lineHeight': '1.4'}))
                if image_url: message_parts.append(html.Img(src=image_url, style={'maxWidth': '100%', 'height': 'auto',
                                                                                  'marginTop': '5px' if text else '0px'}))
                if timestamp_str:
                    try:
                        timestamp_dt = datetime.datetime.fromisoformat(
                            timestamp_str); formatted_timestamp = timestamp_dt.strftime('%H:%M')
                    except ValueError:
                        formatted_timestamp = "Geçersiz Zaman"; print(
                            f"ERROR: Failed to parse timestamp string: {timestamp_str}")
                    timestamp_element = html.Div(formatted_timestamp,
                                                 style={'fontSize': '0.7em', 'color': '#888', 'marginTop': '5px',
                                                        'textAlign': 'right' if is_user else 'left', })
                    message_parts.append(timestamp_element)

                if not message_parts: continue
                if len(message_parts) > 1:
                    message_content_element = html.Div(message_parts)
                elif message_parts:
                    message_content_element = message_parts[0]
                else:
                    continue
                bubble_div = html.Div(message_content_element, style=bubble_style)
                chat_messages.append(html.Div(bubble_div, style=container_style))
                print("DEBUG: Bubble created and added to chat_messages list.")

        print(f"DEBUG: render_chat_log_with_welcome returning {len(chat_messages)} bubbles and no_update for history.")
        # Döndür: Çizilecek baloncuklar listesi VE history Store'u için no_update
        return chat_messages, no_update  # İKİ DEĞER DÖNDÜR


# --- END render_chat_log_with_welcome callback code ---


# llm/views.py dosyasında, diğer callback fonksiyonlarının altında

# datetime modülünün dosyanın başında import edildiğinden emin olun: import datetime
@app.callback(
    Output('chat-history', 'data'),
    Output('user-input', 'value'),
    Output('uploaded-image-data', 'data', allow_duplicate=True),
    Output('image-preview-area', 'children', allow_duplicate=True),
    Input('user-input', 'n_submit'),
    Input('send-button', 'n_clicks'),
    State('user-input', 'value'),
    State('chat-history', 'data'),
    State('uploaded-image-data', 'data'),
    prevent_initial_call=True
)
def process_user_input(n_submit, n_clicks, user_input, history_data, uploaded_image_data):
    # Tetikleyici kontrolü
    is_triggered_by_submit_or_click = False
    if n_submit is not None and n_submit > 0:
        is_triggered_by_submit_or_click = True
    if n_clicks is not None and n_clicks > 0:
        is_triggered_by_submit_or_click = True

    if not is_triggered_by_submit_or_click:
        raise PreventUpdate

    # Görsel veya metin olup olmadığını kontrol et
    has_text = user_input and user_input.strip() != ""
    has_image = uploaded_image_data is not None and 'base64' in uploaded_image_data and uploaded_image_data['base64']

    # Debug için log ekleyin
    print(f"DEBUG: Kullanıcı mesajı - Metin var mı: {has_text}, Görsel var mı: {has_image}")

    if not has_text and not has_image:
        raise PreventUpdate  # Gönderilecek bir şey yok

    # Zaman damgası oluştur
    current_time = datetime.datetime.now().isoformat()

    # LLM için çok modlu içerik hazırla
    llm_input_content = []
    image_url = None

    # Metin varsa ekle
    if has_text:
        llm_input_content.append({"type": "text", "text": user_input})
        print(f"DEBUG: Metin içeriği eklendi: {user_input[:50]}...")

    # Görsel varsa ekle
    if has_image:
        try:
            content_type_img = uploaded_image_data.get('content_type', 'image/jpeg')
            base64_string_img = uploaded_image_data['base64']

            # Base64 string'in geçerli olduğunu kontrol et
            if not base64_string_img or len(base64_string_img) < 10:
                print("HATA: Geçersiz base64 verisi")
                raise ValueError("Geçersiz görsel verisi")

            image_url = f"data:{content_type_img};base64,{base64_string_img}"

            # LLM için görsel içeriği ekle
            llm_input_content.append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })

            print(f"DEBUG: Görsel içeriği eklendi, content_type: {content_type_img}, base64 uzunluğu: {len(base64_string_img)}")
        except Exception as e:
            print(f"HATA: Görsel eklenirken hata oluştu: {e}")
            # Hata durumunda bile devam et, en azından metin mesajını gönder

    if not llm_input_content:
        print("DEBUG: İçerik oluşturulamadı, atlanıyor.")
        raise PreventUpdate
    try:
        # LLM modelini başlat
        llm = ChatAnthropic(model_name=MODEL_NAME, temperature=0.1, timeout=60, max_retries=2, api_key=api_key)

        # Chat geçmişi objesini oluştur
        chat_history_object = ChatMessageHistory()

        # Geçmiş verisini ekle
        if history_data is not None:
            for msg_data in history_data:
                hist_sender = msg_data.get("sender")
                hist_text = msg_data.get("text")
                hist_image_url = msg_data.get("image_url")

                # Geçmişteki mesajın içeriğini hazırla
                hist_content_parts = []
                if hist_text:
                    hist_content_parts.append({"type": "text", "text": hist_text})
                if hist_image_url:
                    hist_content_parts.append({"type": "image_url", "image_url": {"url": hist_image_url}})

                # ChatMessageHistory'ye ekle
                if hist_sender == "Siz" and hist_content_parts:
                    chat_history_object.add_message(HumanMessage(content=hist_content_parts))
                elif hist_sender == "Bot" and hist_text:
                    chat_history_object.add_message(AIMessage(content=hist_text))

        # Runnable zinciri tanımla
        chain = prompt | llm

        # RunnableWithMessageHistory ile zinciri sar
        runnable_with_history = RunnableWithMessageHistory(
            chain,
            get_session_history=lambda session_id: chat_history_object,
            input_messages_key="input",
            history_messages_key="chat_history",
        )

        # Debug için log ekle
        print("DEBUG: LLM ve zincir hazırlandı, istek gönderiliyor...")

        # LLM'ye isteği gönder
        config = {"configurable": {"session_id": "my-unique-dash-session-id"}}
        response = runnable_with_history.invoke(
            {"input": llm_input_content},
            config=config
        )

        # Yanıtı al
        bot_response = response.content
        print(f"DEBUG: LLM yanıtı alındı, uzunluk: {len(bot_response)}")

    except Exception as e:
        print(f"HATA: LLM işlemi sırasında hata: {e}")
        error_detail = str(e)
        bot_response = f"Üzgünüm, bir hata oluştu: {error_detail}"

    # Geçmişi güncelle
    user_message_history_item = {
        "sender": "Siz",
        "text": user_input if has_text else "",
        "image_url": image_url if has_image else None,
        "timestamp": current_time
    }

    bot_message_history_item = {
        "sender": "Bot",
        "text": bot_response,
        "image_url": None,
        "timestamp": datetime.datetime.now().isoformat()
    }

    new_messages = [user_message_history_item, bot_message_history_item]

    # Geçmişi güncelle
    if history_data is None:
        updated_history = new_messages
    else:
        updated_history = history_data + new_messages

    # Temizleme işlemleri
    clear_image_data = None  # Görsel verisini temizle
    clear_preview_children = []  # Önizleme alanını temizle

    # Sonuçları döndür
    return updated_history, "", clear_image_data, clear_preview_children



# --- process_user_input callback code sonu ---


# llm/views.py dosyasında, process_uploaded_image fonksiyonunun tanımı

# create_image_preview_bubble fonksiyonunu silebilirsiniz, artık kullanılmıyor.
# def create_image_preview_bubble(...): ... # <-- BU FONKSİYONU SİLİN


# --- CALLBACK: Yüklenen Resmi İşleme ---
@app.callback(
    Output('uploaded-image-data', 'data', allow_duplicate=True),
    Output('image-preview-area', 'children'),
    Input('upload-image', 'contents'),
    State('upload-image', 'filename'),
    State('upload-image', 'last_modified'),
    prevent_initial_call=True
)
def process_uploaded_image(contents, filename, last_modified):
    if contents is not None:
        try:
            # Debug için log ekleyin
            print(f"DEBUG: Görsel yükleniyor: {filename}")

            # contents Base64 formatında gelir
            content_type, content_string = contents.split(',')

            # Base64 verisini doğru şekilde kaydet
            image_data_to_store = {
                'base64': content_string,
                'filename': filename,
                'content_type': content_type
            }

            # Tam data URL'i oluştur
            base64_image_url = f"data:{content_type};base64,{content_string}"

            # Daha belirgin bir önizleme elementi oluştur
            image_preview_element = html.Div([
                html.H6(f"Yüklenen Görsel: {filename}", style={
                    'marginBottom': '10px',
                    'fontSize': '0.9rem',
                    'color': '#666'
                }),
                html.Img(src=base64_image_url, style={
                    'maxWidth': '250px',
                    'height': 'auto',
                    'margin': '0 auto',
                    'display': 'block',
                    'border': '1px solid #ddd',
                    'borderRadius': '4px',
                    'padding': '4px'
                })
            ], style={'textAlign': 'center', 'padding': '10px'})

            print("DEBUG: Görsel önizleme oluşturuldu")
            return image_data_to_store, image_preview_element

        except Exception as e:
            print(f"HATA: Görsel işlenirken sorun oluştu: {e}")
            error_element = html.Div([
                html.H6("Görsel Yükleme Hatası", style={'color': 'red'}),
                html.P(f"Hata: {str(e)}")
            ])
            return None, error_element

    return None, []


# --- CALLBACK SONU ---

app.clientside_callback(
    ClientsideFunction(
        namespace='clientside',  # static/js/clientside.js içinde tanımlı namespace
        function_name='submitLogoutForm'  # static/js/clientside.js içindeki fonksiyon adı
    ),
    Output('logout-button-trigger', 'n_clicks'),  # <-- Output olarak butonun kendi n_clicks'i
    [Input('logout-button-trigger', 'n_clicks')],  # <-- Input olarak butonun n_clicks'i (Liste içinde!)
    prevent_initial_call=True  # Clientside callback argümanı
)

# llm/views.py dosyasında, diğer callback'lerin altında
