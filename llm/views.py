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
from langchain_community.chat_message_histories import ChatMessageHistory # Veya kullandığınız diğer history class'ı

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
js = "static/js/clientside.js"


# Django View Fonksiyonu
def ChatLmmView(request):
    app = DjangoDash(
        name='ChatLLM',
        external_stylesheets=[dbc.themes.BOOTSTRAP, external_style, custom_css],
        external_scripts=[js],
        suppress_callback_exceptions=True
    )

    # === LAYOUT TANIMI ===
    # ÖNEMLİ: Aşağıdaki bileşenlerin inline 'style' tanımlarından
    # color, backgroundColor, border gibi dinamik olması gerekenler SİLİNMELİDİR!
    # (Bu stil yönetimi artık update_styles callback'inde yapılıyor)
    app.layout = html.Div(
        id='app-container',
        children=[
            html.Div(
                id='offcanvas-menu',
                children=[
                    html.H4('Menü', style={'marginBottom': '20px'}),
                    # Hr için ID eklenmiş
                    html.Hr(id='menu-hr', style={'margin': '15px 0'}),
                    dbc.Button(
                        [html.I(className="fas fa-plus", style={'marginRight': '8px'}), " Yeni Sohbet"],
                        id='new-chat-button',
                        style={  # Sadece GÖRÜNÜM ile ilgili sabit stiller
                            'marginBottom': '10px', 'display': 'flex', 'alignItems': 'center',
                            'textDecoration': 'none', 'textAlign': 'left', 'width': '100%',
                            'padding': '10px 15px', 'borderRadius': '16px', 'fontWeight': '500',
                            'border': 'none'
                            # Dinamik renk/arkaplan/border callback'ten gelecek
                        },
                        n_clicks=0
                    ),
                    html.Div(
                        id='offcanvas-menu-bottom',
                        children=[
                            html.A(
                                [html.I(className="fas fa-home mr-2"), "Ana Sayfa"], href='/',
                                # Ana sayfa URL'sini güncelleyin
                                # Renk stili kaldırıldı, callback yönetecek
                                style={'marginBottom': '10px', 'display': 'block',
                                       'textDecoration': 'none', 'alignItems': 'center'}
                            ),
                            dcc.Link(
                                [html.I(className="fas fa-cog mr-2"), "Ayarlar"], href='/ayarlar',
                                # Ayarlar URL'sini güncelleyin
                                # Renk stili kaldırıldı, callback yönetecek
                                style={'marginBottom': '10px', 'display': 'block',
                                       'textDecoration': 'none', 'alignItems': 'center'}
                            ),
                            dcc.Link(
                                [html.I(className="fas fa-question-circle mr-2"), "Yardım"], href='/yardim',
                                # Yardım URL'sini güncelleyin
                                # Renk stili kaldırıldı, callback yönetecek
                                style={'marginBottom': '10px', 'display': 'block',
                                       'textDecoration': 'none', 'alignItems': 'center'}
                            ),
                        ]
                    ),
                ]
            ),  # offcanvas-menu sonu

            html.Div(
                id='content-area',
                children=[
                    html.Div(
                        id='top-bar',
                        children=[
                            html.Button(
                                html.I(className="fas fa-bars"),  # FontAwesome ikon
                                id='toggle-offcanvas-button', n_clicks=0, title="Menüyü aç/kapat",
                                # Stil callback'ten
                            ),
                            html.H3('ChatwithLLM', style={'margin': '0', 'flexGrow': 1, 'textAlign': 'center'},
                                    className="text-primary"),
                            html.Div(
                                style={'display': 'flex', 'alignItems': 'center'},
                                children=[
                                    html.Button(
                                        '🌙',  # İkon toggle_dark_mode ile değişecek
                                        id='dark-mode-button', n_clicks=0, title="Temayı değiştir",
                                        # Stil callback'ten
                                    ),
                                    # --- LOGOUT LINKI EKLENİYOR ---
                                    dbc.Button(
                                        html.I(className="fas fa-sign-out-alt", style={'marginRight': '5px'}),
                                        # Çıkış ikonu
                                        href='accounts/logout/',  # Django projenizdeki çıkış URL'si
                                        id='logout-link',
                                        title="Çıkış Yap",
                                        external_link=True,  # Burası eklendi! Standart tarayıcı navigasyonu için
                                        # Stil callback'ten yönetilecek
                                        style={'textDecoration': 'none', 'marginLeft': '15px'}
                                        # Temel aralık, callback ezecek
                                    ),
                                    # --- LOGOUT LINKI SONU ---
                                ]
                            )
                        ]
                    ),  # top-bar sonu

                    html.Div(id='chat-log', children=[]),  # chat-log sonu

                    html.Div(
                        id='input-area',
                        children=[
                            dcc.Input(
                                id='user-input', type='text', placeholder='Mesajınızı yazın...',
                                # Stil callback'ten
                            ),
                            html.Button(
                                html.I(className="fas fa-paper-plane"), id='send-button',
                                title="Gönder", n_clicks=0,
                                # Stil callback'ten
                            ),
                            html.Button(
                                html.I(className="fas fa-paperclip"), id='attach-file-button',
                                n_clicks=0, title="Dosya Ekle (İşlevsiz)",
                                # Stil callback'ten
                            ),
                            dbc.Modal(  # Modal içeriği aynı
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
                    dcc.Store(id='chat-history', data=[], storage_type='session'),  # Session storage daha iyi
                    dcc.Store(id='offcanvas-open', data=False),
                    dcc.Store(id='theme-store', data='light'),
                ]
            ),  # content-area sonu
        ]
    )  # app.layout sonu

    # ----------- CALLBACKS -----------

    # *** YENİ CALLBACK: Yeni Sohbet Butonu İşleyici ***
    @app.callback(
        Output('chat-history', 'data', allow_duplicate=True),
        Output('user-input', 'value', allow_duplicate=True),
        Output('offcanvas-open', 'data', allow_duplicate=True),
        Input('new-chat-button', 'n_clicks'),
        prevent_initial_call=True
    )
    def start_new_chat(n_clicks):
        if n_clicks:
            print("DEBUG: Yeni Sohbet butonuna basıldı. Geçmiş ve input temizleniyor, menü kapatılıyor.")
            return [], "", False
        else:
            raise PreventUpdate

    # Modal'ı Açma/Kapatma (Değişiklik yok)
    @app.callback(
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

    # Offcanvas Menüyü Açma/Kapatma (Değişiklik yok)
    @app.callback(
        Output('offcanvas-open', 'data'),
        Input('toggle-offcanvas-button', 'n_clicks'),
        State('offcanvas-open', 'data'),
        prevent_initial_call=True
    )
    def toggle_offcanvas(n_clicks, is_open):
        return not is_open

    # Tema Değiştirme (Light/Dark) (Değişiklik yok)
    @app.callback(
        Output('theme-store', 'data'),
        Output('dark-mode-button', 'children'),
        Input('dark-mode-button', 'n_clicks'),
        State('theme-store', 'data'),
        prevent_initial_call=True
    )
    def toggle_dark_mode(n_clicks, current_theme):
        # n_clicks None ise (başlangıç) veya çift ise light moda geç/kal
        if n_clicks is None or n_clicks % 2 == 0:
            new_theme = 'light'
            button_icon = '🌙'  # Dark moda geçiş butonu
        else:  # Tek ise dark moda geç
            new_theme = 'dark'
            button_icon = '☀️'  # Light moda geçiş butonu
        return new_theme, button_icon

    # --- Stil Güncelleme Callback'i ---
    # Bu callback artık tüm dinamik stilleri yönetecek
    @app.callback(
        Output('app-container', 'style'),  # 1
        Output('chat-log', 'style'),  # 2
        Output('offcanvas-menu', 'style'),  # 3
        Output('new-chat-button', 'style'),  # 4
        Output('offcanvas-menu-bottom', 'style'),  # 5
        Output('content-area', 'style'),  # 6
        Output('user-input', 'style'),  # 7
        Output('top-bar', 'style'),  # 8
        Output('input-area', 'style'),  # 9
        Output('toggle-offcanvas-button', 'style'),  # 10
        Output('dark-mode-button', 'style'),  # 11
        Output('send-button', 'style'),  # 12
        Output('attach-file-button', 'style'),  # 13
        Output('menu-hr', 'style'),  # 14 (Hr için eklendi)
        Output('logout-link', 'style'),  # 15 (Logout link stili eklendi)
        # --- OUTPUTS SONU ---
        Input('theme-store', 'data'),  # Input 1
        Input('offcanvas-open', 'data')  # Input 2
    )
    def update_styles(theme, is_offcanvas_open):
        # Tema renklerini tanımla
        if theme == 'dark':
            app_bg = '#212529'
            app_color = '#f8f9fa'  # Genel metin rengi
            chat_bg = '#343a40'
            chat_border = '#495057'
            input_bg = '#495057'
            input_color = '#f8f9fa'  # Input metin rengi
            border_color = '#495057'
            menu_bg = '#343a40'
            menu_color = '#f8f9fa'  # Menü ana metin rengi
            menu_border = '#495057'
            hr_color = '#495057'
            top_bar_bg = '#343a40'
            top_bar_border = '#495057'
            input_area_bg = '#343a40'
            input_area_border = '#495057'
            menu_button_bg = '#2d3135'  # Koyu Gri/Mavi tonu
            menu_button_color = '#c2e7ff'  # Açık Mavi yazı (Kullanılmıyor ama durabilir)
            menu_button_border = 'none'
            send_button_bg = '#0d6efd'
            send_button_color = 'white'
            icon_button_color = '#adb5bd'  # İkon rengi
            link_color = '#64b5f6'  # Alt linkler için açık mavi

        else:  # light mode
            app_bg = '#ffffff'
            app_color = '#212529'  # Genel metin rengi
            chat_bg = '#ffffff'
            chat_border = '#dee2e6'
            input_bg = '#ffffff'
            input_color = '#212529'  # Input metin rengi
            border_color = '#dee2e6'
            menu_bg = '#f8f9fa'
            menu_color = '#212529'  # Menü ana metin rengi
            menu_border = '#dee2e6'
            hr_color = '#dee2e6'
            top_bar_bg = '#f8f9fa'
            top_bar_border = '#dee2e6'
            input_area_bg = '#f8f9fa'
            input_area_border = '#dee2e6'
            menu_button_bg = '#c2e7ff'  # Açık Mavi arka plan (Kullanılmıyor ama durabilir)
            menu_button_color = '#072d4b'  # Koyu Mavi yazı (Kullanılmıyor ama durabilir)
            menu_button_border = 'none'
            send_button_bg = '#007bff'
            send_button_color = 'white'
            icon_button_color = '#6c757d'  # İkon rengi
            link_color = '#007bff'  # Alt linkler için standart mavi

        offcanvas_left = '0px' if is_offcanvas_open else '-250px'
        content_margin_left = '250px' if is_offcanvas_open else '0px'

        # --- Stil Sözlükleri ---
        app_container_style = {'display': 'flex', 'height': '100vh', 'fontFamily': 'Segoe UI, sans-serif',
                               'backgroundColor': app_bg, 'color': app_color,
                               'overflow': 'hidden'}  # app_color tüm alt elementler için genel renk sağlar
        # chat_log stilinde color kaldırıldı, genel app_color'dan miras alacak
        chat_log_style = {'flexGrow': 1, 'overflowY': 'auto', 'padding': '15px', 'backgroundColor': chat_bg,
                          'borderTop': f'1px solid {chat_border}', 'borderBottom': f'1px solid {chat_border}'}
        content_area_style = {'flexGrow': 1, 'display': 'flex', 'flexDirection': 'column', 'height': '100vh',
                              'marginLeft': content_margin_left, 'transition': 'margin-left 0.3s ease-in-out',
                              'backgroundColor': app_bg}
        user_input_style = {'flexGrow': 1, 'marginRight': '10px', 'padding': '10px 15px', 'borderRadius': '20px',
                            'border': f'1px solid {border_color}', 'backgroundColor': input_bg, 'color': input_color}
        top_bar_style = {'padding': '10px 15px', 'backgroundColor': top_bar_bg,
                         'borderBottom': f'1px solid {top_bar_border}', 'display': 'flex', 'alignItems': 'center',
                         'justifyContent': 'space-between', 'color': app_color}  # Top barın kendi metin rengi
        input_area_style = {'padding': '15px', 'display': 'flex', 'alignItems': 'center',
                            'borderTop': f'1px solid {input_area_border}', 'backgroundColor': input_area_bg}
        # Menü Stilleri
        # offcanvas_menu style'ında color kaldırıldı, genel app_color'dan miras alacak (veya menu_color kullanılabilir)
        offcanvas_menu_style = {'width': '250px', 'backgroundColor': menu_bg, 'borderRight': f'1px solid {menu_border}',
                                'padding': '20px', 'position': 'fixed', 'top': 0, 'left': offcanvas_left, 'bottom': 0,
                                'zIndex': 1050, 'transition': 'left 0.3s ease-in-out', 'overflowY': 'auto',
                                'color': menu_color, 'display': 'flex',
                                'flexDirection': 'column'}  # Menu ana metin rengi kullanıldı
        hr_style = {'borderColor': hr_color, 'margin': '15px 0'}  # Hr stili
        new_chat_button_style = {  # New Chat butonunun rengi, menü metin rengini kullanacak
            'backgroundColor': 'transparent',
            'border': 'none',
            'color': menu_color,
            'boxShadow': 'none'
        }
        offcanvas_menu_bottom_style = {
            'position': 'absolute', 'bottom': '0', 'left': '0', 'width': '100%',
            'padding': '10px 20px', 'backgroundColor': menu_bg,
            'color': link_color,  # Alt linklerin rengi buradan miras alınacak
            'borderTop': f'1px solid {menu_border}'
        }
        # İkon Buton Stilleri
        base_icon_button_style = {  # Ortak stil
            'background': 'none', 'border': 'none', 'cursor': 'pointer',
            'padding': '5px', 'fontSize': '1.5em',
            'lineHeight': '1', 'textDecoration': 'none',  # Logout linki için textDecoration eklendi
            'color': icon_button_color  # İkon rengini temadan al
        }
        toggle_offcanvas_button_style = {**base_icon_button_style, 'marginRight': '10px', 'fontSize': '1.5em'}
        dark_mode_button_style = {**base_icon_button_style, 'fontSize': '1.2em'}
        attach_file_button_style = {**base_icon_button_style, 'fontSize': '1.2em', 'marginLeft': '5px'}
        # Logout Link Stili - base_icon_button_style'ı kullanıyor
        logout_link_style = {**base_icon_button_style, 'marginLeft': '15px',
                             'fontSize': '1.2em'}  # Margin ve boyutu ayarla

        # Gönder Buton Stili
        send_button_style = {
            'padding': '8px 12px', 'borderRadius': '20px', 'border': 'none',
            'cursor': 'pointer', 'marginLeft': '10px', 'fontSize': '1em',
            'lineHeight': '1', 'backgroundColor': send_button_bg, 'color': send_button_color
        }

        # Return sırası Output sırasıyla aynı olmalı
        return (
            app_container_style,  # 1
            chat_log_style,  # 2
            offcanvas_menu_style,  # 3
            new_chat_button_style,  # 4
            offcanvas_menu_bottom_style,  # 5
            content_area_style,  # 6
            user_input_style,  # 7
            top_bar_style,  # 8
            input_area_style,  # 9
            toggle_offcanvas_button_style,  # 10
            dark_mode_button_style,  # 11
            send_button_style,  # 12
            attach_file_button_style,  # 13
            hr_style,  # 14
            logout_link_style  # 15
        )

    # --- Chat Mesajlarını Gösterme Callback'i ---
    # Bu callback Markdown içeriğinin renginin bubble'dan miras alındığından emin oluyor.
    # CSS dosyasındaki .chat-markdown pre { ... } stilleri responsiveness için kritik.
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

    # --- Kullanıcı Girdisini İşleme ve Yanıt Alma Callback'i ---
    # LangChain Deprecation uyarılarını gidermek için güncellendi
    @app.callback(
        Output('chat-history', 'data'),
        Output('user-input', 'value'),
        Input('user-input', 'n_submit'),
        Input('send-button', 'n_clicks'),
        State('user-input', 'value'),
        State('chat-history', 'data'),  # Geçmiş verisini alıyoruz
        prevent_initial_call=True
    )
    def process_user_input(n_submit, n_clicks, user_input, history_data):
        # Sadece submit veya button click tetiklediyse devam et
        if not user_input or user_input.strip() == "":
            raise PreventUpdate

        print(f"DEBUG: Kullanıcı girdisi alındı: {user_input}")

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
            print("DEBUG: LangChain runnable zinciri başarıyla oluşturuldu.")

        except Exception as e:
            print(f"Hata: LangChain zinciri veya history setup oluşturulamadı - {e}")
            error_message = f"Bot başlatılırken bir hata oluştu: {e}";
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

    # Clientside callback for auto-scrolling chat log
    # client_side_callbacks'ı uygulamanızın ana yerinde (urls.py veya settings.py yanında)
    # veya Dash uygulamasının başlatıldığı yerde tanımlamanız gerekebilir.
    # Örneğin: clientside_callback(ClientsideFunction(namespace='clientside', function_name='scrollToBottom'), ...)
    # Bu kısım Dash'in başlatıldığı yere ve js dosyanızın nasıl yüklendiğine bağlıdır.
    # Şu anki yapıda doğrudan view içinde tanımlamak uygun olmayabilir, bu sadece bir hatırlatma.

    # Django template'ini render et (Bu template içinde {% plotly_app name='ChatLLM' %} olmalı)
    return render(request, 'llm.html')

