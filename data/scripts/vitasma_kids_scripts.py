"""Save 5 Vitasma Kids scripts to database."""
from src.scripts.manager import ScriptManager

sm = ScriptManager()

# ═══════════════════════════════════════════════════
# SCRIPT 1: Problem-Solution (Panik Ibu)
# ═══════════════════════════════════════════════════
sm.create_script(
    title="Vitasma Kids - Anak Batuk Tengah Malam",
    hook="Jam 2 pagi anak gue batuk sampe muntah...",
    content="""[ACTION: Layar gelap, suara batuk anak di background, teks "Jam 2 Pagi..."]

Jam 2 pagi anak gue batuk sampe muntah. Gue panik, udah coba segala cara — madu biasa, uap, balsem, NOTHING WORKS.

[ACTION: Close-up muka capek + khawatir, lighting redup]

Sampe akhirnya tetangga gue yang anaknya juga punya masalah yang sama, rekomendasiin ini.

[ACTION: Reveal produk Vitasma Kids, zoom in pelan-pelan dengan lighting terang]

Vitasma Kids. Madu herbal yang emang KHUSUS buat masalah pernapasan anak. Batuk, pilek, sesak napas, sampe asma — ini bisa bantu.

[ACTION: Kasih liat anak minum, anak happy/senyum]

Yang bikin gue tenang? 3.500 lebih orang udah repurchase. Bukan beli sekali doang — BELI LAGI.

[ACTION: Tunjukin screenshot 3.5K+ repurchased]

Dan sekarang lagi flash sale cuma 95 ribu dari 120 ribu.

[ACTION: Tunjukin harga + sticker "DISKON 21%"]

Moms, kalo anak lo sering batuk-batuk, cobain deh sebelum flash sale-nya abis. Link di keranjang kuning ya!

[ACTION: Point ke keranjang kuning, close with anak yang lagi main happy]""",
    cta="Link di keranjang kuning ya, Moms! Sebelum flash sale-nya abis!",
    niche="kesehatan anak",
    script_type="affiliate",
    product_id=1,
    tags="batukanak,maduherbal,vitasmakids,ibuanak,fyp",
    notes="Style: Problem-Solution. Target emosi ibu yg panik tengah malam. High emotional hook.",
)

# ═══════════════════════════════════════════════════
# SCRIPT 2: Storytelling (Perjalanan Anak Sembuh)
# ═══════════════════════════════════════════════════
sm.create_script(
    title="Vitasma Kids - 1 Minggu Perubahan",
    hook="Anak gue 3 tahun, batuknya udah SEBULAN ga sembuh-sembuh.",
    content="""[ACTION: Video anak yang lagi batuk / tampak lesu, teks overlay "Sudah 1 Bulan..."]

Anak gue 3 tahun, batuknya udah SEBULAN ga sembuh-sembuh. Udah ke dokter, udah dikasih obat, tetep balik lagi.

[ACTION: Montage botol obat-obat sebelumnya, wajah frustasi]

Gue sampe stress. Tiap malam ga bisa tidur dengerin dia batuk terus.

[ACTION: Transisi — tangan ambil botol Vitasma Kids]

Sampe akhirnya gue nemu Vitasma Kids. Jujur awalnya skeptis — "ah paling sama aja."

[ACTION: Kasih ke anak, anak minum]

Tapi hari ke-3... batuknya mulai berkurang.

[ACTION: Teks "Hari ke-3" + anak mulai aktif main]

Hari ke-7... GONE. Anak gue bisa tidur nyenyak lagi.

[ACTION: Teks "Hari ke-7" + anak tidur pulas]

Ternyata emang beda ya madu herbal yang khusus pernapasan sama madu biasa. Ini tuh bisa bantu buat batuk, pilek, sesak, sampe asma dan bronkitis.

[ACTION: Close-up produk + list manfaat muncul satu-satu]

Lagi diskon 95 ribu doang. Cek keranjang kuning sebelum harganya balik!

[ACTION: Point ke bawah, anak main happy di background]""",
    cta="Cek keranjang kuning sebelum harganya balik normal!",
    niche="kesehatan anak",
    script_type="affiliate",
    product_id=1,
    tags="batukanak,storyanak,maduherbal,vitasmakids,fyp",
    notes="Style: Storytelling timeline. Day 1 → Day 7 transformation. Builds credibility.",
)

# ═══════════════════════════════════════════════════
# SCRIPT 3: Edukasi (Kenapa Batuk Anak Ga Sembuh)
# ═══════════════════════════════════════════════════
sm.create_script(
    title="Vitasma Kids - Alasan Batuk Anak Ga Sembuh",
    hook="Anak lo batuk ga sembuh-sembuh? Ini alasannya.",
    content="""[ACTION: Face to camera, expression serius, teks "PENTING untuk orang tua!"]

Anak lo batuk ga sembuh-sembuh? Ini alasannya.

[ACTION: Finger count / teks muncul satu-satu]

Pertama — lo cuma ngatasi GEJALA, bukan AKAR masalahnya. Obat batuk biasa cuma suppress batuk, tapi ga bersihin saluran pernapasannya.

[ACTION: Ilustrasi simple / teks animasi "Gejala vs Akar Masalah"]

Kedua — sistem imun anak lo belum kuat. Jadi kena polusi dikit, cuaca berubah dikit, langsung kambuh.

[ACTION: Teks "Imun Lemah = Gampang Kambuh"]

Nah makanya lo butuh yang DOUBLE action. Bersihin saluran pernapasan DAN boost daya tahan tubuh anak.

[ACTION: Reveal Vitasma Kids, hold produk]

Vitasma Kids ini madu herbal yang emang didesain khusus buat itu. Bukan cuma redain batuk, tapi juga bantu masalah pernapasan dan paru secara keseluruhan.

[ACTION: List manfaat muncul: Batuk, Pilek, Sesak, Asma, ISPA, Bronkitis, Daya Tahan Tubuh]

3.500 lebih orang udah repurchase — artinya WORKS.

Flash sale sekarang cuma 95 ribu. Link di keranjang kuning!

[ACTION: Close-up produk, point ke bawah]""",
    cta="Flash sale cuma 95 ribu! Cek keranjang kuning sekarang.",
    niche="kesehatan anak",
    script_type="affiliate",
    product_id=1,
    tags="edukasianak,batukanak,tipsibu,vitasmakids,kesehatananak,fyp",
    notes="Style: Edukasi. Position as 'knowledgeable parent'. Hook rasa penasaran, deliver value, soft sell.",
)

# ═══════════════════════════════════════════════════
# SCRIPT 4: Social Proof / Review Jujur
# ═══════════════════════════════════════════════════
sm.create_script(
    title="Vitasma Kids - Review Jujur Setelah 2 Minggu",
    hook="Gue disuruh review ini, tapi gue mau JUJUR.",
    content="""[ACTION: Hold produk, ekspresi serius ke camera]

Gue disuruh review ini, tapi gue mau JUJUR.

[ACTION: Taruh produk di meja, sit down vibe]

Jadi ini Vitasma Kids — madu herbal buat anak yang katanya bisa bantu masalah batuk dan pernapasan. Harga 95 ribu lagi flash sale.

[ACTION: Close-up produk, tunjukin label]

Pertama, baunya. Ini bau madu beneran, anak gue ga nolak minumnya. Itu PENTING karena kalo anak ga mau minum, percuma.

[ACTION: Anak minum, ekspresi suka]

Kedua, hasilnya. Anak gue emang lagi batuk-pilek, gue kasih ini rutin. Hari ke-4-5 udah keliatan bedanya. Batuknya berkurang drastis.

[ACTION: Teks "Hari ke-4: Batuk berkurang"]

Ketiga, yang bikin gue percaya — 3.500 lebih orang REPURCHASE. Bukan cuma beli sekali terus nyesel. Mereka beli LAGI.

[ACTION: Screenshot repurchased, zoom in]

Minusnya? Menurut gue cuma satu — stoknya sering abis karena emang laris.

[ACTION: Balik ke camera, senyum]

So, worth it ga? WORTH IT. Apalagi lagi diskon. Cek sendiri di keranjang kuning.

[ACTION: Hold produk, point ke bawah]""",
    cta="Worth it! Cek sendiri di keranjang kuning.",
    niche="kesehatan anak",
    script_type="affiliate",
    product_id=1,
    tags="reviewjujur,vitasmakids,maduanak,batukanak,honest,fyp",
    notes="Style: Honest Review. Credibility play — 'gue mau jujur' hook builds trust. Include minor 'minus' for authenticity.",
)

# ═══════════════════════════════════════════════════
# SCRIPT 5: Trending / POV / Relatable Mom
# ═══════════════════════════════════════════════════
sm.create_script(
    title="Vitasma Kids - POV Ibu Pas Anak Batuk",
    hook="POV: Anak lo batuk di tengah malam dan lo udah desperate",
    content="""[ACTION: POV style — camera angle dari sudut pandang ibu, gelap, suara batuk]

POV: Anak lo batuk di tengah malam dan lo udah desperate.

[ACTION: Quick montage — cek Google "obat batuk anak alami", scrolling TikTok, wajah khawatir]

Lo udah Google, udah nanya grup WhatsApp, udah coba madu + jeruk nipis, uap air panas — MASIH batuk.

[ACTION: Tangan grab HP, buka TikTok, "nemu" Vitasma Kids]

Terus lo nemu ini di TikTok. Lo skeptis. Tapi 3.500 orang udah repurchase...

[ACTION: Close-up angka 3.5K+ repurchased]

Lo mikir "yaudah lah coba."

[ACTION: Paket dateng, unboxing quick, kasih ke anak]

3 hari kemudian...

[ACTION: Anak tidur nyenyak, no batuk, ibu senyum lega]

*audio shift ke musik calm/wholesome*

Best 95 ribu yang pernah gue spend.

[ACTION: Produk di samping anak yang tidur, teks "Rp95.000 — worth every rupiah"]

Kalo anak lo juga lagi batuk-batuk, gue taruh linknya di keranjang kuning.

[ACTION: Soft point ke bawah, smile]""",
    cta="Gue taruh linknya di keranjang kuning ya.",
    niche="kesehatan anak",
    script_type="affiliate",
    product_id=1,
    tags="pov,relatableibu,batukanak,vitasmakids,momtok,fyp",
    notes="Style: POV/Trending. Relatable mom angle. Cinematic feel. Audio shift for emotional impact. High shareability.",
)

print("All 5 scripts saved!")
