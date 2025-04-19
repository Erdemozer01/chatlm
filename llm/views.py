import os
from pathlib import Path

from dash import dcc, html, Input, Output, State, ctx, ALL, MATCH, clientside_callback, DiskcacheManager, \
    ClientsideFunction, no_update
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

# django_plotly_dash ve django importları Django entegrasyonu için gerekli
from django_plotly_dash import DjangoDash
from django.shortcuts import render

# LangChain importları
from langchain_anthropic.chat_models import ChatAnthropic
# Eski importlar (artık kullanılmayacak ama uyumluluk için tutulabilir veya kaldırılabilir)
# from langchain.chains import ConversationChain
# from langchain.memory import ConversationBufferMemory

# Yeni LangChain importları for RunnableWithMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory  # Veya kullandığınız diğer history class'ı

from langchain_core.prompts import PromptTemplate
# LangChain mesaj türleri import edildi (zaten vardı, tekrar eklemeye gerek yoksa silin)
from langchain_core.messages import HumanMessage, AIMessage

from dotenv import load_dotenv

# BASE_DIR, Path(__file__).resolve().parent.parent

external_style = 'https://use.fontawesome.com/releases/v5.8.2/css/all.css'

load_dotenv()

# Ortam değişkeninden API key'i alın
api_key = os.environ.get("ANTHROPIC_API_KEY")

# Model adını tanımlayın
MODEL_NAME = "claude-3-7-sonnet-20250219"  # VEYA geçerli başka bir model

# Prompt template global kalabilir.
prompt = PromptTemplate.from_template("""
The following is a friendly conversation between a human and an AI.
The AI is talkative and provides lots of specific details from its context.
If the AI does not know the answer to a question, it truthfully says it does not know.

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

# --- DjangoDash uygulamasını View fonksiyonunun DIŞINDA oluştur ---
# BU BLOK BURADA OLMALI! ChatLmmView fonksiyonunun DIŞINDA!
# Uygulamanın yalnızca bir kez başlatılması ve kaydedilmesi için bu ZORUNLUDUR.
# KEYERROR ve TypeError gibi state sorunlarını önler.
app = DjangoDash(
    name='ChatLLM',
    external_stylesheets=[dbc.themes.BOOTSTRAP, external_style, custom_css],
    external_scripts=[custom_js],  # clientside.js dosyasının static klasörünüzde olduğundan emin olun
    suppress_callback_exceptions=True
)


# --- DjangoDash uygulamasını oluşturma sonu ---

# --- Bölüm 2 Sonu ---
def ChatLmmView(request):
    # Kullanıcının oturum açıp açmadığını burada kontrol edebilirsiniz
    # if not request.user.is_authenticated:
    #     return redirect('/login/') # Login sayfanıza yönlendirin (Django URL adı veya yolu)

    # app.layout ve tüm callback'ler global 'app' instance'ına bağlıdır

    # Django template'ini render etme işini yapar.
    # {% plotly_app name='ChatLLM' %} tag'i global olarak oluşturulan 'ChatLLM' isimli app'i bulacak.
    # llm.html içinde gizli logout formunu ve clientside.js'i yüklediğinizden emin olun.
    return render(request, 'llm.html')


# --- Bölüm 3 Sonu ---

# --- app.layout tanımı şimdi View fonksiyonunun dışında ---
# Stil yönetimi update_styles callback'inde yapılıyor
app.layout = html.Div(
    id='app-container',
    children=[
        html.Div(
            id='offcanvas-menu',
            children=[
                html.H4('Menü', style={'marginBottom': '20px'}),
                html.Hr(id='menu-hr', style={'margin': '15px 0'}),
                dbc.Button(
                    [html.I(className="fas fa-plus-circle", style={'marginRight': '8px'}), " Yeni Sohbet"],
                    # Seçilen ikon: fas fa-plus-circle
                    id='new-chat-button', n_clicks=0,
                    # Style callback'ten gelecek
                ),
                html.Div(id='offcanvas-menu-bottom', children=[
                    html.A([html.I(className="fas fa-home mr-2"), "Ana Sayfa"], href='/',
                           style={'marginBottom': '10px', 'display': 'block', 'textDecoration': 'none',
                                  'alignItems': 'center'}),  # Seçilen ikon: fas fa-home
                    dcc.Link([html.I(className="fas fa-sliders-h mr-2"), "Ayarlar"], href='/ayarlar',
                             style={'marginBottom': '10px', 'display': 'block', 'textDecoration': 'none',
                                    'alignItems': 'center'}),  # Seçilen ikon: fas fa-sliders-h
                    dcc.Link([html.I(className="fas fa-info-circle mr-2"), "Yardım"], href='/yardim',
                             style={'marginBottom': '10px', 'display': 'block', 'textDecoration': 'none',
                                    'alignItems': 'center'}),  # Seçilen ikon: fas fa-info-circle
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
                                    title="Menüyü aç/kapat"),  # Seçilen ikon: fas fa-bars
                        html.H3('ChatwithLLM', style={'margin': '0', 'flexGrow': 1, 'textAlign': 'center'},
                                className="text-primary"),
                        html.Div(
                            style={'display': 'flex', 'alignItems': 'center'},
                            children=[
                                # --- TEMA DEĞİŞTİR BUTONU ---
                                # İkonu callback döndürecek. Layout'a varsayılan ikonu koyalım (light tema için Ay ikonu).
                                html.Button(
                                    html.I(className="fas fa-moon"),
                                    # Varsayılan ikon (light tema için seçilen ikon: fas fa-moon)
                                    id='dark-mode-button',
                                    n_clicks=0, title="Temayı değiştir",
                                ),
                                # --- TEMA DEĞİŞTİR BUTONU SONU ---
                                # --- LOGOUT BUTONU (CLIENTSIDE TETİKLEYİCİ) ---
                                # Bu buton href veya external_link kullanmıyor.
                                # Sadece tıklama eventini Clientside Callback tetikleyecek ve JS formunu submit edecek.
                                html.Button(  # html.Button kullanıldı, ismini 'logout-button-trigger' yaptık
                                    html.I(className="fas fa-sign-out-alt"),  # Seçilen ikon: fas fa-sign-out-alt
                                    id='logout-button-trigger',
                                    # Bu ID Clientside Callback'te ve style callback'te kullanılacak
                                    title="Çıkış Yap",
                                    n_clicks=0,  # Buton click sayacı
                                    # Style callback'ten
                                ),
                                # --- LOGOUT BUTONU SONU ---
                            ]
                        )
                    ]
                ),  # top-bar sonu

                html.Div(id='chat-log', children=[]),  # chat-log sonu

                html.Div(
                    id='input-area',
                    children=[
                        # --- USER INPUT AREA (dcc.Textarea) ---
                        dcc.Textarea(  # dcc.Input yerine dcc.Textarea kullanıldı
                            id='user-input',  # ID aynı kaldı
                            placeholder='Mesajınızı yazın...',
                            # Style callback'ten yönetilecek
                            # rows=1 # rows özelliği başlangıç satır sayısını belirler, style'daki minHeight ile birlikte kullanılabilir
                        ),
                        # --- END USER INPUT AREA ---
                        html.Button(html.I(className="fas fa-paper-plane"), id='send-button', title="Gönder",
                                    n_clicks=0),  # Seçilen ikon: fas fa-paper-plane
                        html.Button(html.I(className="fas fa-paperclip"), id='attach-file-button', n_clicks=0,
                                    title="Dosya Ekle (İşlevsiz)"),  # Seçilen ikon: fas fa-paperclip
                        dbc.Modal(
                            [
                                dbc.ModalHeader(dbc.ModalTitle("Dosya Ekle")),
                                dbc.ModalBody("Dosya yükleme özelliği henüz aktif değil."),
                                dbc.ModalFooter(dbc.Button("Kapat", id="close-modal-button", className="ml-auto")),
                            ],
                            id="upload-modal", is_open=False,
                        ),
                    ],
                ),  # input-area sonu

                # Store tanımları
                dcc.Store(id='chat-history', data=[], storage_type='session'),
                dcc.Store(id='offcanvas-open', data=False),
                dcc.Store(id='theme-store', data='light'),  # Varsayılan tema light
            ]
        ),  # content-area sonu
    ]
)  # app.layout sonu


# --- Bölüm 4 Sonu ---
# --- CALLBACKS ---
# Callback'ler global 'app' instance'ına bağlıdır (@app.callback veya app.clientside_callback)

@app.callback(  # start_new_chat callback'i
    Output('chat-history', 'data', allow_duplicate=True),
    Output('user-input', 'value', allow_duplicate=True),
    Output('offcanvas-open', 'data', allow_duplicate=True),
    Input('new-chat-button', 'n_clicks'),
    prevent_initial_call=True
)
def start_new_chat(n_clicks):
    if n_clicks is not None and n_clicks > 0:  # None kontrolü eklendi
        # print("DEBUG: Yeni Sohbet butonuna basıldı. Geçmiş ve input temizleniyor, menü kapatılıyor.") # Debug print kaldırıldı
        return [], "", False
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


@app.callback(  # toggle_offcanvas callback'i
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
# Metin ikonlar yerine Font Awesome ikonları döndürecek şekilde güncellendi
@app.callback(
    Output('theme-store', 'data'),
    # Output artık string '🌙'/'☀️' değil, html.I elementi olacak
    Output('dark-mode-button', 'children'),
    Input('dark-mode-button', 'n_clicks'),
    State('theme-store', 'data'),
    prevent_initial_call=True  # İlk yüklemede çalışma (layout'taki varsayılan ikon görünür)
)
def toggle_dark_mode(n_clicks, current_theme):
    # Bu callback sadece tıklama olursa temayı ve ikonu değiştirir.
    # İlk yüklemede layout'taki varsayılan ikon görünür.
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
        app_bg = '#212529';
        app_color = '#f8f9fa'
        chat_bg = '#343a40';
        chat_border = '#495057'
        input_bg = '#495057';
        input_color = '#f8f9fa'
        border_color = '#495057'
        menu_bg = '#343a40';
        menu_color = '#f8f9fa';
        menu_border = '#495057'
        hr_color = '#495057'
        top_bar_bg = '#343a40';
        top_bar_border = '#495057'
        input_area_bg = '#343a40';
        input_area_border = '#495057'
        send_button_bg = '#0d6efd';
        send_button_color = 'white'
        icon_button_color = '#adb5bd'
        link_color = '#64b5f6'
        menu_button_bg = '#2d3135'
        menu_button_color = '#c2e7ff'
    else:  # light mode
        app_bg = '#ffffff';
        app_color = '#212529'
        chat_bg = '#ffffff';
        chat_border = '#dee2e6'
        input_bg = '#ffffff';
        input_color = '#212529'
        border_color = '#dee2e6'
        menu_bg = '#f8f9fa';
        menu_color = '#212529';
        menu_border = '#dee2e6'
        hr_color = '#dee2e6'
        top_bar_bg = '#f8f9fa';
        top_bar_border = '#dee2e6'
        input_area_bg = '#f8f9fa';
        input_area_border = '#dee2e6'
        send_button_bg = '#007bff';
        send_button_color = 'white'
        icon_button_color = '#6c757d'
        link_color = '#007bff'
        menu_button_bg = '#c2e7ff'
        menu_button_color = '#072d4b'

    offcanvas_left = '0px' if is_offcanvas_open else '-250px'
    content_margin_left = '250px' if is_offcanvas_open else '0px'

    app_container_style = {'display': 'flex', 'height': '100vh', 'fontFamily': 'Segoe UI, sans-serif',
                           'backgroundColor': app_bg, 'color': app_color, 'overflow': 'hidden'}
    chat_log_style = {'flexGrow': 1, 'overflowY': 'auto', 'padding': '15px', 'backgroundColor': chat_bg,
                      'borderTop': f'1px solid {chat_border}', 'borderBottom': f'1px solid {chat_border}'}
    content_area_style = {'flexGrow': 1, 'display': 'flex', 'flexDirection': 'column', 'height': '100vh',
                          'marginLeft': content_margin_left, 'transition': 'margin-left 0.3s ease-in-out',
                          'backgroundColor': app_bg}
    # --- USER INPUT AREA STYLE (dcc.Textarea için ayarlandı) ---
    user_input_style = {
        'flexGrow': 1,
        'marginRight': '10px',
        'padding': '15px 15px',
        'borderRadius': '10px',
        'border': f'1px solid {border_color}',
        'backgroundColor': input_bg,
        'color': input_color,
        'minHeight': '80px',  # Minimum yükseklik (istenirse ayarlanabilir)
        # 'resize': 'none',  # <-- Bu satırı silin veya aşağıdaki gibi değiştirin
        'resize': 'vertical',  # <-- Yüksekliği kullanıcı tarafından ayarlanabilir yap
        'boxSizing': 'border-box',
        'lineHeight': '1.4',
        'width': '100%',
    }
    # --- End USER INPUT AREA STYLE ---

    top_bar_style = {'padding': '10px 15px', 'backgroundColor': top_bar_bg,
                     'borderBottom': f'1px solid {top_bar_border}', 'display': 'flex', 'alignItems': 'center',
                     'justifyContent': 'space-between', 'color': app_color}
    input_area_style = {'padding': '15px', 'display': 'flex', 'alignItems': 'center',
                        'borderTop': f'1px solid {input_area_border}', 'backgroundColor': input_area_bg}
    offcanvas_menu_style = {'width': '250px', 'backgroundColor': menu_bg, 'borderRight': f'1px solid {menu_border}',
                            'padding': '20px', 'position': 'fixed', 'top': 0, 'left': offcanvas_left, 'bottom': 0,
                            'zIndex': 1050, 'transition': 'left 0.3s ease-in-out', 'overflowY': 'auto',
                            'color': menu_color, 'display': 'flex', 'flexDirection': 'column'}
    hr_style = {'borderColor': hr_color, 'margin': '15px 0'}

    new_chat_button_style = {
        'marginBottom': '10px', 'display': 'flex', 'alignItems': 'center',
        'textDecoration': 'none', 'textAlign': 'left', 'width': '100%',
        'padding': '10px 15px', 'borderRadius': '16px', 'fontWeight': '500',
        'border': 'none', 'boxShadow': 'none',
        'backgroundColor': menu_button_bg,
        'color': menu_button_color,
    }

    offcanvas_menu_bottom_style = {
        'position': 'absolute', 'bottom': '0', 'left': '0', 'width': '100%',
        'padding': '10px 20px', 'backgroundColor': menu_bg,
        'borderTop': f'1px solid {menu_border}',
        'color': link_color,
    }

    base_icon_button_style = {
        'background': 'none', 'border': 'none', 'cursor': 'pointer',
        'padding': '5px', 'fontSize': '1.2em',
        'lineHeight': '1', 'color': icon_button_color
    }
    toggle_offcanvas_button_style = {**base_icon_button_style, 'marginRight': '10px', 'fontSize': '1.5em'}
    dark_mode_button_style = {**base_icon_button_style, 'fontSize': '1.2em'}
    attach_file_button_style = {**base_icon_button_style, 'fontSize': '1.2em', 'marginLeft': '5px'}
    logout_button_style = {**base_icon_button_style, 'marginLeft': '15px', 'fontSize': '1.2em'}

    send_button_style = {
        'padding': '8px 12px', 'borderRadius': '20px', 'border': 'none',
        'cursor': 'pointer', 'marginLeft': '10px', 'fontSize': '1em',
        'lineHeight': '1', 'backgroundColor': send_button_bg, 'color': send_button_color
    }

    # Return all style dictionaries
    return (
        app_container_style, chat_log_style, offcanvas_menu_style,
        new_chat_button_style,
        offcanvas_menu_bottom_style, content_area_style,
        user_input_style,  # <-- user_input_style döndürülüyor
        top_bar_style, input_area_style,
        toggle_offcanvas_button_style, dark_mode_button_style, send_button_style,
        attach_file_button_style, hr_style, logout_button_style
    )


@app.callback(
    Output('chat-log', 'children'),
    Input('chat-history', 'data'),
    State('theme-store', 'data')
)
def update_chat_log(history_data, theme):
    if not history_data: return []
    chat_messages = []
    for msg_data in history_data:
        sender = msg_data.get("sender");
        text = msg_data.get("text")
        if not sender or not text: continue

        bubble_style = {'padding': '10px 15px', 'borderRadius': '15px', 'marginBottom': '0px', 'maxWidth': '85%',
                        'wordWrap': 'break-word', 'display': 'inline-block', 'textAlign': 'left',
                        'fontSize': '0.95em'}
        container_style = {'overflow': 'auto', 'marginBottom': '10px', 'paddingLeft': '5px', 'paddingRight': '5px'}
        is_user = sender == "Siz"

        if is_user:
            bubble_style['backgroundColor'] = '#007bff' if theme == 'light' else '#0d6efd'
            bubble_style['color'] = 'white'
            container_style['textAlign'] = 'right'
        else:  # Bot
            bubble_style['backgroundColor'] = '#e9ecef' if theme == 'light' else '#495057'
            # Bot bubble metin rengi: açık temada koyu, koyu temada açık
            bubble_style['color'] = '#212529' if theme == 'light' else '#f8f9fa'
            container_style['textAlign'] = 'left'

        # Markdown'ın rengi bubble_style'daki color'dan miras alınmalı
        # CSS dosyasındaki .chat-markdown pre {} stilleri taşmayı yönetir.
        message_content = dcc.Markdown(
            text,
            className='chat-markdown',  # Bu class CSS hedeflemesi için kullanılıyor
            # Markdown içindeki metin, parent elementten (bubble) renk miras alsın
            style={'color': 'inherit', 'fontSize': 'inherit', 'lineHeight': '1.4'}
        )
        bubble_div = html.Div(message_content, style=bubble_style)
        chat_messages.append(html.Div(bubble_div, style=container_style))
    # Otomatik kaydırma için Clientside Callback ekle
    # client_side_callbacks eklendiği yerden emin olun
    return chat_messages


# llm/views.py dosyasında, process_user_input fonksiyonunun başı

@app.callback(
    Output('chat-history', 'data'),
    Output('user-input', 'value'),
    Input('user-input', 'n_submit'),  # Input 1
    Input('send-button', 'n_clicks'),  # Input 2
    State('user-input', 'value'),  # State 1
    State('chat-history', 'data'),  # State 2
    prevent_initial_call=True
)
def process_user_input(n_submit, n_clicks, user_input, history_data):
    # Sadece submit veya button click tetiklediyse devam et
    if not user_input or user_input.strip() == "":
        raise PreventUpdate

    # --- LangChain Setup ve Çalıştırma (RunnableWithMessageHistory ile) ---
    try:
        # LLM modelini başlat
        llm = ChatAnthropic(model_name=MODEL_NAME, temperature=0.1, timeout=60, max_retries=2, api_key=api_key)

        # Mesaj geçmişini dcc.Store'dan yükleyen bir fonksiyon tanımla
        # RunnableWithMessageHistory bu fonksiyonu kullanarak geçmişi alır.
        # Dash oturumu için sabit bir session_id kullanabilirsiniz.
        def get_session_history(session_id: str) -> ChatMessageHistory:
            history = ChatMessageHistory(session_id=session_id)  # ChatMessageHistory nesnesi oluştur
            # dcc.Store'daki mevcut veriyi history nesnesine ekle
            for msg_data in history_data:
                sender = msg_data.get("sender");
                text = msg_data.get("text")
                if sender == "Siz":
                    history.add_user_message(text)
                elif sender == "Bot":
                    history.add_ai_message(text)
            print(f"DEBUG: History data'dan {len(history_data)} mesaj yüklendi.")
            return history

        # Temel Runnable zincirini oluştur (Prompt ve LLM)
        chain = prompt | llm

        # Zinciri RunnableWithMessageHistory ile sar
        # Bu sarmalayıcı, her çağrıda get_session_history fonksiyonunu kullanarak
        # geçmişi zincire (prompt'taki {chat_history} değişkenine) ekler
        runnable_with_history = RunnableWithMessageHistory(
            chain,
            get_session_history=get_session_history,
            input_messages_key="input",  # Prompt'unuzdaki kullanıcı girdisi değişkeni
            history_messages_key="chat_history",  # Prompt'unuzdaki geçmiş değişkeni
        )


    except Exception as e:

        error_message = f"Bot başlatılırken bir hata oluştu: {e}"
        bot_response = error_message  # Hata mesajını bot yanıtı yap
        # Hata durumunda kullanıcı girdisini ve hata mesajını geçmişe ekle
        updated_history = history_data + [{"sender": "Siz", "text": user_input},
                                          {"sender": "Bot", "text": bot_response}]
        return updated_history, ""  # Güncellenmiş geçmişi ve temizlenmiş input'u döndür

    # --- Runnable'ı Çalıştırma (invoke ile) ---
    try:
        # invoke() metodunu çağır. session_id içeren config dictionary'si gerekli.
        # Dash oturumu için sabit bir ID kullanıyoruz.
        config = {"configurable": {"session_id": "my-unique-dash-session-id"}}
        print(f"DEBUG: Runnable.invoke çağrılıyor, config: {config}")

        # invoke metodu, input dictionary'si alır. input_messages_key ile eşleşmeli.
        response = runnable_with_history.invoke(
            {"input": user_input},
            config=config  # Config'i invoke metoduna geçirin
        )

        # invoke'dan dönen yanıt genellikle bir message nesnesidir. İçeriğini alın.
        bot_response = response.content
        print(f"DEBUG: Bot yanıtı alındı (İlk 100 karakter): {bot_response[:100]}...")

    except Exception as e:
        print(f"Hata: LangChain yanıt alınamadı - {e}");
        error_detail = str(e)
        if "404" in error_detail and "not_found_error" in error_detail:
            bot_response = f"Üzgünüm, belirtilen model ('{MODEL_NAME}') bulunamadı veya erişim yetkiniz yok. Lütfen model adını kontrol edin. (Hata Kodu: 404)"
        elif "api_key" in error_detail.lower():
            bot_response = f"Üzgünüm, API anahtarı ile ilgili bir sorun var. (Hata: {e})"
        else:
            bot_response = f"Üzgünüm, bir hata oluştu ve yanıt veremiyorum. (Hata: {e})"
        print(f"DEBUG: Bot hata yanıtı: {bot_response}")

    # --- Geçmişi Güncelle ve Return Et ---
    # Yeni kullanıcı ve bot mesajlarını geçmişe ekle
    new_messages = [{"sender": "Siz", "text": user_input}, {"sender": "Bot", "text": bot_response}]
    updated_history = history_data + new_messages
    print(f"DEBUG: Geçmiş güncellendi. Toplam mesaj sayısı: {len(updated_history)}")

    # Güncellenmiş geçmişi ve input temizleme bilgisini return et
    return updated_history, ""


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


