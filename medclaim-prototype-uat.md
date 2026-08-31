# MedClaim clickable prototype UAT

Version: 0.1  
Prototype: [`medclaim-prototype.html`](medclaim-prototype.html)  
Automated preflight: 2026-09-01

## Scope and roles

This tests the portfolio interaction only. It does not validate a model, clinical performance, source freshness, EHR integration, or time savings.

- **Automated preflight:** confirms deterministic interaction and layout behavior.
- **Candidate UAT:** the candidate performs the workflow, judges whether the evidence supports the decision, and records one usability or content issue. Automated PASS does not count as candidate mastery.

## Automated preflight result

| ID | Scenario | Expected result | Result |
|---|---|---|---|
| UAT-01 | Open MC003 from the queue | Evidence review displays the claim, source and reviewer controls | PASS |
| UAT-02 | Submit without choosing a label | Submission is blocked and an accessible error appears | PASS |
| UAT-03 | Choose `Partial support` and submit | Decision record shows the same label | PASS |
| UAT-04 | Keep the default route | Decision record shows `Priority human review` | PASS |
| UAT-05 | Select `Review again` | The label clears and evidence review reopens | PASS |
| UAT-06 | Use 1280×800 and 390×844 | No horizontal overflow | PASS |
| UAT-07 | Complete the flow | No console errors or application data requests | PASS |

The preflight used Playwright against a local Python standard-library web server. Screenshots remained outside the repository.

## Candidate UAT｜60-minute personal gate

Do this without reading the automated result table again.

1. Start the prototype:

   ```bash
   cd '/Users/xynia/Library/Mobile Documents/com~apple~CloudDocs/7️⃣/🇦🇺phD/upskill'
   python3 -m http.server 8765 --bind 127.0.0.1
   ```

2. Open `http://127.0.0.1:8765/medclaim-prototype.html`.
3. Before selecting a label, write your predicted label and the decisive evidence sentence.
4. Complete UAT-01 through UAT-05 in order.
5. Record one issue or improvement that you personally noticed. “No issue” is not accepted.
6. Explain aloud why the final decision is `Partial support`, why the route is priority review, and why this prototype cannot claim clinical validity.
7. Recreate the same three-screen flow in Figma using only rectangles, text, radio choices and three links. Do not add animations or a design system.

## Candidate record

| Field | Candidate entry |
|---|---|
| Date and duration | |
| Predicted label before interaction | |
| Decisive evidence sentence | |
| UAT-01 to UAT-05 result | |
| One issue or improvement | |
| Figma prototype URL or screenshot path | |
| One sentence on what remains unproven | |

Pass only when all five scenarios work, the evidence explanation is correct, one real issue is recorded, and the candidate-created Figma flow can be clicked from queue to decision record.
