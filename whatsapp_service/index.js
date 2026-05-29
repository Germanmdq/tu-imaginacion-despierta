const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const express = require('express');

const app = express();
app.use(express.json());

const PORT = 3001;

let latestQR = '';
let isReady = false;

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

client.on('qr', async (qr) => {
    console.log('Nuevo QR generado. Ingresa a http://localhost:3001/qr para escanearlo.');
    try {
        latestQR = await qrcode.toDataURL(qr);
    } catch (err) {
        console.error('Error generando imagen QR', err);
    }
});

client.on('ready', () => {
    console.log('¡WhatsApp Web conectado y listo para enviar mensajes!');
    isReady = true;
    latestQR = ''; // Limpiar QR
});

client.on('authenticated', () => {
    console.log('Autenticado exitosamente.');
});

client.on('auth_failure', msg => {
    console.error('Error de autenticación en WhatsApp:', msg);
});

client.initialize();

// Endpoint para que el dueño escanee el QR desde el navegador sin tocar la terminal
app.get('/qr', (req, res) => {
    if (isReady) {
        return res.send(`
            <div style="font-family: sans-serif; text-align: center; margin-top: 50px;">
                <h1 style="color: #065f46;">✅ WhatsApp ya está vinculado y funcionando.</h1>
                <p>Tu computadora ya está actuando como el servidor que envía mensajes.</p>
                <p>Podés cerrar esta pestaña.</p>
            </div>
        `);
    }

    if (!latestQR) {
        return res.send(`
            <div style="font-family: sans-serif; text-align: center; margin-top: 50px;">
                <h2>⏳ Cargando WhatsApp...</h2>
                <p>Por favor, esperá unos 15 a 30 segundos y recargá (F5) esta página.</p>
            </div>
        `);
    }

    res.send(`
        <div style="font-family: sans-serif; text-align: center; margin-top: 50px;">
            <h2>📱 Vinculación de WhatsApp (Solo para el Administrador)</h2>
            <p>1. Abrí WhatsApp en tu celular principal (el que va a ENVIAR los mensajes a la gente).</p>
            <p>2. Andá a <b>Dispositivos Vinculados</b> > <b>Vincular un dispositivo</b>.</p>
            <p>3. Escaneá este código QR:</p>
            <img src="${latestQR}" alt="QR Code" style="width: 300px; height: 300px; border: 2px solid #ccc; border-radius: 10px; padding: 10px;">
            <p style="color: #666; font-size: 14px; margin-top: 20px;">Nota: El código se actualiza cada 20 segundos. Recargá la página si caduca.</p>
        </div>
    `);
});

// Endpoint para enviar mensajes (Llamado internamente por Python)
app.post('/send', async (req, res) => {
    try {
        if (!isReady) {
            return res.status(503).json({ error: 'WhatsApp no está listo todavía.' });
        }

        const { to, message } = req.body;
        
        if (!to || !message) {
            return res.status(400).json({ error: 'Faltan los campos "to" o "message"' });
        }

        let cleanNumber = to.replace(/\D/g, '');
        const chatId = `${cleanNumber}@c.us`;

        console.log(`Enviando mensaje de WhatsApp a: ${chatId}`);
        const response = await client.sendMessage(chatId, message);
        
        res.json({ success: true, messageId: response.id.id });
    } catch (error) {
        console.error('Error enviando mensaje de WhatsApp:', error);
        res.status(500).json({ error: error.toString() });
    }
});

app.listen(PORT, () => {
    console.log(`Servidor de WhatsApp corriendo en el puerto ${PORT}`);
    console.log(`----> ENTRÁ A http://localhost:3001/qr PARA ESCANEAR EL CÓDIGO <----`);
});
