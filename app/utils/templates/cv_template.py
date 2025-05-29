CV_TEMPLATE_HTML = """
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cover Letter</title>
    <style>
        @font-face {
            font-family: 'Arial';
            src: local('Arial');
        }
        
        @page {
            size: A4;
            margin: 0;
        }
        
        body {
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #fff;
        }

        .cover-letter {
            background-color: #fff;
            padding: 30px;
            width: 210mm; /* A4 width */
            height: 297mm; /* A4 height */
            box-sizing: border-box;
            font-size: 11pt; /* Base font size */
        }

        .sender-info {
            margin-bottom: 20px;
        }

        .sender-info h1 {
            font-size: 24pt; /* Larger font for name */
            font-weight: bold;
            margin: 0 0 5px 0;
            color: #333;
        }

        .sender-info p {
            margin: 2px 0;
            font-size: 10pt;
            color: #555;
        }

        .date {
            text-align: right;
            margin-bottom: 20px;
            font-size: 11pt;
            color: #333;
        }

        .recipient-info {
            margin-bottom: 15px;
        }

        .recipient-info p {
            margin: 2px 0;
            font-size: 11pt;
            color: #333;
        }
        .recipient-info .recipient-name {
            font-weight: bold;
        }

        .salutation {
            margin-bottom: 15px;
            font-size: 11pt;
            color: #333;
        }

        .body-paragraph {
            margin-bottom: 12px;
            text-align: justify;
            font-size: 11pt;
            color: #333;
        }

        .closing {
            margin-top: 20px;
            margin-bottom: 5px;
            font-size: 11pt;
            color: #333;
        }

        .signature {
            font-size: 11pt;
            color: #333;
        }
    </style>
</head>
<body>
    <div class="cover-letter">
        <div class="sender-info">
            <h1>[Nama Pengguna]</h1>
            <p>[Alamat Pengguna]</p>
            <p>[Nomor Telepon Pengguna]</p>
            <p>[Email Pengguna]</p>
        </div>

        <div class="date">
            [Tanggal Saat Ini]
        </div>

        <div class="recipient-info">
            <p class="recipient-name">[Nama Manajer Perekrutan atau Kepada Siapa Surat Ditujukan]</p>
            <p>[Jabatan Manajer Perekrutan]</p>
            <p>[Nama Perusahaan]</p>
            <p>[Alamat Perusahaan]</p>
        </div>

        <div class="salutation">
            <p>Yth. [Bapak/Ibu] [Nama Belakang Manajer Perekrutan],</p>
        </div>

        <div class="body-paragraph">
            <p>[Paragraf Pembuka: Sebutkan posisi yang dilamar, di mana Anda menemukan lowongan, dan antusiasme Anda. Perkenalkan diri secara singkat dan tesis utama mengapa Anda cocok.]</p>
        </div>

        <div class="body-paragraph">
            <p>[Paragraf Isi 1: Fokus pada 1-2 kualifikasi/pengalaman paling relevan dari CV Anda yang cocok dengan deskripsi pekerjaan. Berikan contoh konkret, gunakan teknik STAR secara implisit. Hubungkan langsung dengan kebutuhan pekerjaan.]</p>
        </div>

        <div class="body-paragraph">
            <p>[Paragraf Penutup: Ulangi antusiasme Anda. Tegaskan kembali keyakinan Anda sebagai kandidat yang cocok. Sertakan ajakan bertindak untuk wawancara. Sebutkan referensi ke CV.]</p>
        </div>

        <div class="closing">
            <p>Hormat saya,</p>
        </div>

        <div class="signature">
            <p>[Nama Pengguna]</p>
        </div>
    </div>
</body>
</html>
```
"""
