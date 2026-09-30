ALERT
- name: {alertname}  severity: {severity}  started: {starts_at} ({age} ago)
- namespace: {namespace}  deployment: {deployment}  pod: {pod}  service: {service}
- summary: {summary}
- labels: {labels}

RECENT ROLLOUTS of {deployment} (newest first)
{rollouts}

NOW: {now}
Investigate and call submit_diagnosis.
