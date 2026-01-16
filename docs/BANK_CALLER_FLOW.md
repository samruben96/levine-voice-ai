# Bank Caller Conversation Flow Design

**Last Updated**: January 2025
**Status**: Complete Design Ready for Implementation
**Scope**: Voice AI receptionist handling calls from bank representatives

## Executive Summary

Bank representatives call Harry Levine Insurance seeking renewal documents and invoices for mutual customers. This document provides the exact wording for a professional, efficient voice interaction that requires no special collection logic—just identification, clarification, and email routing.

## Call Detection

Banks typically identify themselves with these phrases:
- "Calling from [Bank Name]"
- "I'm with [Bank Name]"
- "On a recorded line"
- "We have a mutual customer"
- "Mutual insured"
- "Verify coverage"
- "Confirm renewal"
- "Verify insurance"

When these patterns appear, route immediately to MortgageeCertificateAgent (already exists for mortgagee/bank callers).

## Complete Conversation Flow

### Turn 1: Clarifying Question

**Exact Wording:**
```
"Let me clarify - are you requesting renewal documents or invoices for a mutual customer?"
```

**Why This Wording:**
- "Let me clarify" - Professional, acknowledges the request
- Specific options listed - "renewal documents or invoices"
- Open language - doesn't assume either/or
- Concise - Under 20 words
- Natural rhythm - Works well in voice

**Acceptable Variations** (if needed):
```
"Just to confirm, are you looking for renewal documents or invoices for a mutual customer?"
"Are you requesting renewal documents and invoices for a mutual customer?"
```

**DO NOT SAY:**
```
❌ "Are you submitting a written request for documentation pertaining to a mutual insured?"
❌ "What materials do you require?"
❌ "Can you provide more details?"
```

---

### Turn 2a: Caller Says YES

**Caller's Likely Response:**
- "Yes, I need renewal documents"
- "Yes, invoices for a client"
- "Yes, both actually"
- "Yes, for [Customer Name]"

**Exact Response:**
```
"Perfect. All requests must be submitted in writing to Info@HLInsure.com. No, we don't have a fax number."
```

**Why This Wording:**
- "Perfect" - Professional warmth, acknowledges they said the right thing
- "All requests must be submitted in writing" - Clear, firm, professional
- "to Info@HLInsure.com" - Email spelled out naturally (sounds like: "Info at H-L-Insure dot com")
- "No, we don't have a fax number" - Directly answers the question they'll probably ask next
- Proactive statement prevents follow-up

**Email Pronunciation Guide for Agent:**
When spoken aloud, say: "Info at H-L-Insure dot com"
(Do NOT spell each letter: "I-N-F-O")

---

### Turn 2b: Caller Says NO or Hesitates

**Caller's Likely Response:**
- "No, actually I'm calling about something else"
- "Hmm, not quite"
- "I'm not sure, let me explain"
- Silence or confusion

**Exact Response:**
```
"No problem. Can you tell me what you're calling about today?"
```

**Why This Wording:**
- Non-judgmental - "No problem"
- Open-ended - Lets them explain
- Warm - "can you tell me"
- Efficient - Gets to actual intent quickly

**Follow-up Actions:**
1. Listen to their explanation
2. If it IS a bank inquiry → Return to Turn 2a response
3. If it's something else → Route to appropriate agent using existing logic

---

### Turn 3: Error Recovery

**Scenario 1: Caller Asks "Can I speak to someone?"**

**Exact Response:**
```
"I'm not able to transfer calls for documentation requests, but the team at Info@HLInsure.com will be happy to help. They typically respond within one business day."
```

**Why This Works:**
- Acknowledges their request professionally
- Sets expectation that email is the channel
- Provides timeline confidence
- Doesn't promise a human transfer (we can't do it)

---

**Scenario 2: Caller Asks "When will it be processed?"**

**Exact Response:**
```
"That depends on what you're requesting. The team at Info@HLInsure.com will let you know the timeline once they receive your request."
```

**Why This Works:**
- Honest about timelines (we don't know)
- Defers to email team (they have systems for this)
- Empathetic - acknowledges their concern
- Professional - doesn't over-promise

---

**Scenario 3: Caller Insists on Talking to Someone**

**Exact Response:**
```
"I understand. Unfortunately for documentation requests, email is our process. The team responds quickly. Would you like me to confirm that email address again?"
```

**Why This Works:**
- Validates their frustration - "I understand"
- Firm but professional - "unfortunately for documentation requests"
- Confidence in process - "team responds quickly"
- Moves forward - Offers concrete next step (confirm email)

**If They Still Insist:**
```
"The fastest way to get what you need is through Info@HLInsure.com. Is there anything else I can clarify about the process?"
```

---

**Scenario 4: Caller Says "We need this urgently"**

**Exact Response:**
```
"I understand it's urgent. Please note that in your email to Info@HLInsure.com and they'll prioritize your request."
```

**Why This Works:**
- Validates urgency - "I understand it's urgent"
- Provides solution - "note that in your email"
- Empowers caller - Gives them control over prioritization
- Realistic - Doesn't promise same-day service

---

**Scenario 5: Caller Asks "What's your fax number?"**

**This is Already Answered** in Turn 2a:
```
"No, we don't have a fax number."
```

If they ask again:
```
"We don't accept fax requests. Email to Info@HLInsure.com is the way to go."
```

---

**Scenario 6: Caller Asks for a Different Email or Contact**

**Exact Response:**
```
"Info@HLInsure.com is our standard email for all documentation requests. If you have any questions about the process, you're welcome to call back during business hours—we're open Monday through Friday, 9 AM to 5 PM Eastern."
```

**Why This Works:**
- Clear - Directs to single email for consistency
- Helpful - Offers alternative (call back during hours)
- Professional - Provides office hours context

---

## Implementation Notes

### For Voice Agent Developers

1. **Integration Point**: Route bank callers to `route_call_mortgagee()` in Assistant agent
   - Already implemented in existing code
   - Uses `MortgageeCertificateAgent` (request_type="mortgagee")

2. **Key Difference from Other Mortgagee Calls**:
   - Bank callers DO NOT need business/personal insurance type collected
   - They're calling about a CUSTOMER'S policy, not their own
   - No alpha-split routing needed
   - Just email + confirmation

3. **Email Clarification**:
   - Use **Info@HLInsure.com** (not Certificate@hlinsure.com)
   - Banks are seeking documents on behalf of customers
   - This is a general information request, not a certificate

4. **Turn Detection**:
   - Wait for full response to clarifying question before responding
   - Don't interrupt if caller continues explaining
   - "What are you requesting?" pattern allows them to self-correct

### VUI Best Practices Applied

- **Conciseness**: Each response under 25 words
- **Clarity**: No jargon, no abbreviations
- **Anticipation**: "No fax number" mentioned proactively
- **Natural Flow**: Conversational, not robotic
- **Empathy**: Acknowledges urgency, validates frustration
- **Professional Tone**: Warm but formal (insurance industry standard)

## Testing Scenarios

### Happy Path (Yes → Process)
```
Caller: "Hi, I'm calling from First National Bank. We have a mutual customer and need renewal documents."
Agent: "Let me clarify - are you requesting renewal documents or invoices for a mutual customer?"
Caller: "Yes, both actually."
Agent: "Perfect. All requests must be submitted in writing to Info@HLInsure.com. No, we don't have a fax number."
Caller: "Okay, thanks."
Agent: "Is there anything else I can help with today?"
```

### Redirect Path (No → Clarify)
```
Caller: "Calling from ABC Bank. I'm actually calling about something else."
Agent: "No problem. Can you tell me what you're calling about today?"
Caller: "Actually, we do need those documents after all."
Agent: "Perfect. All requests must be submitted in writing to Info@HLInsure.com. No, we don't have a fax number."
```

### Escalation Path (Insists on Transfer)
```
Caller: "Can I speak to someone?"
Agent: "I'm not able to transfer calls for documentation requests, but the team at Info@HLInsure.com will be happy to help. They typically respond within one business day."
Caller: "Can't you just transfer me?"
Agent: "I understand. Unfortunately for documentation requests, email is our process. The team responds quickly. Would you like me to confirm that email address again?"
```

## Reference

**Related Documentation:**
- `/src/agents/mortgagee.py` - MortgageeCertificateAgent implementation
- `/src/agents/assistant.py` - route_call_mortgagee() function
- `OPERATIONS.md` - Staff directory and routing

**Email Addresses**:
- Info@HLInsure.com - General inquiries and mortgagee/bank requests
- Certificate@hlinsure.com - Certificate of insurance requests only

**Office Hours**: Monday-Friday, 9 AM-5 PM Eastern

**Caller Types Handled**:
- Bank representatives seeking customer documents
- Mortgage companies verifying coverage
- Lenders confirming renewal status
- Any "calling from [bank]" identifier
