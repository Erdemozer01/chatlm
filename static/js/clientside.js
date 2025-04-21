// static/js/clientside.js

// Dash Clientside Callback'lerinin kullanacağı ana namespace objesi.
// window.dash_clientside objesi genellikle Dash tarafından sağlanır.
// Object.assign kullanarak, bu objeye veya içindeki namespace'lere yeni fonksiyonları
// mevcut olanları bozmadan ekleyebiliriz.

window.dash_clientside = Object.assign({}, window.dash_clientside, {

    // 'clientside' adında bir namespace tanımlıyoruz veya genişletiyoruz.
    // llm/views.py dosyasındaki ClientsideFunction'da belirtilen namespace ile aynı olmalı.
    clientside: {

        // --- Menü Açma/Kapama Callback Fonksiyonu ---
        // llm/views.py'deki Clientside Callback tarafından çağrılır.
        // Output: offcanvas-menu class name, offcanvas-open store data
        // Input: toggle-offcanvas-button n_clicks
        // State: offcanvas-menu className, offcanvas-open store data
        /**
         * Menü açma/kapama sınıfını ve server tarafındaki offcanvas-open store'unu günceller.
         * @param {number} n_clicks - Butonun tıklanma sayısı.
         * @param {string} current_classes - Menü elementinin mevcut sınıfları.
         * @param {boolean} current_state - Offcanvas-open store'unun mevcut değeri.
         * @returns {Array<string|boolean>} [Yeni sınıf listesi stringi, Yeni offcanvas-open store değeri]
         */
        toggle_offcanvas_class: function (n_clicks, current_classes, current_state) {
            // prevent_initial_call=True olduğu için n_clicks ilk yüklemede None olur ve burası çalışmaz.
            // Sonraki tıklamalarda n_clicks 0'dan büyük olur.
            if (n_clicks === 0 || n_clicks === null) {
                throw window.Dash.PreventUpdate; // Dash callback'i atla
            }

            // current_classes Offcanvas menü elementinin mevcut class name stringi (layoutta verilmişse veya başka callback tarafından set edildiyse)
            // Veya callback input/state olarak elementin className'ini alıyorsa o değer gelir.
            // Layout'ta offcanvas-menu'nün className'i yok, store değeri (current_state) ile durumu takip ediyoruz.
            // current_state offcanvas-open store'undan geliyor.

            let is_open = current_state; // Durumu store'dan al
            let new_state = !is_open; // Durumu ters çevir

            // Class name'i store'a göre güncelleyebiliriz veya sadece store'u güncelleyebiliriz.
            // Görsel stil CSS'te offcanvas-open store'u üzerinden yönetiliyorsa (update_styles callback gibi), sadece store'u güncellemek yeterli.
            // Ancak burada örnekte Hem class name hem store dönülüyor, bu eğer bir elementin class name'i de output ise kullanılır.
            // Layout'ta offcanvas-menu'nün className'i yoktu, update_styles margin-left ile yönetiyordu.
            // Bu fonksiyon aslında SADECE offcanvas-open store'unu güncellemek için yeterli olabilir.
            // Ama örnek kod yapısını koruyarak, Output('offcanvas-menu', 'className') olsaydı ne döneceğini hesaplayalım:

            // Eğer layout'ta className olsaydı:
            // let classesList = current_classes ? current_classes.split(' ') : [];
            // let new_classesList = classesList.filter(cls => cls !== 'menu-open');
            // if (new_state) { new_classesList.push('menu-open'); }
            // let new_classes = new_classesList.join(' ');

            // Sadece offcanvas-open store'unu güncelleyen daha basit callback için (eğer layout class name kullanmıyorsa):
            // Output('offcanvas-open', 'data')
            // Input('toggle-offcanvas-button', 'n_clicks')
            // State('offcanvas-open', 'data')
            // return !current_state; // Sadece yeni store değeri

            // Görünen o ki llm/views.py'deki callback offcanvas-open store'unu Output olarak alıyor.
            // Dolayısıyla sadece store'un yeni değerini dönmek yeterli.

            // NOT: llm/views.py'deki toggle_offcanvas callback'i sadece store'u güncelliyor ve Output('offcanvas-open', 'data') dönüyor.
            // Bu JS fonksiyonu llm/views.py'deki toggle_offcanvas callback'ini EZMİYOR, farklı bir callback bu.
            // Bu JS fonksiyonu, eğer llm/views.py'de buna karşılık gelen bir Clientside Callback tanımı varsa çalışır.
            // (Output('offcanvas-menu', 'className'), Output('offcanvas-open', 'data')).
            // llm/views.py'deki kodda böyle bir Clientside Callback tanımı YOKTU.
            // Bu JS fonksiyonu şu anki llm/views.py koduyla tetiklenmez.

            // Kullanıcının son llm/views.py kodunda tanımlı olan toggle_offcanvas callback'i Python tarafındaydı.
            // Bu JS fonksiyonu muhtemelen eski bir denemeden kalmış veya bir örnekten alınmış.

            // Bu durumda, bu JS fonksiyonu şu anki llm/views.py koduyla aktif olarak kullanılmıyor.
            // Ancak istenirse, menü açma/kapama animasyonunu clientside yapmak için kullanılabilir.
            // Şimdilik, bu fonksiyonu kodu doğru şekilde içerecek ama mevcut durumda tetiklenmeyecek şekilde bırakalım.

            // Eğer bu JS fonksiyonu Clientside callback ile tetiklenirse,
            // ve outputları Output('offcanvas-menu', 'className'), Output('offcanvas-open', 'data') ise,
            // dönüş değeri [yeni_class_name_stringi, yeni_store_değeri] olmalıdır.
            let classesList = current_classes ? current_classes.split(' ') : [];
            let new_classesList = classesList.filter(cls => cls !== 'menu-open');
            if (new_state) {
                new_classesList.push('menu-open');
            }
            let new_classes = new_classesList.join(' ');
            return [new_classes, new_state];
        },

        // --- LOGOUT FORMU SUBMIT ETME FONKSİYONU ---
        // llm/views.py'deki Clientside Callback tarafından çağrılacak.
        // Bu fonksiyon, llm.html'deki gizli logout formunu POST metoduyla submit eder.
        // İmza: (n_clicks) - Logout butonunun n_clicks Input'u gelir.
        submitLogoutForm: function (n_clicks) {
            // Callback, prevent_initial_call=True ve Input n_clicks olduğu için
            // sadece butona tıklanınca (n_clicks > 0 olduğunda) çalışır.
            if (n_clicks > 0) {
                // llm.html'deki gizli formu ID'si ile bul.
                var form = document.getElementById('logout-form');
                // Konsola formun bulunup bulunmadığını yazdır (hata ayıklama için faydalı)
                console.log("Logout form araniyor:", form);

                // Eğer form bulunduysa
                if (form) {
                    form.submit(); // Formu submit et - bu POST isteği gönderir.
                    console.log("Logout formu submit edildi.");
                    // Form submit edildikten sonra tarayıcı sayfayı yeniden yükleyecektir (Django'nun yönlendirmesiyle).
                } else {
                    // Form bulunamazsa konsola hata yaz.
                    console.error("Hata: 'logout-form' ID'li HTML formu bulunamadı!");
                }
            }
            // Dash callback yapısı gereği bir değer dönmelidir (Output'u güncellemek için).
            // Logout butonu n_clicks sayacını sıfırlıyoruz.
            // Output('logout-button-trigger', 'n_clicks') olduğu için burası 0 dönecek.
            return 0;
        },

        // --- TEXTAREA ENTER KEY HANDLER ---
        // llm/views.py'deki Clientside Callback tarafından sayfa yüklendiğinde çağrılacak.
        // Textarea alanında Enter tuşuna basıldığında (Shift+Enter hariç) gönder butonuna tıklama eventini simüle eder.
        // İmza: (chatHistoryData, textarea_id_string) - Callback'in Input/State sırasına uygun.
        // Output: user-input id (Dummy Output)
        // Input: chat-history data (Trigger)
        // State: user-input id
        addTextareaEnterKeyListener: function (chatHistoryData, textarea_id) {
            // Konsola hata ayıklama mesajları
            console.log("addTextareaEnterKeyListener called for ID:", textarea_id); // textarea_id stringi buraya gelecek

            // Textarea elementini ID'si ile bul
            var textarea = document.getElementById(textarea_id);
            console.log("Textarea element found:", textarea); // <-- Textarea elementinin bulunup bulunmadığını logla

            // Eğer textarea elementi bulunduysa
            if (textarea) { // <-- Doğru 'if (textarea)' bloğu başlangıcı

                console.log("Adding keydown listener to textarea:", textarea); // Listener eklemeden önce logla

                // Keydown event listener'ı ekle
                textarea.addEventListener('keydown', function (event) {
                    // Basılan tuş Enter (keyCode 13) olup olmadığını ve Shift tuşuna basılmadığını kontrol et
                    if (event.keyCode === 13 && !event.shiftKey) {
                        event.preventDefault(); // Enter tuşunun varsayılan davranışını (yeni satır) engelle

                        console.log("Enter key pressed without Shift. Attempting to simulate click on send button."); // <-- JS'nin buraya ulaştığını gösterir

                        // Gönder butonunu ID'si ile bul
                        var sendButton = document.getElementById('send-button');
                        console.log("Send button found:", sendButton); // <-- Gönder butonunun bulunup bulunmadığını logla


                        // Eğer buton bulunduysa, tıklama eventini tetikle
                        if (sendButton) {
                            sendButton.click(); // Butona tıklama eventini simüle et
                            console.log("Send button click simulated."); // Simülasyonun başarılı olduğunu logla
                        } else {
                            console.error("Hata: 'send-button' ID'li gönderme butonu bulunamadi!"); // <-- Buton bulunamazsa hata
                        }
                    }
                    // Eğer Shift + Enter basılırsa, varsayılan davranışa (yeni satır ekleme) izin verilir.
                });

                // --- Listener başarıyla eklendikten sonra logla ---
                console.log("Textarea Enter key listener successfully added for ID:", textarea_id); // <-- Bu satır 'if (textarea)' bloğunun sonunda, addEventListener sonrası olmalı
            } else { // <-- 'if (textarea)' koşulu yanlışsa (element bulunamazsa)
                console.error("Hata: '" + textarea_id + "' ID'li textarea elementi bulunamadi! Listener eklenemedi."); // <-- Textarea bulunamazsa hata ve listener eklenemediği bilgisi
            } // <-- 'if/else (textarea)' bloğu sonu

            // Callback'in Output'u (Dummy), null döndürebiliriz.
            return null;
        } // <-- addTextareaEnterKeyListener fonksiyonu sonu

        // --- DİĞER CLIENTSIDE FONKSİYONLARI BURAYA EKLENEBİLİR ---


    } // <-- 'clientside' namespace'i sonu
}); // <-- window.dash_clientside objesi tanımı sonu

// static/js/clientside.js dosyasına eklenecek kod
if (!window.dashExtensions) {
    window.dashExtensions = {};
}

window.dashExtensions.clientside = {

    // Mevcut submitLogoutForm fonksiyonu
    submitLogoutForm: function(n_clicks) {
        if (n_clicks > 0) {
            // Logout formu gönder
            document.getElementById('logout-form').submit();
        }
        return n_clicks;
    },

    // Ekran boyutu değiştiğinde offcanvas menüyü otomatik kapat
    handleResize: function(n, is_open) {
        // İlk yükleme kontrolü - sadece ekran boyutu değiştiğinde çalışsın
        if (n === 0) return is_open;

        // Küçük ekranlarda (mobil) offcanvas menüyü otomatik kapat
        if (window.innerWidth <= 768 && is_open) {
            return false;
        }

        return is_open;
    },

    // Mesaj alanında Enter tuşu davranışı (Shift+Enter için yeni satır, sadece Enter için gönder)
    handleEnterKey: function(n_submit, n_clicks, value) {
        document.getElementById('user-input').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                document.getElementById('send-button').click();
            }
        });

        return window.dash_clientside.no_update;
    },

    // Sohbet günlüğünü otomatik kaydır
    scrollChatToBottom: function(chat_history) {
        const chatLog = document.getElementById('chat-log');
        if (chatLog) {
            setTimeout(() => {
                chatLog.scrollTop = chatLog.scrollHeight;
            }, 100);
        }
        return window.dash_clientside.no_update;
    }
};

// Ekran boyutu değişimini dinle
window.addEventListener('resize', function() {
    // Küçük ekranlarda offcanvas menüyü otomatik kapat
    if (window.innerWidth <= 768) {
        // Dash uygulamasının store verilerini doğrudan değiştiremeyiz,
        // Bu nedenle bir event dispatch ederek callback'i tetikliyoruz
        const resizeEvent = new CustomEvent('windowResize', {
            detail: { width: window.innerWidth, height: window.innerHeight }
        });
        document.dispatchEvent(resizeEvent);
    }
});

// Sayfa yüklendiğinde çalışacak kod
window.addEventListener('DOMContentLoaded', function() {
    // Mobil cihazlarda dokunmatik kaydırma iyileştirmeleri
    const chatLog = document.getElementById('chat-log');
    if (chatLog) {
        chatLog.style.WebkitOverflowScrolling = 'touch';
    }

    // İnput alanı için otomatik yükseklik ayarı
    const userInput = document.getElementById('user-input');
    if (userInput) {
        userInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    }
});