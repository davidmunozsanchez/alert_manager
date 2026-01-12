# Prometheus

## Acceso a Prometheus vía Port Forward

Para acceder al dashboard de Prometheus desde tu máquina local:

1. Ejecuta en terminal:
   ```sh
   kubectl port-forward -n alert-manager svc/prometheus 9090:9090
   ```
2. Abre tu navegador y entra en:
   [http://localhost:9090](http://localhost:9090)

---

## Queries útiles para node-exporter

- **Ver si node-exporter está up:**
  ```
  up{job="node-exporter"}
  ```

- **CPU total usada por nodo:**
  ```
  sum(rate(node_cpu_seconds_total{mode!="idle"}[5m])) by (instance)
  ```

- **Memoria libre por nodo:**
  ```
  node_memory_MemAvailable_bytes
  ```

- **Memoria total por nodo:**
  ```
  node_memory_MemTotal_bytes
  ```

- **Porcentaje de memoria usada:**
  ```
  100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))
  ```

- **Espacio libre en disco raíz:**
  ```
  node_filesystem_avail_bytes{mountpoint="/"}
  ```

- **Espacio total en disco raíz:**
  ```
  node_filesystem_size_bytes{mountpoint="/"}
  ```

- **Porcentaje de uso de disco raíz:**
  ```
  100 * (1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}))
  ```