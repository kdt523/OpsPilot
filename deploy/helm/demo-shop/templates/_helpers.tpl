{{- define "shop.podSecurity" -}}
securityContext:
  runAsNonRoot: true
  runAsUser: 10001
  runAsGroup: 10001
  seccompProfile: { type: RuntimeDefault }
{{- end -}}

{{- define "shop.containerSecurity" -}}
securityContext:
  allowPrivilegeEscalation: false
  capabilities: { drop: [ALL] }
{{- end -}}

{{- define "shop.probes" -}}
readinessProbe:
  httpGet: { path: /healthz, port: 8000 }
  periodSeconds: 5
livenessProbe:
  httpGet: { path: /healthz, port: 8000 }
  initialDelaySeconds: 20
  periodSeconds: 10
  failureThreshold: 6
{{- end -}}
