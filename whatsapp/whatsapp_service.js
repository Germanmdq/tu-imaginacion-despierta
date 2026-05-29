// ─────────────────────────────────────────────────────────────
// Ánima — WhatsApp Service (whatsapp-web.js)
// Puerto: 3001
// Expone una API REST que el backend Python llama para enviar
// mensajes de WhatsApp sin necesitar la API oficial de Meta.
// ─────────────────────────────────────────────────────────────

const { Client, LocalAuth } = require("whatsapp-web.js");
const qrcode  = require("qrcode-terminal");
const express = require("express");

const app  = express();
app.use(express.json());

// ── Estado del cliente ──
let clientReady = false;
let qrData      = null;

// ── Cliente WhatsApp ──
const client = new Client({
    authStrategy: new LocalAuth({ dataPath: "./.wwebjs_auth" }),
    puppeteer: {
        headless: true,
        args: [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-accelerated-2d-canvas",
            "--no-first-run",
            "--no-zygote",
            "--disable-gpu"
        ]
    }
});

// ── Eventos ──
client.on("qr", (qr) => {
    qrData = qr;
    clientReady = false;
    console.log("\n════════════════════════════════════════");
    console.log("  Escaneá este QR con WhatsApp en tu celular:");
    console.log("  Ajustes → Dispositivos vinculados → Vincular dispositivo");
    console.log("════════════════════════════════════════\n");
    qrcode.generate(qr, { small: true });
});

client.on("ready", () => {
    clientReady = true;
    qrData      = null;
    console.log("✅ WhatsApp conectado y listo.");
});

client.on("authenticated", () => {
    console.log("🔐 Autenticación exitosa.");
});

client.on("auth_failure", (msg) => {
    console.error("❌ Error de autenticación:", msg);
    clientReady = false;
});

client.on("disconnected", (reason) => {
    console.warn("⚠️  WhatsApp desconectado:", reason);
    clientReady = false;
    // Reintentar conexión después de 10 segundos
    setTimeout(() => {
        console.log("🔄 Reconectando...");
        client.initialize();
    }, 10000);
});

client.initialize();

// ─────────────────────────────────────────────────────────────
// API REST
// ─────────────────────────────────────────────────────────────

// GET /status — estado de la conexión
app.get("/status", (req, res) => {
    res.json({
        ready: clientReady,
        has_qr: !!qrData,
        qr: qrData || null
    });
});

// POST /send — enviar mensaje
// Body: { "to": "5491112345678", "message": "Hola!" }
// El número va sin + ni espacios, con código de país
app.post("/send", async (req, res) => {
    const { to, message } = req.body;

    if (!clientReady) {
        return res.status(503).json({
            ok: false,
            error: "WhatsApp no está conectado. Escaneá el QR en /status"
        });
    }

    if (!to || !message) {
        return res.status(400).json({
            ok: false,
            error: "Campos requeridos: 'to' (número) y 'message' (texto)"
        });
    }

    // Formatear número: debe terminar en @c.us
    const chatId = to.includes("@c.us") ? to : `${to.replace(/\D/g, "")}@c.us`;

    try {
        await client.sendMessage(chatId, message);
        console.log(`📤 Enviado a ${chatId}: ${message.substring(0, 60)}...`);
        res.json({ ok: true, to: chatId });
    } catch (err) {
        console.error("Error al enviar:", err.message);
        res.status(500).json({ ok: false, error: err.message });
    }
});

// POST /send-bulk — enviar a múltiples números
// Body: { "contacts": [{ "to": "549...", "message": "..." }] }
app.post("/send-bulk", async (req, res) => {
    const { contacts } = req.body;

    if (!clientReady) {
        return res.status(503).json({ ok: false, error: "WhatsApp no conectado" });
    }

    if (!Array.isArray(contacts) || contacts.length === 0) {
        return res.status(400).json({ ok: false, error: "'contacts' debe ser un array" });
    }

    const results = [];
    for (const contact of contacts) {
        const chatId = `${contact.to.replace(/\D/g, "")}@c.us`;
        try {
            await client.sendMessage(chatId, contact.message);
            results.push({ to: chatId, ok: true });
            // Pausa entre mensajes para no ser detectado como spam
            await new Promise(r => setTimeout(r, 1500));
        } catch (err) {
            results.push({ to: chatId, ok: false, error: err.message });
        }
    }

    res.json({ ok: true, results });
});

// GET /health
app.get("/health", (req, res) => res.json({ status: "ok" }));

// ── Iniciar servidor ──
const PORT = process.env.WA_PORT || 3001;
app.listen(PORT, () => {
    console.log(`\n🚀 WhatsApp Service corriendo en http://localhost:${PORT}`);
    console.log(`   GET  /status     → ver estado + QR`);
    console.log(`   POST /send       → enviar mensaje`);
    console.log(`   POST /send-bulk  → enviar a varios\n`);
});
