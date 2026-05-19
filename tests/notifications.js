// src/notifications.js — Notificaciones de escalado
import twilio from 'twilio'
import { config } from './config.js'

const twilioClient = twilio(config.twilio.accountSid, config.twilio.authToken)

export async function notifyEscalation({ business, customerPhone, reason, lastMessages }) {
  const summary = lastMessages
    .slice(-6)
    .map(m => `${m.role === 'user' ? '👤 Cliente' : '🤖 Bot'}: ${m.content.slice(0, 120)}`)
    .join('\n')

  const body = `🚨 *Conversación escalada*

🏢 *Negocio:* ${business.name}
📱 *Cliente:* ${customerPhone}
📝 *Motivo:* ${reason}

*Últimos mensajes:*
${summary}

Responde directamente al cliente en WhatsApp: ${customerPhone}`.trim()

  const sent = []

  // 1. Email vía Resend (si está configurado)
  if (config.resend.apiKey && business.escalation_email) {
    try {
      const { Resend } = await import('resend')
      const resend = new Resend(config.resend.apiKey)
      await resend.emails.send({
        from:    config.resend.fromEmail,
        to:      business.escalation_email,
        subject: `🚨 Conversación escalada — ${business.name}`,
        text:    body
      })
      sent.push('email')
    } catch (err) {
      console.error('[Notify] Email error:', err.message)
    }
  }

  // 2. WhatsApp al responsable (si está configurado)
  if (business.escalation_whatsapp) {
    try {
      await twilioClient.messages.create({
        from: `whatsapp:${business.whatsapp_number}`,
        to:   `whatsapp:${business.escalation_whatsapp}`,
        body
      })
      sent.push('whatsapp')
    } catch (err) {
      console.error('[Notify] WhatsApp error:', err.message)
    }
  }

  if (sent.length === 0) {
    console.warn('[Notify] No hay canales de escalado configurados para:', business.name)
  } else {
    console.log('[Notify] Escalado enviado por:', sent.join(', '))
  }

  return sent
}
