# Bank Caller Conversation Flow - Complete Design Summary

**Status**: Ready for Implementation
**Last Updated**: January 15, 2025
**Scope**: Voice AI handling of bank representative calls

---

## What This Is

A complete conversation design for when bank representatives call Harry Levine Insurance seeking renewal documents and invoices for mutual customers. Includes exact wording, error recovery, and implementation guide.

---

## The Five Exact Responses You Need

### 1. Opening Clarifying Question
```
"Let me clarify - are you requesting renewal documents
 or invoices for a mutual customer?"
```
**Purpose**: Confirms they're asking for the right thing (avoids assumptions)
**Length**: 16 words | **Duration**: ~6 seconds

---

### 2. Response When They Say YES
```
"Perfect. All requests must be submitted in writing to
 Info@HLInsure.com. No, we don't have a fax number."
```
**Purpose**: Provides full answer + preempts follow-up questions
**Length**: 22 words | **Duration**: ~9 seconds

---

### 3. Response When They Say NO or Are Unsure
```
"No problem. Can you tell me what you're calling about today?"
```
**Purpose**: Non-judgmental redirect to their actual need
**Length**: 10 words | **Duration**: ~4 seconds

---

### 4. If They Ask "Can I Speak to Someone?"
```
"I'm not able to transfer calls for documentation requests, but
 the team at Info@HLInsure.com will be happy to help.
 They typically respond within one business day."
```
**Purpose**: Sets expectation that email is the standard, provides timeline confidence
**Length**: 28 words | **Duration**: ~11 seconds

---

### 5. If They Say "This Is Urgent"
```
"I understand it's urgent. Please note that in your email to
 Info@HLInsure.com and they'll prioritize your request."
```
**Purpose**: Validates their concern while maintaining process
**Length**: 20 words | **Duration**: ~8 seconds

---

## The Design Thinking Behind Each Response

### Clarifying Question
- **"Let me clarify"** - Professional, acknowledges their request isn't complete
- **"renewal documents or invoices"** - Specific options (most common requests)
- **"for a mutual customer"** - Confirms we understand they're calling ABOUT a customer
- **Open not closed** - Allows them to add context ("Yes, and I also need...")

### Information Response
- **"Perfect"** - Positive reinforcement for clear request
- **"All requests must be submitted in writing"** - Firm, professional, non-negotiable
- **"Info@HLInsure.com"** - Specific, clear, searchable
- **"No fax number"** - Proactive = caller won't ask follow-up question
- **Concise** - All necessary info in 22 words

### Redirect Response
- **"No problem"** - No judgment or frustration
- **Open-ended** - Lets them explain their actual need
- **"Can you tell me"** - Warm, conversational, not "What do you need?"

### Error Recovery (Transfer Request)
- **"I'm not able to transfer"** - Honest, sets boundary
- **"but...will be happy to help"** - Immediately offers alternative
- **"typically respond within one business day"** - Gives timeline confidence (sets expectations)
- **Longer** (28 words) - Justified because it's error recovery, caller is frustrated

### Error Recovery (Urgency)
- **"I understand it's urgent"** - Validates emotion first
- **"Please note that in your email"** - Empowers caller with action
- **"they'll prioritize"** - Gives them control and confidence
- **Natural** - Real phrase people use when stressed

---

## How It Integrates with Existing Code

**Already Built:**
- `route_call_mortgagee()` in Assistant agent
- `MortgageeCertificateAgent` class
- `provide_mortgagee_email_info()` tool
- Info@hlinsure.com email configured

**Just Need:**
- Add the exact wording to agent instructions
- Add error recovery tools for edge cases
- Test the flow with bank scenarios
- Update agent's `on_enter()` to use clarifying question first

**Timeline to Production:**
- Update instructions: 5 minutes
- Add error recovery tools: 15 minutes
- Write tests: 30 minutes
- QA testing: 30 minutes
- **Total**: ~1.5 hours

---

## Why This Design Works

### For Callers (UX)
- Quick (45-90 seconds total)
- Clear (email requirement stated upfront)
- Professional (insurance industry tone)
- Efficient (no unnecessary transfers)
- Empathetic (acknowledges frustration/urgency)

### For Business (Operations)
- Filters out non-documentation requests early
- Prevents transfer attempts (saves staff time)
- Email trail (traceable, documented)
- Standard process (consistency)
- Proactive (prevents fax question follow-ups)

### For Voice AI (Technical)
- Short responses (fast generation, natural speech)
- Clear intent detection (yes/no/other)
- Reusable patterns (mirrors other error recovery)
- Low latency (no complex routing logic)
- Natural vocabulary (common words, contractions)

---

## What NOT to Do

❌ "Are you submitting a written request for documentation pertaining to a mutual insured?"
❌ "What materials do you require?"
❌ "Can you provide more details?" (too open-ended)
❌ "Let me transfer you to someone" (they don't transfer doc requests)
❌ "I'll have to check with the team" (delays caller unnecessarily)
❌ "Maybe the bank/lender can call us back" (unhelpful)

---

## Complete File List

You now have four detailed documents:

1. **`docs/BANK_CALLER_FLOW.md`** (Detailed Design)
   - Full design rationale
   - All 6 error recovery scenarios
   - Testing scenarios
   - Best practices applied

2. **`docs/BANK_CALLER_QUICK_REFERENCE.md`** (For QA/Testing)
   - One-page reference
   - Exact script table
   - Detection triggers
   - Key points summary

3. **`docs/BANK_CALLER_DIALOG_FLOW.txt`** (Visual)
   - ASCII diagram of conversation flow
   - Decision points
   - Branching logic
   - Success criteria

4. **`docs/BANK_CALLER_IMPLEMENTATION.md`** (For Developers)
   - Python integration examples
   - Tool signatures
   - Test examples
   - Deployment checklist

---

## Key Contact Info for Calls

| Item | Value |
|------|-------|
| **Email** | Info@HLInsure.com |
| **Email (Certificates only)** | Certificate@hlinsure.com |
| **Office Hours** | Monday-Friday, 9 AM-5 PM Eastern |
| **Fax** | NOT AVAILABLE |

---

## Success Metrics

After implementation, track:
- **Call duration**: Target 45-90 seconds
- **Transfer attempts for doc requests**: Should be 0
- **Caller satisfaction**: Did they understand email requirement?
- **Follow-up calls**: Did they email or call back asking?
- **Accuracy**: Are we routing to correct email?

---

## Next Steps

For **Product/Operations**:
1. Review the design doc (`docs/BANK_CALLER_FLOW.md`)
2. Validate wording with insurance compliance
3. Confirm email addresses with CS team
4. Set expectations for response time

For **Engineering**:
1. Add tools to MortgageeCertificateAgent
2. Update on_enter() to ask clarifying question
3. Implement error recovery branches
4. Write unit + integration tests
5. QA test with bank scenarios

For **QA**:
1. Use `docs/BANK_CALLER_QUICK_REFERENCE.md`
2. Test each scenario in `docs/BANK_CALLER_DIALOG_FLOW.txt`
3. Verify exact wording matches
4. Test error recovery paths
5. Confirm no unwanted transfers

---

## Questions?

Refer back to the relevant design document:
- **"Why this wording?"** → `docs/BANK_CALLER_FLOW.md` (Design Rationale section)
- **"Quick copy-paste version?"** → `docs/BANK_CALLER_QUICK_REFERENCE.md`
- **"Visual overview?"** → `docs/BANK_CALLER_DIALOG_FLOW.txt`
- **"How do I code this?"** → `docs/BANK_CALLER_IMPLEMENTATION.md`

---

**Created by**: Voice User Experience Designer
**Review Date**: January 15, 2025
**Status**: Complete and Ready for Implementation
