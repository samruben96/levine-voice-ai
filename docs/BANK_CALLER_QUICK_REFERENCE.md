# Bank Caller Quick Reference

**For**: Voice Agent Developers & QA Testing

---

## Detection Triggers

Route to `route_call_mortgagee()` when caller says:
- "Calling from [bank name]"
- "Bank representative"
- "Mutual customer/insured"
- "Verify coverage"
- "Confirm renewal"
- "On a recorded line"

---

## The Exact Script

### Initial Question
```
"Let me clarify - are you requesting renewal documents
 or invoices for a mutual customer?"
```

### If YES
```
"Perfect. All requests must be submitted in writing to
 Info@HLInsure.com. No, we don't have a fax number."
```

### If NO / Unsure
```
"No problem. Can you tell me what you're calling about today?"
```

---

## Common Questions & Answers

| Question | Response |
|----------|----------|
| "Can I speak to someone?" | "I'm not able to transfer calls for documentation requests, but the team at Info@HLInsure.com will be happy to help. They typically respond within one business day." |
| "When will it be processed?" | "That depends on what you're requesting. The team at Info@HLInsure.com will let you know the timeline once they receive your request." |
| "Do you have a fax number?" | "No, we don't have a fax number." |
| "This is urgent" | "I understand it's urgent. Please note that in your email to Info@HLInsure.com and they'll prioritize your request." |
| "Can you call me back?" | "I can help point you in the right direction. Email Info@HLInsure.com and mention you need this urgent. They'll contact you." |

---

## Key Points

✓ **Use Info@HLInsure.com** (not Certificate@hlinsure.com)
✓ **Say "No fax number" proactively** - prevents follow-up questions
✓ **Don't collect personal/business info** - They're not OUR customer
✓ **Keep it under 25 words per turn** - Professional voice pace
✓ **Never transfer for doc requests** - Email is the standard

---

## Why This Matters

Banks calling = professional, routine, predictable requests. Efficiently handling them:
- Saves 2-3 minutes per call
- Reduces transfer attempts
- Sets correct expectations
- Improves caller satisfaction

---

## Integration Status

✓ Already Integrated: `MortgageeCertificateAgent` exists
✓ Routing: `route_call_mortgagee()` in Assistant agent
✓ Email: Info@hlinsure.com configured

**No code changes needed** - Just use this exact wording in the agent's instructions for bank callers.
