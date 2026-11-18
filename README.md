# TypeTug

**TypeTug** adalah game _multiplayer_ berbasis web dengan mekanik tarik tambang (_tug of war_) yang digerakkan oleh kecepatan dan ketepatan mengetik secara _real-time_.

Proyek ini dikembangkan untuk Tugas Besar mata kuliah **Pemrograman Jaringan**, dengan fokus utama pada arsitektur _client-server_ yang skalabel, latensi rendah, manajemen konkurensi (_concurrency_), serta struktur kode yang modular agar mudah dipelihara dan diaudit.

---

## Fitur Utama

- **Flexible Team Matchmaking (`1v1` – `5v5`):** Pemain dapat memilih mode pertandingan mulai dari duel `1v1` hingga tim `5v5` dengan sistem pengacakan tim (_random matchup_) otomatis.
- **Real-Time Typing Physics:** Kecepatan dan akurasi mengetik setiap pemain dikonversi secara _real-time_ menjadi gaya tarik (_pull force_) yang menggerakkan posisi tali dan animasi karakter.
- **Match Timer & Win Condition:** Batas waktu pertandingan (_countdown timer_) untuk mencegah _stalemate_, di mana pemenang ditentukan berdasarkan garis batas akhir atau posisi tali dominan saat waktu habis.
- **High Concurrency & Low Latency:** Dirancang untuk menangani banyak koneksi klien secara simultan (_concurrent connections_) dengan sinkronisasi _state_ yang ringan dan efisien.

---

## Arsitektur Sistem

Aplikasi ini menerapkan pola desain berikut untuk menjamin performa saat _load testing_ dan keterbacaan kode saat evaluasi teknis:

- **Authoritative Server:** Seluruh validasi kata, kalkulasi gaya tarik, posisi tali, dan timer diproses di _server_ untuk mencegah manipulasi data dari sisi klien (_anti-cheat_).
- **Event-Driven & Full-Duplex Communication:** Menggunakan WebSocket untuk pertukaran _state_ dua arah berlatensi rendah tanpa _overhead_ HTTP _polling_.
- **Separation of Concerns:** Pemisahan tegas antara _network layer_ (manajemen _socket_ dan _room_), _game engine_ (logika fisika tali dan _matchmaking_), serta _presentation layer_ (UI dan animasi).

---

## Tech Stack
