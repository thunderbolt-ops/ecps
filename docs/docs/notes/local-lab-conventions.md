# ECPS Local Lab Conventions (kind on Ubuntu)

## Fixed port-forwards (avoid collisions)
- Ingress NGINX:
  kubectl -n platform-system port-forward svc/ingress-nginx-controller 8080:80
- Argo CD:
  kubectl -n platform-system port-forward svc/argocd-server 8081:80
- Grafana:
  kubectl -n platform-observability port-forward svc/kube-prometheus-stack-grafana 3000:80

Rule: never reuse the same local port for different port-forwards.

## /etc/hosts entries (keep both)
127.0.0.1 hello.team-alpha.local
127.0.0.1 hello.team-beta.local

## kind NodePort gotcha
NodePorts are not reliably reachable on localhost in kind unless you set explicit port mappings.
Default approach: use port-forward for ingress.

## NetworkPolicy reality check
NetworkPolicy enforcement depends on the CNI.
If policies appear “ignored”, do not assume your YAML/TF is wrong—verify the CNI supports enforcement.
