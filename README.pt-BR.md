# GHSA-c9cx-7r7m-264v — escalação de privilégio entre tenants no InvoiceShelf

> O proprietário de uma empresa pode inserir uma conta controlada pelo atacante em outro tenant com qualquer papel, inclusive `owner`.

[English](README.md) · [Advisory oficial](https://github.com/InvoiceShelf/InvoiceShelf/security/advisories/GHSA-c9cx-7r7m-264v) · [Correção 2.x](https://github.com/InvoiceShelf/InvoiceShelf/pull/826) · [Correção 3.x](https://github.com/InvoiceShelf/InvoiceShelf/pull/822)

## Resumo

| Item | Valor |
|---|---|
| Produto | InvoiceShelf |
| Versões afetadas | `<= 2.4.3`; `3.0.0-alpha.1` até `3.0.0-alpha.3` |
| Versões corrigidas | `2.4.4`; `3.0.0-alpha.4` |
| Severidade | Crítica |
| Fraquezas | CWE-284, CWE-863 |
| CVSS v3.1 sugerido | `9.1 — AV:N/AC:L/PR:H/UI:N/S:C/C:H/I:H/A:H` |
| Advisory | `GHSA-c9cx-7r7m-264v` |
| CVE | Nenhum CVE conhecido na data da publicação |

## Causa raiz

`MemberRequest` verifica somente o formato do array `companies` controlado pelo cliente. Não verifica se o usuário possui a empresa indicada nem se pode conceder o papel solicitado. Em seguida, `MemberService::create()` e `update()` usam diretamente os IDs em `companies()->sync()` e `grantRoles()` muda o escopo do Bouncer para a empresa escolhida pelo atacante.

A autorização do controller comprova apenas que o solicitante é proprietário da empresa ativa no cabeçalho. Essa decisão não é vinculada ao `companies[].id` presente no corpo da requisição.

```text
proprietário da Empresa A
        │ autorizado a criar membro em A
        ▼
POST /api/v1/members
companies[0].id = Empresa B
companies[0].role = owner
        │ valores aceitos pelo serviço
        ▼
conta do atacante torna-se proprietária da Empresa B
```

## Prova de conceito

A reprodução fornecida é exclusiva para laboratório: recusa alvos que não sejam loopback e não envia nada sem `--execute`. Ela não foi executada durante a preparação desta publicação.

Pré-requisitos:

1. Instalação isolada do InvoiceShelf `2.4.3` ou `3.0.0-alpha.3`.
2. Duas empresas de teste, A e B.
3. Token Sanctum válido de um proprietário da Empresa A.
4. Identificador numérico da Empresa B.

Visualização sem enviar a requisição:

```bash
python3 poc/poc.py \
  --base-url http://127.0.0.1:8080 \
  --token LAB_TOKEN \
  --active-company-id 1 \
  --victim-company-id 2 \
  --email poc-user@example.invalid
```

Depois de revisar a requisição, um pesquisador autorizado pode acrescentar `--execute`. Em uma versão vulnerável, o resultado esperado é HTTP `200`/`201`, com a nova conta associada à Empresa B como `owner`. A versão corrigida deve rejeitar a associação, normalmente com HTTP `403` ou `422`, sem criar o relacionamento.

## Impacto

O proprietário de um tenant legítimo pode obter controle administrativo de outro tenant na mesma instalação. Isso permite acesso ou alteração de faturas, clientes, pagamentos e outros registros financeiros, além das demais capacidades do papel escolhido.

## Correção

Atualize para `2.4.4`, `3.0.0-alpha.4` ou versão posterior. A correção limita os IDs às empresas realmente possuídas pelo solicitante, valida os papéis no escopo correto e preserva associações fora da autoridade do usuário.

## Referências

- [GitHub Security Advisory](https://github.com/InvoiceShelf/InvoiceShelf/security/advisories/GHSA-c9cx-7r7m-264v)
- [Repositório do InvoiceShelf](https://github.com/InvoiceShelf/InvoiceShelf)
- [Correção da linha 2.x, PR #826](https://github.com/InvoiceShelf/InvoiceShelf/pull/826)
- [Correção da linha 3.x, PR #822](https://github.com/InvoiceShelf/InvoiceShelf/pull/822)
- Commit analisado: `0076ab9c5b1840d53690e721a1a4e7a91a068795`
- Divulgação pública: 23/09/2026

## Créditos

Créditos de pesquisa e divulgação solicitados para:

- Alysson Dutra
- Lucas Diniz
- [Fernando Viana](https://github.com/capivara-research)

O GHSA público atualmente identifica `capivara-research` como Reporter e `gdarko` como Coordinator.

## Uso ético e legal

Utilize este material somente em sistemas próprios ou com autorização explícita. A PoC é limitada a alvos locais de laboratório. Não teste instalações públicas ou de terceiros.

