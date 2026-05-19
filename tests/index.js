// src/index.js — Servidor Express + Webhook Twilio WhatsApp
import 'dotenv/config'
import express from 'express'
import twilio from 'twilio'
import { config } from './config.js'
import {
  getBusinessByPhone,
  getOrCreateConversation,
  getConversationHistory,
  saveMessage,
  escalateConversation,
  reopenConversation,
  getFaqs,
  getServices
} from './lib/db.js'
import { runAgent } from './agent.js'
import { notifyEscalation } from './notifications.js'

const app = express()
app.use(express.urlencoded({ extended: false }))
app.use(express.json())

// ─── VALIDACIÓN DE FIRMA TWILIO (solo en producción) ─────────────────────────
function twilioMiddleware(req, res, next) {
  if (!config.validateTwilioSignature) return next()

  const valid = twilio.validateRequest(
    config.twilio.authToken,
    req.headers['x-twilio-signature'] ?? '',
    `${req.protocol}://${req.get('host')}${req.originalUrl}`,
    req.body
  )
  if (!valid) return res.status(403).send('Forbidden')
  next()
}

// ─── HELPERS ─────────────────────────────────────────────────────────────────
function twimlReply(res, message) {
  const twiml = new twilio.twiml.MessagingResponse()
  twiml.message(message)
  res.type('text/xml').send(twiml.toString())
}

function twimlEmpty(res) {
  res.type('text/xml').send('<Response></Response>')
}

function log(level, ...args) {
  const ts = new Date().toISOString().slice(11, 19)
  console.log(`[${ts}] [${level}]`, ...args)
}

// ─── HEALTH CHECK ─────────────────────────────────────────────────────────────
app.get('/', (_req, res) => {
  res.json({
    service: 'Recepcionista IA',
    status:  'ok',
    ts:      new Date().toISOString(),
    env:     process.env.NODE_ENV ?? 'development'
  })
})

// ─── WEBHOOK PRINCIPAL: mensajes WhatsApp entrantes ───────────────────────────
app.post('/webhook/whatsapp', twilioMiddleware, async (req, res) => {
  const {
    Body:        rawBody,
    From:        fromRaw,      // "whatsapp:+34600000000"
    To:          toRaw,        // "whatsapp:+34700000000"
    ProfileName: profileName,  // nombre WhatsApp del cliente
    NumMedia:    numMedia,
  } = req.body

  const customerPhone = fromRaw?.replace('whatsapp:', '') ?? ''
  const businessPhone = toRaw?.replace('whatsapp:', '')   ?? ''
  const userMessage   = (rawBody ?? '').trim()

  log('INFO', `MSG ${customerPhone} → ${businessPhone}: "${userMessage.slice(0, 60)}"`)

  // Mensajes sin texto (imágenes, audio, etc.)
  if (!userMessage) {
    if (Number(numMedia) > 0) {
      return twimlReply(res, 'He recibido tu archivo, pero solo puedo procesar mensajes de texto por ahora. ¿En qué te puedo ayudar?')
    }
    return twimlEmpty(res)
  }

  try {
    // 1. Obtener negocio por número Twilio
    let business
    try {
      business = await getBusinessByPhone(businessPhone)
    } catch {
      log('WARN', `Negocio no encontrado para ${businessPhone}`)
      return twimlEmpty(res)
    }

    // 2. Obtener conversación activa
    let conversation = await getOrCreateConversation(business.id, customerPhone)

    // 2b. Si la conversación estaba escalada, dar opción de reabrir
    if (conversation.status === 'escalated') {
      const keywords = ['hola', 'hello', 'reabrir', 'nuevo', 'otra', 'diferente', 'hi']
      const isGreeting = keywords.some(k => userMessage.toLowerCase().includes(k))

      if (isGreeting) {
        await reopenConversation(business.id, customerPhone)
        conversation = await getOrCreateConversation(business.id, customerPhone)
        log('INFO', `Conversación reabierta para ${customerPhone}`)
      } else {
        // Conversación escalada, el humano lleva el control
        log('INFO', `Conversación escalada — bot silenciado para ${customerPhone}`)
        return twimlEmpty(res)
      }
    }

    // 3. Guardar mensaje del usuario
    await saveMessage(conversation.id, 'user', userMessage, {
      profile_name: profileName ?? null,
      twilio_sid:   req.body.MessageSid ?? null
    })

    // 4. Cargar contexto del negocio e historial en paralelo
    const [faqs, services, history] = await Promise.all([
      getFaqs(business.id),
      getServices(business.id),
      getConversationHistory(conversation.id, 20)
    ])

    // 5. Ejecutar agente IA
    const { reply, shouldEscalate, escalateReason } = await runAgent({
      business,
      faqs,
      services,
      history:       history.slice(0, -1), // excluir el mensaje recién guardado
      userMessage,
      conversationId: conversation.id,
      customerPhone
    })

    // 6. Gestionar escalado si el agente lo decide
    if (shouldEscalate) {
      log('INFO', `Escalando conversación ${conversation.id}: ${escalateReason}`)
      await escalateConversation(conversation.id)
      await notifyEscalation({
        business,
        customerPhone,
        reason:       escalateReason,
        lastMessages: history
      })
    }

    // 7. Guardar respuesta del bot
    await saveMessage(conversation.id, 'assistant', reply)

    log('INFO', `REPLY → ${customerPhone}: "${reply.slice(0, 80)}..."`)
    twimlReply(res, reply)

  } catch (err) {
    log('ERROR', 'Webhook error:', err.message)
    console.error(err.stack)
    twimlReply(res,
      'Lo siento, ha habido un error técnico. Por favor inténtalo de nuevo en unos minutos.'
    )
  }
})

// ─── WEBHOOK STATUS (delivery receipts de Twilio) ─────────────────────────────
app.post('/webhook/status', (req, res) => {
  log('STATUS', `${req.body.MessageSid}: ${req.body.MessageStatus}`)
  twimlEmpty(res)
})

// ─── API INTERNA: guardar negocio desde el HTML de onboarding ────────────────
app.post('/api/businesses', async (req, res) => {
  // Esta ruta la usa el formulario de onboarding del HTML
  const apiKey = req.headers['x-api-key']
  if (apiKey !== process.env.INTERNAL_API_KEY) {
    return res.status(401).json({ error: 'Unauthorized' })
  }

  try {
    const { supabase } = await import('./lib/supabase.js')
    const { data, error } = await supabase
      .from('businesses')
      .upsert(req.body, { onConflict: 'whatsapp_number' })
      .select()
      .single()

    if (error) throw error
    res.json({ ok: true, id: data.id })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// ─── ARRANQUE ─────────────────────────────────────────────────────────────────
app.listen(config.port, () => {
  log('INFO', `✅ Recepcionista IA · Puerto ${config.port}`)
  log('INFO', `   Webhook:  POST /webhook/whatsapp`)
  log('INFO', `   Status:   POST /webhook/status`)
  log('INFO', `   Health:   GET  /`)
  log('INFO', `   Entorno:  ${process.env.NODE_ENV ?? 'development'}`)
})
