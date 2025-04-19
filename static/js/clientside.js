// static/js/clientside.js

window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        /**
         * Menü açma/kapama sınıfını ve server tarafındaki offcanvas-open store'unu günceller.
         * @param {number} n_clicks - Butonun tıklanma sayısı.
         * @param {string} current_classes - Menü elementinin mevcut sınıfları.
         * @returns {Array<string|boolean>} [Yeni sınıf listesi, Yeni offcanvas-open store değeri]
         */
        toggle_offcanvas_class: function(n_clicks, current_classes) {
            // İlk yüklemede (n_clicks=0) veya null olduğunda hiçbir şey yapma
            if (n_clicks === 0 || n_clicks === null) {
                // Dash.no_update tarayıcıda tanımsız olabilir, yerine throw exception kullan
                throw window.Dash.PreventUpdate; // Doğru kullanımı bu
            }

            let classesList = current_classes ? current_classes.split(' ') : [];
            let is_open = classesList.includes('menu-open');
            let new_state = !is_open; // Durumu ters çevir (açıksa kapat, kapalıysa aç)

            let new_classesList = classesList.filter(cls => cls !== 'menu-open'); // menu-open sınıfını kaldır
            if (new_state) {
                new_classesList.push('menu-open'); // Yeni durum açıksa sınıfı ekle
            }

            let new_classes = new_classesList.join(' '); // Yeni sınıf listesini string yap

            // Server tarafındaki offcanvas-open-server-state store'unu da güncellemek için yeni durumu döndür
            // Bu, server tarafındaki stil callback'inin (margin-left için) doğru durumu bilmesini sağlar.
            return [new_classes, new_state];
        }
    }
});

// static/js/clientside.js

window.clientside = { // Callback'te belirtilen namespace
    submitLogoutForm: function(n_clicks) { // Callback'te belirtilen fonksiyon adı ve inputlar
        // n_clicks değeri burada kullanılıyor ama fonksiyona tıklama dışı bir input gelmez
        if (n_clicks > 0) {
            var form = document.getElementById('logout-form'); // llm.html'deki gizli formun ID'si
            if (form) {
                form.submit(); // Formu submit et, bu POST isteği gönderir ve Django logout'u tetikler
                console.log("Logout formu submit edildi.");
            } else {
                console.error("Logout formu bulunamadı!");
            }
        }
        return 0; // Dash callback'e geri dönen değer (logout-button'ın n_clicks'ini sıfırlar)
    }
    // ... Diğer clientside fonksiyonlarınız (örn. scroll to bottom) buraya eklenebilir
};