// static/js/clientside.js

// Dash Clientside Callback'lerinin kullanacağı namespace.
// window.dash_clientside.clientside namespace'ini tanımlıyoruz.
// Object.assign, mevcut window.dash_clientside objesini bozmadan yeni fonksiyonları eklemek için kullanılır.
window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: { // <-- clientside namespace'i

        /**
         * Menü açma/kapama sınıfını ve server tarafındaki offcanvas-open store'unu günceller.
         * @param {number} n_clicks - Butonun tıklanma sayısı.
         * @param {string} current_classes - Menü elementinin mevcut sınıfları.
         * @returns {Array<string|boolean>} [Yeni sınıf listesi, Yeni offcanvas-open store değeri]
         */
        toggle_offcanvas_class: function (n_clicks, current_classes) {
            // İlk yüklemede (n_clicks=0) veya null olduğunda hiçbir şey yapma
            if (n_clicks === 0 || n_clicks === null) {
                throw window.Dash.PreventUpdate; // Doğru kullanımı bu
            }

            let classesList = current_classes ? current_classes.split(' ') : [];
            let is_open = classesList.includes('menu-open');
            let new_state = !is_open; // Durumu ters çevir

            let new_classesList = classesList.filter(cls => cls !== 'menu-open'); // menu-open sınıfını kaldır
            if (new_state) {
                new_classesList.push('menu-open'); // Yeni durum açıksa sınıfı ekle
            }

            let new_classes = new_classesList.join(' '); // Yeni sınıf listesini string yap

            // Server tarafındaki offcanvas-open-server-state store'unu güncellemek için yeni durumu döndür
            return [new_classes, new_state];
        },

        // --- LOGOUT FORMU SUBMIT ETME FONKSİYONU ---
        // llm/views.py'deki Clientside Callback tarafından çağrılacak.
        submitLogoutForm: function(n_clicks) { // <-- submitLogoutForm fonksiyonu, clientside namespace'i içinde
            // Sadece butona gerçekten tıklandığında (n_clicks 0'dan büyük olunca) çalıştır.
            if (n_clicks > 0) {
                // llm.html'deki gizli formu ID'si ile bul.
                var form = document.getElementById('logout-form');
                // Console'a formun bulunup bulunmadığını yazdır (hata ayıklama için faydalı)
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
            return 0;
        }
        // --- DİĞER CLIENTSIDE FONKSİYONLARI BURAYA EKLENİR ---

    } // <-- clientside namespace'i sonu
}); // <-- window.dash_clientside objesi tanımı sonu