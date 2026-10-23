## Tabela 1 - Métricas por perfil e cenário (média ± desvio padrão das repetições)

| Perfil | Cenário | Usuários | Reps | Tempo médio (ms) | P95 (ms) | Vazão (req/s) | Vazão sem falhas (req/s) | Total de req. | Falhas (%) |
|---|---|---|---|---|---|---|---|---|---|
| leitura | A - Leve | 30 | 10 | 12.0 ± 0.7 | 37.2 ± 8.2 | 19.8 ± 0.1 | 19.7 ± 0.2 | 7083 | 0.3 ± 1.1 |
| leitura | B - Moderado | 80 | 10 | 26.4 ± 6.6 | 56.9 ± 15.2 | 52.2 ± 0.3 | 52.2 ± 0.3 | 18734 | 0.0 ± 0.0 |
| leitura | C - Elevado | 150 | 10 | 309.4 ± 45.8 | 1460.0 ± 217.1 | 82.6 ± 2.1 | 82.6 ± 2.1 | 29650 | 0.0 ± 0.0 |
| escrita | A - Leve | 30 | 10 | 39.7 ± 5.9 | 119.8 ± 11.0 | 19.4 ± 0.1 | 19.3 ± 0.2 | 6954 | 0.4 ± 1.2 |
| escrita | B - Moderado | 80 | 10 | 533.1 ± 137.1 | 3872.0 ± 1866.0 | 39.3 ± 2.7 | 29.1 ± 2.4 | 14105 | 26.0 ± 4.6 |
| escrita | C - Elevado | 150 | 10 | 467.0 ± 32.4 | 2850.0 ± 724.6 | 76.0 ± 1.2 | 14.1 ± 0.6 | 27294 | 81.5 ± 0.8 |

## Tabela 2 - Métricas por operação (média das repetições)

| Perfil | Cenário | Operação | Tempo médio (ms) | P95 (ms) | Falhas (%) | Req. (média) |
|---|---|---|---|---|---|---|
| leitura | A | GET /owners | 15.6 | 23.8 | 0.3 | 3181.3 |
| leitura | A | GET /owners/{id} | 5.1 | 7.3 | 0.3 | 2487.4 |
| leitura | A | GET /vets | 5.3 | 7.9 | 0.4 | 1074.0 |
| leitura | A | POST /owners | 48.7 | 53.0 | 0.3 | 340.2 |
| leitura | B | GET /owners | 43.3 | 72.9 | 0.0 | 8455.8 |
| leitura | B | GET /owners/{id} | 10.3 | 9.9 | 0.0 | 6542.8 |
| leitura | B | GET /vets | 5.0 | 8.5 | 0.0 | 2797.0 |
| leitura | B | POST /owners | 50.8 | 55.3 | 0.0 | 938.6 |
| leitura | C | GET /owners | 434.9 | 1680.0 | 0.0 | 13293.1 |
| leitura | C | GET /owners/{id} | 278.3 | 1290.0 | 0.0 | 10365.8 |
| leitura | C | GET /vets | 7.1 | 10.9 | 0.0 | 4486.2 |
| leitura | C | POST /owners | 317.4 | 1330.0 | 0.0 | 1504.6 |
| escrita | A | GET /owners | 95.1 | 161.0 | 0.3 | 1407.2 |
| escrita | A | GET /owners/{id} | 8.8 | 9.1 | 0.4 | 1414.2 |
| escrita | A | GET /vets | 5.3 | 8.0 | 0.4 | 1387.5 |
| escrita | A | POST /owners | 44.5 | 52.8 | 0.3 | 2745.3 |
| escrita | B | GET /owners | 973.7 | 8230.0 | 28.3 | 2827.1 |
| escrita | B | GET /owners/{id} | 550.1 | 4248.5 | 26.1 | 2819.9 |
| escrita | B | GET /vets | 5.6 | 10.1 | 24.2 | 2832.1 |
| escrita | B | POST /owners | 568.0 | 4442.0 | 25.6 | 5625.5 |
| escrita | C | GET /owners | 697.7 | 5820.0 | 82.9 | 5468.3 |
| escrita | C | GET /owners/{id} | 507.2 | 3520.0 | 81.9 | 5477.1 |
| escrita | C | GET /vets | 4.0 | 7.9 | 79.1 | 5454.0 |
| escrita | C | POST /owners | 562.8 | 3880.0 | 81.8 | 10895.1 |

## Tabela 3 - CPU e memória por serviço (média das repetições)

| Perfil | Cenário | Serviço | CPU média (%) | CPU máx. média (%) | Memória média (MiB) |
|---|---|---|---|---|---|
| escrita | A | api-gateway | 9.1 | 49.6 | 349.2 |
| escrita | A | customers-service | 43.0 | 140.4 | 405.2 |
| escrita | A | vets-service | 1.0 | 19.5 | 343.5 |
| escrita | B | api-gateway | 14.8 | 71.2 | 356.5 |
| escrita | B | customers-service | 123.8 | 243.1 | 426.1 |
| escrita | B | vets-service | 1.3 | 24.7 | 344.2 |
| escrita | C | api-gateway | 14.6 | 110.7 | 369.4 |
| escrita | C | customers-service | 79.9 | 241.1 | 449.5 |
| escrita | C | vets-service | 0.7 | 13.2 | 344.8 |
| leitura | A | api-gateway | 7.9 | 64.2 | 338.1 |
| leitura | A | customers-service | 16.3 | 58.7 | 379.2 |
| leitura | A | vets-service | 1.0 | 31.7 | 343.5 |
| leitura | B | api-gateway | 14.7 | 62.2 | 349.8 |
| leitura | B | customers-service | 80.4 | 186.3 | 404.3 |
| leitura | B | vets-service | 1.7 | 24.4 | 343.9 |
| leitura | C | api-gateway | 25.6 | 115.5 | 357.8 |
| leitura | C | customers-service | 184.9 | 273.6 | 427.1 |
| leitura | C | vets-service | 2.3 | 45.4 | 344.5 |
