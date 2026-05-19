// src/agent.js — Agente Claude con agentic loop y herramientas
import Anthropic from '@anthropic-ai/sdk'
import { config } from './config.js'
import { getFaqs, getServices, getAvailableSlots, createAppointment } from './lib/db.js'

const anthropic = new Anthropic({ apiKey: config.anthropic.apiKey })

// ─── HERRAMIENTAS ────────────────────────────────────────────────────────────

const TOOLS = [
  {
    name: 'get_available_slots',
    description: 'Consulta los horarios o slots disponibles para reservar. Úsala cuando el cliente pregunte por disponibilidad, horarios libres, o quiera reservar/pedir cita.',
    input_schema: {
      type: 'object',
      properties: {
        service_name: {
          type: 'string',
          description: 'Nombre del servicio que quiere el cliente (opcional). Si no lo menciona, devuelve todos los disponibles.'
        }
      },
      required: []
    }
  },
  {
    name: 'book_appointment',
    description: 'Confirma y crea una reserva o cita. Úsala SOLO cuando el cliente haya elegido explícitamente un slot y dado su nombre.',
    input_schema: {
      type: 'object',
      properties: {
        slot_id:       { type: 'string', description: 'ID del slot (obtenido de get_available_slots)' },
        service_id:    { type: 'string', description: 'ID del servicio (obtenido de get_available_slots)' },
        customer_name: { type: 'string', description: 'Nombre del cliente para la reserva' },
        notes:         { type: 'string', description: 'Notas o peticiones especiales (opcional)' }
      },
      required: ['slot_id', 'customer_name']
    }
  },
  {
    name: 'escalate_to_human',
    description: 'Transfiere la conversación a un humano. Usa esta herramienta cuando: (1) el cliente lo pide explícitamente, (2) hay una queja grave, (3) no puedes resolver la duda tras 2 intentos, (4) la consulta requiere decisión humana.',
    input_schema: {
      type: 'object',
      properties: {
        reason: { type: 'string', description: 'Motivo del escalado en una frase' }
      },
      required: ['reason']
    }
  }
]

// ─── SYSTEM PROMPT ────────────────────────────────────────────────────────────

function buildSystemPrompt(business, faqs, services) {
  const faqText = faqs.length > 0
    ? faqs.map(f => `P: ${f.question}\nR: ${f.answer}`).join('\n\n')
    : '(Sin FAQs configuradas todavía)'

  const servicesText = services.length > 0
    ? services.map(s => [
        `• ${s.name}`,
        s.duration_min ? ` (${s.duration_min} min)` : '',
        s.price        ? ` — ${s.price}` : '',
        s.description  ? `\n  ${s.description}` : ''
      ].join('')).join('\n')
    : '(Sin servicios configurados)'

  const customPrompt = business.system_prompt
    ? `\nINSTRUCCIONES ADICIONALES DEL NEGOCIO:\n${business.system_prompt}\n`
    : ''

  return `Eres ${business.agent_name ?? 'el asistente virtual'} de ${business.name}.
Tu función es atender a los clientes por WhatsApp de forma eficiente y amable.
${customPrompt}
━━━ DATOS DEL NEGOCIO ━━━
Nombre: ${business.name}
Dirección: ${business.address ?? 'Consultar directamente'}
Horario: ${business.schedule ?? 'Consultar directamente'}
Teléfono: ${business.phone_display ?? 'No disponible'}

━━━ SERVICIOS ━━━
${servicesText}

━━━ PREGUNTAS FRECUENTES ━━━
${faqText}

━━━ REGLAS CRÍTICAS ━━━
1. Responde SIEMPRE en el idioma del cliente (detecta automáticamente).
2. Mensajes cortos y directos — máximo 3 párrafos en WhatsApp.
3. NUNCA inventes información que no esté en este prompt.
4. Si no sabes algo, di: "Para ese detalle, puedes contactarnos directamente."
5. Usa emojis con moderación para ser más cercano.
6. Para consultar disponibilidad o hacer reservas, usa las herramientas disponibles.
7. Confirma siempre los datos de una reserva antes de crearla.`
}

// ─── PROCESADOR DE HERRAMIENTAS ───────────────────────────────────────────────

async function processTool(toolName, toolInput, ctx) {
  const { business, conversationId, customerPhone } = ctx

  try {
    switch (toolName) {

      case 'get_available_slots': {
        const services = await getServices(business.id)
        let serviceId = null

        if (toolInput.service_name) {
          const match = services.find(s =>
            s.name.toLowerCase().includes(toolInput.service_name.toLowerCase())
          )
          serviceId = match?.id ?? null
        }

        const slots = await getAvailableSlots(business.id, serviceId)

        if (slots.length === 0) {
          return { available: false, message: 'No hay disponibilidad en los próximos 7 días.' }
        }

        const formatted = slots.map(slot => ({
          id: slot.id,
          service_id: slot.service_id,
          service_name: slot.services?.name ?? 'General',
          date: new Date(slot.starts_at).toLocaleDateString('es-ES', {
            weekday: 'long', day: 'numeric', month: 'long'
          }),
          time: new Date(slot.starts_at).toLocaleTimeString('es-ES', {
            hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Madrid'
          }),
          spots_left: slot.capacity - slot.booked
        }))

        return { available: true, slots: formatted }
      }

      case 'book_appointment': {
        const appt = await createAppointment({
          businessId:    business.id,
          conversationId,
          slotId:        toolInput.slot_id,
          serviceId:     toolInput.service_id ?? null,
          customerPhone,
          customerName:  toolInput.customer_name,
          notes:         toolInput.notes ?? null
        })
        return {
          success: true,
          appointment_id: appt.id,
          message: 'Reserva confirmada y guardada correctamente.'
        }
      }

      case 'escalate_to_human': {
        return { escalate: true, reason: toolInput.reason }
      }

      default:
        return { error: `Herramienta desconocida: ${toolName}` }
    }
  } catch (err) {
    console.error(`[Tool error] ${toolName}:`, err.message)
    return { error: err.message }
  }
}

// ─── AGENTE PRINCIPAL ─────────────────────────────────────────────────────────

/**
 * @returns {{ reply: string, shouldEscalate: boolean, escalateReason: string|null }}
 */
export async function runAgent({ business, faqs, services, history, userMessage, conversationId, customerPhone }) {
  const systemPrompt = buildSystemPrompt(business, faqs, services)

  const messages = [
    ...history.map(m => ({ role: m.role, content: m.content })),
    { role: 'user', content: userMessage }
  ]

  let shouldEscalate = false
  let escalateReason = null
  let finalReply = null

  // Agentic loop — max 6 iteraciones para evitar loops infinitos
  for (let i = 0; i < 6; i++) {
    const response = await anthropic.messages.create({
      model:       config.anthropic.model,
      max_tokens:  1024,
      system:      systemPrompt,
      tools:       TOOLS,
      messages
    })

    // Añadir respuesta al historial del loop
    messages.push({ role: 'assistant', content: response.content })

    if (response.stop_reason === 'end_turn') {
      const textBlock = response.content.find(b => b.type === 'text')
      finalReply = textBlock?.text ?? null
      break
    }

    if (response.stop_reason === 'tool_use') {
      const toolUseBlocks = response.content.filter(b => b.type === 'tool_use')
      const toolResults = []

      for (const toolUse of toolUseBlocks) {
        const result = await processTool(toolUse.name, toolUse.input, {
          business, conversationId, customerPhone
        })

        if (result.escalate) {
          shouldEscalate = true
          escalateReason = result.reason
        }

        toolResults.push({
          type: 'tool_result',
          tool_use_id: toolUse.id,
          content: JSON.stringify(result)
        })
      }

      messages.push({ role: 'user', content: toolResults })
      continue
    }

    break
  }

  return {
    reply: finalReply ?? 'Ha habido un problema procesando tu mensaje. Por favor inténtalo de nuevo.',
    shouldEscalate,
    escalateReason
  }
}
