// src/lib/db.js — Todas las operaciones de base de datos
import { supabase } from './supabase.js'

// ─── NEGOCIO ────────────────────────────────────────────────────────────────

export async function getBusinessByPhone(twilioNumber) {
  const { data, error } = await supabase
    .from('businesses')
    .select('*')
    .eq('whatsapp_number', twilioNumber)
    .eq('active', true)
    .single()

  if (error) throw new Error(`Negocio no encontrado [${twilioNumber}]: ${error.message}`)
  return data
}

export async function getFaqs(businessId) {
  const { data, error } = await supabase
    .from('faqs')
    .select('question, answer')
    .eq('business_id', businessId)
    .order('created_at')

  if (error) throw new Error(`FAQs error: ${error.message}`)
  return data ?? []
}

export async function getServices(businessId) {
  const { data, error } = await supabase
    .from('services')
    .select('id, name, duration_min, description, price')
    .eq('business_id', businessId)
    .eq('active', true)
    .order('name')

  if (error) throw new Error(`Services error: ${error.message}`)
  return data ?? []
}

// ─── CONVERSACIÓN ───────────────────────────────────────────────────────────

export async function getOrCreateConversation(businessId, customerPhone) {
  // Buscar activa existente
  const { data: existing } = await supabase
    .from('conversations')
    .select('*')
    .eq('business_id', businessId)
    .eq('customer_phone', customerPhone)
    .eq('status', 'active')
    .maybeSingle()

  if (existing) return existing

  const { data, error } = await supabase
    .from('conversations')
    .insert({ business_id: businessId, customer_phone: customerPhone })
    .select()
    .single()

  if (error) throw new Error(`Conversation create error: ${error.message}`)
  return data
}

export async function getConversationHistory(conversationId, limit = 20) {
  const { data, error } = await supabase
    .from('messages')
    .select('role, content, created_at')
    .eq('conversation_id', conversationId)
    .order('created_at', { ascending: false })
    .limit(limit)

  if (error) throw new Error(`History error: ${error.message}`)
  return (data ?? []).reverse()
}

export async function saveMessage(conversationId, role, content, metadata = {}) {
  const { data, error } = await supabase
    .from('messages')
    .insert({ conversation_id: conversationId, role, content, metadata })
    .select()
    .single()

  if (error) throw new Error(`Save message error: ${error.message}`)
  return data
}

export async function escalateConversation(conversationId) {
  const { error } = await supabase
    .from('conversations')
    .update({ status: 'escalated', escalated_at: new Date().toISOString() })
    .eq('id', conversationId)

  if (error) throw new Error(`Escalate error: ${error.message}`)
}

export async function reopenConversation(businessId, customerPhone) {
  // Cuando un cliente escalado vuelve a escribir, reabrimos
  const { error } = await supabase
    .from('conversations')
    .update({ status: 'active', escalated_at: null })
    .eq('business_id', businessId)
    .eq('customer_phone', customerPhone)
    .eq('status', 'escalated')

  if (error) console.error('Reopen conversation error:', error.message)
}

// ─── CITAS ──────────────────────────────────────────────────────────────────

export async function getAvailableSlots(businessId, serviceId = null, hoursAhead = 168) {
  const from = new Date().toISOString()
  const to = new Date(Date.now() + hoursAhead * 3600 * 1000).toISOString()

  let query = supabase
    .from('availability_slots')
    .select('id, starts_at, ends_at, capacity, booked, service_id, services(name)')
    .eq('business_id', businessId)
    .gte('starts_at', from)
    .lte('starts_at', to)
    .order('starts_at')
    .limit(10)

  if (serviceId) query = query.eq('service_id', serviceId)

  const { data, error } = await query
  if (error) throw new Error(`Slots error: ${error.message}`)

  // Solo devolver slots con plazas libres
  return (data ?? []).filter(s => s.booked < s.capacity)
}

export async function createAppointment({
  businessId, conversationId, slotId, serviceId,
  customerPhone, customerName, notes
}) {
  // Verificar disponibilidad
  const { data: slot, error: slotError } = await supabase
    .from('availability_slots')
    .select('capacity, booked')
    .eq('id', slotId)
    .single()

  if (slotError || !slot) throw new Error('Slot no encontrado')
  if (slot.booked >= slot.capacity) throw new Error('Slot sin disponibilidad')

  // Crear cita
  const { data: appt, error: apptError } = await supabase
    .from('appointments')
    .insert({
      business_id: businessId,
      conversation_id: conversationId,
      slot_id: slotId,
      service_id: serviceId ?? null,
      customer_phone: customerPhone,
      customer_name: customerName,
      notes: notes ?? null,
      status: 'confirmed',
      confirmed_at: new Date().toISOString()
    })
    .select()
    .single()

  if (apptError) throw new Error(`Appointment error: ${apptError.message}`)

  // Incrementar booked
  await supabase
    .from('availability_slots')
    .update({ booked: slot.booked + 1 })
    .eq('id', slotId)

  return appt
}
