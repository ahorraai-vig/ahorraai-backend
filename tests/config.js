// src/config.js — Validación de variables de entorno al arrancar
import 'dotenv/config'

const required = [
  'SUPABASE_URL',
  'SUPABASE_SERVICE_ROLE_KEY',
  'ANTHROPIC_API_KEY',
  'TWILIO_ACCOUNT_SID',
  'TWILIO_AUTH_TOKEN',
]

const missing = required.filter(k => !process.env[k])
if (missing.length > 0) {
  console.error('❌ Faltan variables de entorno:', missing.join(', '))
  console.error('   Copia .env.example a .env y rellena los valores.')
  process.exit(1)
}

export const config = {
  port: Number(process.env.PORT) || 3000,

  supabase: {
    url: process.env.SUPABASE_URL,
    serviceRoleKey: process.env.SUPABASE_SERVICE_ROLE_KEY,
  },

  anthropic: {
    apiKey: process.env.ANTHROPIC_API_KEY,
    model: 'claude-sonnet-4-20250514',
  },

  twilio: {
    accountSid: process.env.TWILIO_ACCOUNT_SID,
    authToken: process.env.TWILIO_AUTH_TOKEN,
  },

  resend: {
    apiKey: process.env.RESEND_API_KEY || null,
    fromEmail: process.env.NOTIFICATION_FROM_EMAIL || 'noreply@recepcionista.ai',
  },

  // En producción valida la firma Twilio; en dev la omitimos
  validateTwilioSignature: process.env.NODE_ENV === 'production',
}
