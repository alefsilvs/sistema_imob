[OPEN] Debug session: whatsapp-send-500

## Symptom
- UI shows: "Erro ao enviar (HTTP 500)." when sending WhatsApp message from WhatsApp Dashboard (Railway).

## Expected
- Message should be sent successfully (or return a clear JSON error like offline/disconnected) without HTTP 500.

## Hypotheses (falsifiable)
1) Backend endpoint `/notificacoes/whatsapp/api/send-selected/` is not on the latest deploy, so request hits older code or different service and crashes before returning JSON.
2) The request is hitting the wrong endpoint (route/namespace mismatch), causing an unhandled server error and returning an HTML 500 page.
3) Gunicorn/Django crashes before reaching the view (worker error), returning a generic 500 HTML page.
4) The view is reached but an exception occurs outside guarded blocks (e.g., middleware/tenant resolution/session), leading to 500 HTML instead of JSON.
5) Evolution API call or response parsing triggers an unhandled exception, causing server 500 before JSON can be returned.

## Evidence to collect
- From browser: request URL, status, response headers/content-type, response text snippet, timestamp.
- From server (if available): Railway logs around the timestamp.

## Plan
1) Instrument front-end to report request/response details to local Debug Server.
2) Reproduce the send action once.
3) Analyze logs and confirm which hypothesis matches.
4) Apply minimal fix based on evidence.
